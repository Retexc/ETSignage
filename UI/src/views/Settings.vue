<script setup>
import { motion } from "motion-v";
import ConfirmButton from "../components/ConfirmButton.vue";
import { ref, watch, onMounted, onBeforeUnmount } from "vue";
import { Linkedin } from "lucide-vue-next";
import { Github } from "lucide-vue-next";
import { useUpdateStore } from "../composables/useUpdateStore.js";
import { uploadFile, getLastGTFSUpdate } from "../lib/supabaseStorage.js";
import JSZip from "jszip";

const tabs = [
  { id: "gtfs", label: "GTFS" },
  { id: "about", label: "À propos" },
];
const active = ref("gtfs");

const stmLastUpdate = ref("N/A");
const exoLastUpdate = ref("N/A");

// Use the update store composable
const { updateState, checkForUpdates, performUpdate, clearNotification } = useUpdateStore();

const icons = {
  idle: new URL("../assets/icons/status_good.png", import.meta.url).href,
  checking: new URL("../assets/icons/status_updating.png", import.meta.url).href,
  up_to_date: new URL("../assets/icons/status_good.png", import.meta.url).href,
  available: new URL("../assets/icons/status_important.png", import.meta.url).href,
  updating: new URL("../assets/icons/status_updating.png", import.meta.url).href,
  error: new URL("../assets/icons/status_warning.png", import.meta.url).href,
};

// --- Settings + scheduler state ---
const settings = ref({
  autoUpdateTime: "02:00",
});
let updateTimeout = null;

// États pour les uploads GTFS
const isUploadingSTM = ref(false);
const isUploadingEXO = ref(false);
const stmFileInputRef = ref(null);
const exoFileInputRef = ref(null);

function scheduleNextUpdate() {
  if (updateTimeout !== null) {
    console.log("[Scheduler] Clearing previous timeout:", updateTimeout);
    clearTimeout(updateTimeout);
    updateTimeout = null;
  }

  const time = settings.value.autoUpdateTime;
  console.log("[Scheduler] User-selected time is:", time);
  if (!time) {
    console.warn("[Scheduler] No time chosen, skipping scheduling");
    return;
  }

  const [hour, minute] = time.split(":").map((s) => parseInt(s, 10));
  const now = new Date();
  let next = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
    hour,
    minute,
    0,
    0
  );

  if (next.getTime() <= now.getTime()) {
    next.setDate(next.getDate() + 1);
  }

  const msUntilNext = next.getTime() - now.getTime();
  console.log(
    `[Scheduler] Scheduling next update at ${next.toLocaleString()} ` +
      `(in ${Math.round(msUntilNext / 1000)}s)`
  );
  updateTimeout = setTimeout(async () => {
    console.log("[Scheduler] ⏰ Timeout fired! Running update check now.");
    await checkForUpdates();
    if (updateState.available) {
      await performUpdate();
    }
    scheduleNextUpdate(); // schedule tomorrow
  }, msUntilNext);
}

// Configuration des stops et routes utilisés
const USED_STOPS = ['52743', '52744', '62248', '62355'];
const USED_ROUTES = ['36', '61'];

// Fonction pour uploader GTFS vers Supabase
// NOUVELLE VERSION: Extrait et filtre les fichiers nécessaires
async function uploadGTFS(transport, file) {
  if (!file) return;
  
  // Vérifier que c'est bien un fichier ZIP
  if (!file.name.endsWith('.zip')) {
    alert('Le fichier doit être un fichier ZIP (.zip)');
    return;
  }
  
  const isSTM = transport === 'stm';
  const uploadingRef = isSTM ? isUploadingSTM : isUploadingEXO;
  
  uploadingRef.value = true;
  
  try {
    console.log(`📤 Extraction du fichier GTFS ${transport.toUpperCase()}...`);
    
    // 1. Lire le fichier ZIP
    const zip = await JSZip.loadAsync(file);
    
    // 2. Vérifier que les fichiers nécessaires existent
    const requiredFiles = ['routes.txt', 'trips.txt', 'stop_times.txt'];
    const missingFiles = [];
    
    for (const fileName of requiredFiles) {
      if (!zip.file(fileName)) {
        missingFiles.push(fileName);
      }
    }
    
    if (missingFiles.length > 0) {
      alert(`❌ Fichiers manquants dans le ZIP: ${missingFiles.join(', ')}`);
      uploadingRef.value = false;
      return;
    }
    
    console.log('✅ Tous les fichiers nécessaires sont présents');
    
    // 3. Traiter et uploader chaque fichier
    let uploadCount = 0;
    
    // === ROUTES.TXT - Filtrer seulement les routes 36 et 61 ===
    console.log('📤 Traitement de routes.txt...');
    const routesContent = await zip.file('routes.txt').async("string");
    const routesLines = routesContent.split('\n');
    const routesHeader = routesLines[0];
    const filteredRoutes = routesLines.filter((line, index) => {
      if (index === 0) return true; // Garder le header
      return USED_ROUTES.some(route => line.includes(`"${route}"`));
    });
    const filteredRoutesContent = filteredRoutes.join('\n');
    console.log(`   Routes: ${routesLines.length} lignes → ${filteredRoutes.length} lignes`);
    
    const routesBlob = new Blob([filteredRoutesContent], { type: 'text/plain' });
    const routesFile = new File([routesBlob], 'routes.txt', { type: 'text/plain' });
    let result = await uploadFile(routesFile, 'gtfs-files', transport);
    if (!result.success) {
      alert(`❌ Erreur upload routes.txt: ${result.error}`);
      uploadingRef.value = false;
      return;
    }
    uploadCount++;
    console.log(`✅ routes.txt uploadé (${uploadCount}/3)`);
    
    // === TRIPS.TXT - Filtrer par route_id ===
    console.log('📤 Traitement de trips.txt...');
    const tripsContent = await zip.file('trips.txt').async("string");
    const tripsLines = tripsContent.split('\n');
    
    // Parser le header pour trouver l'index de route_id
    const tripsHeaderLine = tripsLines[0];
    const tripsHeaders = tripsHeaderLine.split(',');
    const routeIdIndex = tripsHeaders.findIndex(h => h.trim() === 'route_id');
    
    const filteredTrips = tripsLines.filter((line, index) => {
      if (index === 0) return true; // Garder le header
      if (!line.trim()) return false; // Ignorer les lignes vides
      
      const columns = line.split(',');
      const routeId = columns[routeIdIndex]?.replace(/"/g, '').trim();
      
      // Garder seulement les trips des routes 36 et 61
      return USED_ROUTES.includes(routeId);
    });
    
    const filteredTripsContent = filteredTrips.join('\n');
    console.log(`   Trips: ${tripsLines.length} lignes → ${filteredTrips.length} lignes`);
    
    const tripsBlob = new Blob([filteredTripsContent], { type: 'text/plain' });
    const tripsFile = new File([tripsBlob], 'trips.txt', { type: 'text/plain' });
    result = await uploadFile(tripsFile, 'gtfs-files', transport);
    if (!result.success) {
      alert(`❌ Erreur upload trips.txt: ${result.error}`);
      uploadingRef.value = false;
      return;
    }
    uploadCount++;
    console.log(`✅ trips.txt uploadé (${uploadCount}/3)`);
    
    // === STOP_TIMES.TXT - Filtrer par stop_id ===
    console.log('📤 Traitement de stop_times.txt (ceci peut prendre un moment)...');
    const stopTimesContent = await zip.file('stop_times.txt').async("string");
    const stopTimesLines = stopTimesContent.split('\n');
    
    // Parser le header
    const stopTimesHeaderLine = stopTimesLines[0];
    const stopTimesHeaders = stopTimesHeaderLine.split(',');
    const stopIdIndex = stopTimesHeaders.findIndex(h => h.trim() === 'stop_id');
    const tripIdIndex = stopTimesHeaders.findIndex(h => h.trim() === 'trip_id');
    
    // Créer un Set des trip_ids valides depuis trips filtrés
    const validTripIds = new Set();
    filteredTrips.forEach((line, index) => {
      if (index === 0) return; // Skip header
      const columns = line.split(',');
      const tripId = columns[0]?.replace(/"/g, '').trim();
      if (tripId) validTripIds.add(tripId);
    });
    
    console.log(`   Filtrage avec ${validTripIds.size} trips valides et ${USED_STOPS.length} stops...`);
    
    const filteredStopTimes = stopTimesLines.filter((line, index) => {
      if (index === 0) return true; // Garder le header
      if (!line.trim()) return false; // Ignorer les lignes vides
      
      const columns = line.split(',');
      const tripId = columns[tripIdIndex]?.replace(/"/g, '').trim();
      const stopId = columns[stopIdIndex]?.replace(/"/g, '').trim();
      
      // Garder seulement les lignes avec nos stops ET nos trips
      return USED_STOPS.includes(stopId) && validTripIds.has(tripId);
    });
    
    const filteredStopTimesContent = filteredStopTimes.join('\n');
    console.log(`   Stop times: ${stopTimesLines.length} lignes → ${filteredStopTimes.length} lignes`);
    console.log(`   Taille réduite: ${(stopTimesContent.length / 1024 / 1024).toFixed(2)} MB → ${(filteredStopTimesContent.length / 1024 / 1024).toFixed(2)} MB`);
    
    const stopTimesBlob = new Blob([filteredStopTimesContent], { type: 'text/plain' });
    const stopTimesFile = new File([stopTimesBlob], 'stop_times.txt', { type: 'text/plain' });
    result = await uploadFile(stopTimesFile, 'gtfs-files', transport);
    if (!result.success) {
      alert(`❌ Erreur upload stop_times.txt: ${result.error}`);
      uploadingRef.value = false;
      return;
    }
    uploadCount++;
    console.log(`✅ stop_times.txt uploadé (${uploadCount}/3)`);
    
    console.log(`✅ Tous les fichiers GTFS ${transport.toUpperCase()} uploadés avec succès!`);
    alert(`✅ ${uploadCount} fichiers GTFS ${transport.toUpperCase()} filtrés et uploadés!\n\nRoutes: ${filteredRoutes.length} lignes\nTrips: ${filteredTrips.length} lignes\nStop times: ${filteredStopTimes.length} lignes`);
    
    // Rafraîchir les dates de dernière mise à jour
    await fetchLastUpdates();
    
  } catch (error) {
    console.error('❌ Erreur lors du traitement GTFS:', error);
    alert(`Une erreur s'est produite: ${error.message}`);
  } finally {
    uploadingRef.value = false;
  }
}

// Fonctions pour déclencher le sélecteur de fichier
function openSTMFileSelector() {
  stmFileInputRef.value?.click();
}

function openEXOFileSelector() {
  exoFileInputRef.value?.click();
}

// Gestionnaires de changement de fichier
function onStmFileChange(e) {
  const file = e.target.files[0];
  if (file) {
    uploadGTFS("stm", file);
  }
  // Réinitialiser l'input pour permettre de re-uploader le même fichier
  e.target.value = '';
}

function onExoFileChange(e) {
  const file = e.target.files[0];
  if (file) {
    uploadGTFS("exo", file);
  }
  // Réinitialiser l'input pour permettre de re-uploader le même fichier
  e.target.value = '';
}

// Récupérer les dates de dernière mise à jour depuis Supabase
async function fetchLastUpdates() {
  try {
    const stmDate = await getLastGTFSUpdate('stm');
    const exoDate = await getLastGTFSUpdate('exo');
    
    stmLastUpdate.value = stmDate;
    exoLastUpdate.value = exoDate;
    
    console.log('✅ Dates de mise à jour récupérées:', { stm: stmDate, exo: exoDate });
  } catch (e) {
    console.warn('⚠️ Erreur lors de la récupération des infos GTFS:', e);
  }
}

// Clear notification when switching to update tab
watch(active, (newTab) => {
  if (newTab === 'update') {
    clearNotification();
  }
});

onMounted(() => {
  fetchLastUpdates();
  scheduleNextUpdate();
});

watch(
  () => settings.value.autoUpdateTime,
  (newTime, oldTime) => {
    console.log(
      `[Watcher] autoUpdateTime changed from ${oldTime} to ${newTime}`
    );
    scheduleNextUpdate();
  }
);

onBeforeUnmount(() => {
  if (updateTimeout !== null) {
    clearTimeout(updateTimeout);
  }
});

// Helper function to get current update state for display
function getCurrentUpdateState() {
  if (updateState.checking) return 'checking';
  if (updateState.available) return 'available';
  if (updateState.message && !updateState.available) {
    if (updateState.message.includes('error') || updateState.message.includes('Erreur')) {
      return 'error';
    }
    return 'up_to_date';
  }
  return 'up_to_date';
}
</script>

<template>
  <motion.div
    class="flex max-h-screen bg-[#f0f0f0]"
    :initial="{ opacity: 0, y: 20, filter: 'blur(10px)' }"
    :animate="{
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      transition: { duration: 0.5 },
    }"
  >
    <div class="flex-1 flex flex-col p-6 space-y-6 mt-18 ml-5 mr-5">
      <div class="space-y-1 w-full">
        <h2 class="text-4xl font-bold text-black">Paramètres</h2>
        <p class="text-xl text-black">
          Modifier les paramètres de l'application
        </p>

        <!-- ──────── Tabs ──────── -->
        <div
          class="mt-2 text-sm font-medium text-center text-gray-500 border-b border-gray-200"
        >
          <ul class="flex flex-wrap -mb-px">
            <li v-for="tab in tabs" :key="tab.id" class="mr-2">
              <a
                href="#"
                @click.prevent="active = tab.id"
                :class="[
                  'inline-block p-4 border-b-2 rounded-t-lg',
                  active === tab.id
                    ? 'text-black font-bold border-red-500'
                    : 'border-transparent hover:text-gray-600 hover:border-gray-300',
                ]"
              >
                {{ tab.label }}
              </a>
            </li>
          </ul>
        </div>
      </div>

      <!-- ──────── Tab Panels ──────── -->
        <motion.div
          class="mt-4"
          :key="'tab_panel'"
          :initial="{ opacity: 0, y: 20, filter: 'blur(10px)' }"
          :animate="{
            opacity: 1,
            y: 0,
            filter: 'blur(0px)',
            transition: { duration: 0.5 },
          }"
        >
        <motion.div 
        v-if="active === 'gtfs'"
        :key="'gtfs_tab'"
        :initial="{ opacity: 0, y: 20 }"
        :animate="{ opacity: 1, y: 0, transition: { duration: 0.3 } }"        
        >
          <div class="bg-gray-300 rounded-lg p-6 mb-6 text-black space-y-4">
            <h3 class="text-xl font-semibold">
              Les fichiers GTFS contiennent les horaires et les informations des
              autobus de la STM. Il est nécessaire de les mettre à jour
              régulièrement.
            </h3>
            <p>
              Vous pouvez utiliser les dates disponibles sur le site de la STM
              comme référence pour mettre à jour les fichiers.
            </p>
            <p>
              Pour télécharger les dernières versions des données GTFS,
              consultez :
            </p>
            <ul class="list-disc list-inside space-y-1">
              <li>
                <a
                  href="https://www.stm.info/fr/a-propos/developpeurs"
                  target="_blank"
                  class="text-black underline hover:text-blue-400"
                >
                  STM : Développeurs | Société de transport de Montréal
                </a>
              </li>
            </ul>
            <div class="bg-blue-100 border-l-4 border-blue-500 p-4 mt-4">
              <p class="text-sm text-blue-700">
                ℹ️ <strong>Note:</strong> Seuls les fichiers <code class="bg-blue-200 px-1 rounded">routes.txt</code>, 
                <code class="bg-blue-200 px-1 rounded">trips.txt</code> et 
                <code class="bg-blue-200 px-1 rounded">stop_times.txt</code> sont extraits du ZIP et uploadés.
              </p>
            </div>
          </div>
          
          <!-- Section STM -->
          <div class="flex flex-col space-y-6">
            <img
              src="../assets/images/stm_logo.svg"
              alt="STM logo"
              class="gtfs-logo mb-3 h-10 self-start"
            />
            <hr class="border-t border-[#404040] mt-3" />
            
            <div class="flex flex-col space-y-4">
              <!-- Bouton d'import STM -->
              <div class="flex items-center justify-between bg-white rounded-lg p-4 shadow">
                <div class="flex-1">
                  <h4 class="font-semibold text-lg">Fichier GTFS (ZIP)</h4>
                  <p class="text-sm text-gray-600">
                    Dernière mise à jour : {{ stmLastUpdate }}
                  </p>
                </div>
                <button
                  @click="openSTMFileSelector"
                  :disabled="isUploadingSTM"
                  class="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg flex items-center transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <svg v-if="!isUploadingSTM" class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
                  </svg>
                  <svg v-else class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {{ isUploadingSTM ? 'Extraction & Upload...' : 'Importer' }}
                </button>
              </div>
              
              <!-- Input file caché pour STM -->
              <input
                ref="stmFileInputRef"
                type="file"
                accept=".zip"
                @change="onStmFileChange"
                class="hidden"
              />
            </div>
          </div>
        </motion.div>
        
        
        <motion.div
        v-else-if="active === 'about'"
        :key="'about_tab'"
        :initial="{ opacity: 0, y: 20 }"
        :animate="{ opacity: 1, y: 0, transition: { duration: 0.3 } }"          
        >
          <div
            class="bg-gray-300 rounded-2xl p-10 flex flex-row items-center justify-between space-x-8"
          >
            <!-- left column: text info -->
            <div class="space-y-2">
              <h2 class="text-2xl font-bold text-black">Higher Pierre</h2>
              <p class="text-xl text-black">Designer UX/UI</p>
              <p class="text-xl text-black">Créateur de contenu multimédia</p>
              <p class="text-xl text-black flex items-center">
                Fait avec
                <span class="ml-2 text-red-500">❤️</span>
              </p>
            </div>

            <!-- right column: avatar + buttons -->
            <div class="flex flex-col items-center space-y-4">
              <!-- circular profile picture -->
              <img
                src="../assets/images/hp.jpg"
                alt="Mon profil"
                class="w-32 h-32 rounded-full object-cover shadow-lg"
              />

              <!-- social buttons -->
              <div class="flex space-x-2">
                <a
                  href="https://www.linkedin.com/in/higherpierre/"
                  target="_blank"
                  rel="noopener"
                  class="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition"
                >
                  <Linkedin class="w-5 h-5" />
                  <span class="ml-2 font-medium">LinkedIn</span>
                </a>

                <a
                  href="https://github.com/Retexc"
                  target="_blank"
                  rel="noopener"
                  class="flex items-center px-4 py-2 bg-white hover:bg-gray-400 text-black rounded-lg transition"
                >
                  <Github class="w-5 h-5" />
                  <span class="ml-2 font-medium">GitHub</span>
                </a>
              </div>
            </div>
          </div>
        </motion.div>
        </motion.div>
    </div>
</motion.div>
</template>

<style scoped>
.home-page {
  padding: 2rem;
  text-align: center;
}
</style>