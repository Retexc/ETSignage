<script>
import { ref, computed, onMounted, watch } from "vue";
import { useAnnonceStore } from '../stores/annonceStore.js'

export default {
  name: "AnnonceEditorWithMedia",
  setup() {
    // Utiliser le store Pinia
    const annonceStore = useAnnonceStore()
    
    const pageActive = ref(1);
    const fileInput = ref(null);

    // Charger les annonces depuis le store au démarrage
    onMounted(() => {
      // Charger depuis localStorage si disponible
      annonceStore.chargerLocal()
      
      // Si le store a des annonces, les utiliser
      if (annonceStore.annonces.length > 0) {
        annonces.value = [...annonceStore.annonces]
      }
    })

    // Liste des annonces (locale à l'éditeur)
    const annonces = ref([
      {
        id: 1,
        nom: "Page 1",
        media: null,
        mediaType: null,
        mediaName: null,
        mediaSize: null,
        dureeDebut: "",
        dureeFin: "",
        dureeAffichage: 5,
        transition: "fade",
        modeAffichage: "cover",
        loop: false,
      },
    ]);

    // Synchroniser avec le store quand les annonces changent
    watch(annonces, (newAnnonces) => {
      annonceStore.setAnnonces(newAnnonces)
      annonceStore.sauvegarderLocal() // Sauvegarder automatiquement
    }, { deep: true })

    // Obtenir la page sélectionnée
    const pageSelectionnee = computed(() => {
      return annonces.value.find((a) => a.id === pageActive.value);
    });

    // Ajouter une nouvelle page
    const ajouterPage = () => {
      const nouvelId = Math.max(...annonces.value.map((a) => a.id), 0) + 1;
      const nouvellePage = {
        id: nouvelId,
        nom: `Page ${nouvelId}`,
        media: null,
        mediaType: null,
        mediaName: null,
        mediaSize: null,
        dureeDebut: "",
        dureeFin: "",
        dureeAffichage: 5,
        transition: "fade",
        modeAffichage: "cover",
        loop: false,
      }
      annonces.value.push(nouvellePage);
      pageActive.value = nouvelId;
    };

    // Supprimer une page
    const supprimerPage = (index) => {
      if (annonces.value.length > 1) {
        const pageASupprimer = annonces.value[index];
        annonces.value.splice(index, 1);

        if (pageASupprimer.id === pageActive.value) {
          pageActive.value = annonces.value[0]?.id;
        }
      } else {
        alert("Vous devez garder au moins une page!");
      }
    };

    // Monter une page
    const monter = (index) => {
      if (index > 0) {
        const temp = annonces.value[index];
        annonces.value[index] = annonces.value[index - 1];
        annonces.value[index - 1] = temp;
      }
    };

    // Descendre une page
    const descendre = (index) => {
      if (index < annonces.value.length - 1) {
        const temp = annonces.value[index];
        annonces.value[index] = annonces.value[index + 1];
        annonces.value[index + 1] = temp;
      }
    };

    // Ouvrir le sélecteur de fichier
    const ouvrirSelecteurFichier = () => {
      fileInput.value?.click();
    };

    // Gérer l'upload d'un fichier
const gererUploadFichier = (event) => {
  const file = event.target.files[0];
  if (!file) return;

  if (!pageSelectionnee.value) return;

  // Déterminer le type de média
  let mediaType = null;
  if (file.type.startsWith("image/")) {
    mediaType = "image";
  } else if (file.type.startsWith("video/")) {
    mediaType = "video";
  } else if (file.type === "application/pdf") {
    mediaType = "pdf";
  }

  // ✅ Utiliser un URL Blob au lieu de FileReader
  const fileURL = URL.createObjectURL(file);

  // Mettre à jour la page
  pageSelectionnee.value.media = fileURL;
  pageSelectionnee.value.mediaType = mediaType;
  pageSelectionnee.value.mediaName = file.name;
  pageSelectionnee.value.mediaSize = file.size;

  // Si c’est une vidéo → calculer la durée
  if (mediaType === "video") {
    const video = document.createElement("video");
    video.src = fileURL;
    video.onloadedmetadata = () => {
      if (pageSelectionnee.value) {
        pageSelectionnee.value.dureeAffichage = Math.round(video.duration);
      }
    };
  }

  // Reset input pour pouvoir recharger le même fichier ensuite
  event.target.value = "";
};


    // Supprimer le média
    const supprimerMedia = () => {
      if (pageSelectionnee.value) {
        pageSelectionnee.value.media = null;
        pageSelectionnee.value.mediaType = null;
        pageSelectionnee.value.mediaName = null;
        pageSelectionnee.value.mediaSize = null;
        pageSelectionnee.value.dureeAffichage = 5;
      }
    };

    // Formater la taille du fichier
    const formatFileSize = (bytes) => {
      if (bytes === 0) return "0 Bytes";
      const k = 1024;
      const sizes = ["Bytes", "KB", "MB", "GB"];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
    };

    return {
      annonces,
      pageActive,
      pageSelectionnee,
      fileInput,
      ajouterPage,
      supprimerPage,
      monter,
      descendre,
      ouvrirSelecteurFichier,
      gererUploadFichier,
      supprimerMedia,
      formatFileSize,
    };
  },
};
</script>
<template>
  <div
    class="flex flex-row justify-between items-center bg-white p-2 py-4 drop-shadow-xl"
  >
    <div class="flex flex-row items-center mr-6 p-2">
      <router-link
        to="/"
        class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-2 rounded-lg inline-flex items-center"
      >
        <svg
          class="w-6 h-6 text-gray-800 dark:text-gray-700"
          aria-hidden="true"
          xmlns="http://www.w3.org/2000/svg"
          width="24"
          height="24"
          fill="none"
          viewBox="0 0 24 24"
        >
          <path
            stroke="currentColor"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="m4 12 8-8 8 8M6 10.5V19a1 1 0 0 0 1 1h3v-3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v3h3a1 1 0 0 0 1-1v-8.5"
          />
        </svg>
      </router-link>

      <div class="flex flex-row items-center gap-4">
        <img src="../assets/icons/ETS.svg" alt="Bdeblogo" class="w-12 ml-6" />
        <h1 class="text-black font-bold text-2xl">Editeur d'annonces</h1>
      </div>
    </div>
  </div>
  <div class="flex h-screen bg-gray-100">
    <!-- Menu de gauche -->
    <div class="w-100 bg-white shadow-lg p-4 overflow-y-auto">
      <!-- Bouton Ajouter -->
      <button
        @click="ajouterPage"
        class="w-full mb-4 py-3 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg flex items-center justify-center transition-colors"
      >
        <svg
          class="w-5 h-5 mr-2"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 4v16m8-8H4"
          ></path>
        </svg>
        Ajouter une page
      </button>

      <!-- Liste des annonces -->
      <div class="space-y-2">
        <div
          v-for="(annonce, index) in annonces"
          :key="annonce.id"
          class="flex items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
          :class="{
            'bg-gray-800 text-white hover:bg-gray-700':
              annonce.id === pageActive,
          }"
          @click="pageActive = annonce.id"
        >
          <!-- Boutons pour réorganiser -->
          <div class="flex flex-col mr-2">
            <button
              @click.stop="monter(index)"
              :disabled="index === 0"
              class="p-1 hover:bg-gray-200 rounded disabled:opacity-30 disabled:cursor-not-allowed"
              :class="annonce.id === pageActive ? 'hover:bg-gray-600' : ''"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
                />
              </svg>
            </button>
            <button
              @click.stop="descendre(index)"
              :disabled="index === annonces.length - 1"
              class="p-1 hover:bg-gray-200 rounded disabled:opacity-30 disabled:cursor-not-allowed"
              :class="annonce.id === pageActive ? 'hover:bg-gray-600' : ''"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path
                  d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                />
              </svg>
            </button>
          </div>

          <!-- Numéro -->
          <span class="font-bold mr-3 text-lg">{{ index + 1 }}</span>

          <!-- Miniature avec indicateur de type -->
          <div
            class="w-16 h-12 mr-3 rounded overflow-hidden bg-gray-200 flex items-center justify-center relative"
          >
            <img
              v-if="annonce.media && annonce.mediaType === 'image'"
              :src="annonce.media"
              class="w-full h-full object-cover"
            />
            <!-- Icône PDF -->
            <svg
              v-else-if="annonce.mediaType === 'pdf'"
              class="w-8 h-8 text-red-500"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M10,19L12,15H13L15,19H13.5L13.1,18H11.9L11.5,19H10M11.3,16.8L12,15.6L12.7,16.8H11.3Z"
              />
            </svg>
            <!-- Icône Vidéo -->
            <svg
              v-else-if="annonce.mediaType === 'video'"
              class="w-8 h-8 text-blue-500"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                d="M17,10.5V7A1,1 0 0,0 16,6H4A1,1 0 0,0 3,7V17A1,1 0 0,0 4,18H16A1,1 0 0,0 17,17V13.5L21,17.5V6.5L17,10.5Z"
              />
            </svg>
            <!-- Icône par défaut -->
            <svg
              v-else
              class="w-8 h-8 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              ></path>
            </svg>
            <!-- Badge de type de média -->
            <span
              v-if="annonce.mediaType"
              class="absolute -top-1 -right-1 text-xs bg-blue-500 text-white px-1 rounded"
            >
              {{ annonce.mediaType.toUpperCase() }}
            </span>
          </div>

          <!-- Nom de la page -->
          <input
            v-model="annonce.nom"
            class="flex-1 bg-transparent outline-none px-2 py-1 rounded"
            :class="annonce.id === pageActive ? 'text-white' : 'text-gray-700'"
            placeholder="Nom de la page"
            @click.stop
          />

          <!-- Bouton supprimer -->
          <button
            @click.stop="supprimerPage(index)"
            class="ml-2 p-1 hover:bg-red-500 hover:text-white rounded transition-colors"
          >
            <svg
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              ></path>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Zone principale d'aperçu -->
    <div class="flex-1 p-8">
      <div class="bg-white rounded-lg shadow-lg h-full flex flex-col">
        <!-- Header de la zone d'aperçu -->
        <div class="p-4 border-b bg-gray-50">
          <h3 class="text-lg font-semibold">
            Aperçu - {{ pageSelectionnee?.nom || "Aucune page sélectionnée" }}
          </h3>
        </div>

        <!-- Zone de contenu -->
        <div class="flex-1 p-8 flex items-center justify-center">
          <!-- Si un média est présent -->
          <div
            v-if="pageSelectionnee?.media"
            class="w-full h-full flex items-center justify-center"
          >
            <!-- Aperçu Image -->
            <img
              v-if="pageSelectionnee.mediaType === 'image'"
              :src="pageSelectionnee.media"
              class="max-w-full max-h-full object-contain rounded-lg shadow-lg"
              alt="Aperçu"
            />

            <!-- Aperçu PDF -->
            <div
              v-else-if="pageSelectionnee.mediaType === 'pdf'"
              class="text-center"
            >
              <svg
                class="w-32 h-32 text-red-500 mx-auto mb-4"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20M10,19L12,15H13L15,19H13.5L13.1,18H11.9L11.5,19H10M11.3,16.8L12,15.6L12.7,16.8H11.3Z"
                />
              </svg>
              <p class="text-gray-600 mb-2">Document PDF</p>
              <p class="text-sm text-gray-500">
                {{ pageSelectionnee.mediaName }}
              </p>
              <!-- Tu pourrais ajouter un embed PDF ici si nécessaire -->
              <iframe
                v-if="pageSelectionnee.media"
                :src="pageSelectionnee.media"
                class="w-full h-96 mt-4 border rounded"
              ></iframe>
            </div>

            <!-- Aperçu Vidéo -->
            <video
              v-else-if="pageSelectionnee.mediaType === 'video'"
              :src="pageSelectionnee.media"
              controls
              class="max-w-full max-h-full rounded-lg shadow-lg"
            >
              Votre navigateur ne supporte pas la lecture de vidéos.
            </video>
          </div>

          <!-- Si aucun média -->
          <div v-else class="text-center">
            <svg
              class="w-24 h-24 text-gray-300 mx-auto mb-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              ></path>
            </svg>
            <p class="text-gray-500 mb-6">Aucun média ajouté</p>
          </div>
        </div>

        <!-- Zone des boutons d'action -->
        <div class="p-6 border-t bg-gray-50">
          <div class="flex justify-center space-x-4">
            <!-- Bouton pour importer un média -->
            <button
              v-if="pageSelectionnee"
              @click="ouvrirSelecteurFichier"
              class="px-6 py-3 bg-pink-500 hover:bg-pink-600 text-white rounded-lg flex items-center transition-colors shadow-md"
            >
              <svg
                class="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 4v16m8-8H4"
                ></path>
              </svg>
              Importer un média
            </button>

            <!-- Bouton pour supprimer le média -->
            <button
              v-if="pageSelectionnee?.media"
              @click="supprimerMedia"
              class="px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg flex items-center transition-colors shadow-md"
            >
              <svg
                class="w-5 h-5 mr-2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                ></path>
              </svg>
              Supprimer le média
            </button>
          </div>

          <!-- Info sur les formats acceptés -->
          <p class="text-center text-sm text-gray-500 mt-4">
            Formats acceptés : Images (JPG, PNG, GIF), Vidéos (MP4, WebM), PDF
          </p>
        </div>
      </div>

      <!-- Input file caché -->
      <input
        ref="fileInput"
        type="file"
        @change="gererUploadFichier"
        accept="image/*,video/*,application/pdf"
        class="hidden"
      />
    </div>

    <!-- Panneau de propriétés -->
    <div class="w-80 bg-white shadow-lg p-6 overflow-y-auto">
      <h2 class="text-xl font-bold mb-6">Propriétés</h2>

      <div v-if="pageSelectionnee">
        <!-- Info sur le média -->
        <div
          v-if="pageSelectionnee.media"
          class="mb-6 p-4 bg-blue-50 rounded-lg"
        >
          <h3 class="text-sm font-semibold text-blue-900 mb-2">Média actuel</h3>
          <p class="text-sm text-blue-700">
            Type : {{ pageSelectionnee.mediaType }}
          </p>
          <p class="text-sm text-blue-700 truncate">
            Nom : {{ pageSelectionnee.mediaName }}
          </p>
          <p v-if="pageSelectionnee.mediaSize" class="text-sm text-blue-700">
            Taille : {{ formatFileSize(pageSelectionnee.mediaSize) }}
          </p>
        </div>

        <!-- Durée d'affichage -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Durée d'affichage
          </label>
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-600 w-12">Début</span>
            <input
              v-model="pageSelectionnee.dureeDebut"
              type="date"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div class="flex items-center space-x-2 mt-2">
            <span class="text-sm text-gray-600 w-12">Fin</span>
            <input
              v-model="pageSelectionnee.dureeFin"
              type="date"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <!-- Durée à l'écran -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Durée à l'écran (secondes)
          </label>
          <input
            v-model.number="pageSelectionnee.dureeAffichage"
            type="number"
            min="1"
            :disabled="pageSelectionnee.mediaType === 'video'"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <p
            v-if="pageSelectionnee.mediaType === 'video'"
            class="text-xs text-gray-500 mt-1"
          >
            Les vidéos utilisent leur durée native
          </p>
        </div>

        <!-- Type de transition -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Transition
          </label>
          <select
            v-model="pageSelectionnee.transition"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="none">Aucune</option>
            <option value="fade">Fondu</option>
            <option value="slide-left">Glissement gauche</option>
            <option value="slide-right">Glissement droite</option>
            <option value="slide-up">Glissement haut</option>
            <option value="slide-down">Glissement bas</option>
            <option value="zoom">Zoom</option>
          </select>
        </div>

        <!-- Mode d'affichage -->
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Mode d'affichage
          </label>
          <select
            v-model="pageSelectionnee.modeAffichage"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="cover">Couvrir (remplir l'écran)</option>
            <option value="contain">Contenir (afficher tout)</option>
            <option value="stretch">Étirer (déformer si nécessaire)</option>
          </select>
        </div>

        <!-- Répétition (pour les vidéos) -->
        <div v-if="pageSelectionnee.mediaType === 'video'" class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Répétition de la vidéo
          </label>
          <div class="flex items-center">
            <input
              type="checkbox"
              v-model="pageSelectionnee.loop"
              class="mr-2"
            />
            <span class="text-sm">Lire en boucle</span>
          </div>
        </div>
      </div>

      <!-- Message si aucune page sélectionnée -->
      <div v-else class="text-center text-gray-500">
        <p>Sélectionnez une page pour voir ses propriétés</p>
      </div>
    </div>
  </div>
</template>
