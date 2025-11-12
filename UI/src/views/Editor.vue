<script>
import { ref, computed, onMounted, watch } from "vue";
import { useAnnonceStore } from '../stores/annonceStore.js'
import draggable from 'vuedraggable'
import { supabase } from '../lib/supabaseClient.js'

export default {
  name: "AnnonceEditorWithMedia",
  components: {
    draggable
  },
  setup() {
    const annonceStore = useAnnonceStore()
    
    const pageActive = ref(1);
    const fileInput = ref(null);
    const isUploading = ref(false);
    const editingPageId = ref(null);
    const tempPageName = ref("");

    // Charger les annonces au démarrage
    onMounted(async () => {
      await annonceStore.chargerAnnonces()
      
      if (annonceStore.annonces.length > 0) {
        annonces.value = [...annonceStore.annonces]
      }
    })

    // Liste des annonces
    const annonces = ref([
      {
        id: 1,
        nom: "Page 1",
        media: null,
        mediaURL: null,
        mediaType: null,
        mediaName: null,
        mediaSize: null,
        linkURL: "",
        dureeDebut: "",
        dureeFin: "",
        dureeAffichage: 5,
        transition: "fade",
        modeAffichage: "cover",
        loop: false,
      },
    ]);

    // Synchroniser avec le store
    watch(annonces, async (newAnnonces) => {
      const annoncesToSave = newAnnonces.map(a => {
        const { mediaURL, ...rest } = a
        return rest
      })
      await annonceStore.sauvegarderAnnonces(annoncesToSave)
    }, { deep: true })

    const pageSelectionnee = computed(() => {
      return annonces.value.find((a) => a.id === pageActive.value);
    });

    const ajouterPage = () => {
      const nouvelId = Math.max(...annonces.value.map((a) => a.id), 0) + 1;
      const nouvellePage = {
        id: nouvelId,
        nom: `Page ${nouvelId}`,
        media: null,
        mediaURL: null,
        mediaType: null,
        mediaName: null,
        mediaSize: null,
        linkURL: "",
        dureeDebut: "",
        dureeFin: "",
        dureeAffichage: 5,
        transition: "fade",
        modeAffichage: "cover",
        loop: false,
      };
      annonces.value.push(nouvellePage);
      pageActive.value = nouvelId;
    };

    const supprimerPage = async (id) => {
      const pageToDelete = annonces.value.find(a => a.id === id);
      
      // Supprimer le média de Supabase si présent
      if (pageToDelete && pageToDelete.media) {
        try {
          await supabase.storage.from('backgrounds').remove([pageToDelete.media]);
          console.log('✅ Média supprimé de Supabase');
        } catch (error) {
          console.error('❌ Erreur suppression média:', error);
        }
      }
      
      annonces.value = annonces.value.filter((a) => a.id !== id);
      
      if (pageActive.value === id) {
        pageActive.value = annonces.value.length > 0 ? annonces.value[0].id : null;
      }
    };

    const ouvrirSelecteurFichier = () => {
      if (fileInput.value) {
        fileInput.value.click();
      }
    };

    const gererUploadFichier = async (event) => {
      const file = event.target.files[0];
      if (!file || !pageSelectionnee.value) return;

      // Vérifier la taille (500 MB max)
      const maxSize = 500 * 1024 * 1024;
      if (file.size > maxSize) {
        alert("Le fichier est trop volumineux. Taille maximale : 500 MB");
        return;
      }

      isUploading.value = true;

      try {
        // Déterminer le type de média
        let mediaType = null;
        if (file.type.startsWith("image/")) {
          mediaType = "image";
        } else if (file.type.startsWith("video/")) {
          mediaType = "video";
        } else if (file.type === "application/pdf") {
          mediaType = "pdf";
        }

        if (!mediaType) {
          alert("Format de fichier non supporté");
          isUploading.value = false;
          return;
        }

        // Supprimer l'ancien média de Supabase s'il existe
        if (pageSelectionnee.value.mediaURL && pageSelectionnee.value.media) {
          try {
            const oldFilePath = pageSelectionnee.value.media.split('/').pop();
            await supabase.storage.from('backgrounds').remove([oldFilePath]);
          } catch (err) {
            console.warn('Erreur suppression ancien fichier:', err);
          }
        }

        // Créer un nom de fichier unique et sécurisé
        const timestamp = Date.now();
        const safeFileName = file.name.replace(/[^a-zA-Z0-9.-]/g, '_');
        const fileName = `${timestamp}-${safeFileName}`;

        console.log('📤 Upload vers Supabase:', fileName);

        // Upload vers Supabase Storage
        const { data, error } = await supabase.storage
          .from('backgrounds')
          .upload(fileName, file, {
            cacheControl: '3600',
            upsert: false
          });
        
        if (error) {
          console.error('❌ Erreur upload:', error);
          alert(`Erreur lors de l'upload: ${error.message}`);
          isUploading.value = false;
          return;
        }

        // Récupérer l'URL publique
        const { data: urlData } = supabase.storage
          .from('backgrounds')
          .getPublicUrl(fileName);

        // Mettre à jour l'annonce avec l'URL Supabase
        pageSelectionnee.value.media = fileName;
        pageSelectionnee.value.mediaURL = urlData.publicUrl;
        pageSelectionnee.value.mediaType = mediaType;
        pageSelectionnee.value.mediaName = file.name;
        pageSelectionnee.value.mediaSize = file.size;

        console.log('✅ Média uploadé avec succès:', urlData.publicUrl);

      } catch (error) {
        console.error('❌ Erreur lors de l\'upload:', error);
        alert("Une erreur s'est produite lors de l'upload");
      } finally {
        isUploading.value = false;
        event.target.value = "";
      }
    };

    const supprimerMedia = async () => {
      if (!pageSelectionnee.value) return;
      
      // Supprimer de Supabase
      if (pageSelectionnee.value.media) {
        try {
          await supabase.storage.from('backgrounds').remove([pageSelectionnee.value.media]);
          console.log('✅ Média supprimé de Supabase');
        } catch (error) {
          console.error('❌ Erreur suppression:', error);
        }
      }
      
      // Réinitialiser les propriétés
      pageSelectionnee.value.media = null;
      pageSelectionnee.value.mediaURL = null;
      pageSelectionnee.value.mediaType = null;
      pageSelectionnee.value.mediaName = null;
      pageSelectionnee.value.mediaSize = null;
    };

    const formatFileSize = (bytes) => {
      if (bytes === 0) return "0 Bytes";
      const k = 1024;
      const sizes = ["Bytes", "KB", "MB", "GB"];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
    };

    const startEditingName = (annonce) => {
      editingPageId.value = annonce.id;
      tempPageName.value = annonce.nom;
    };

    const finishEditingName = (annonce) => {
      if (tempPageName.value.trim()) {
        annonce.nom = tempPageName.value.trim();
      }
      editingPageId.value = null;
      tempPageName.value = "";
    };

    const cancelEditingName = () => {
      editingPageId.value = null;
      tempPageName.value = "";
    };

    return {
      annonces,
      pageActive,
      pageSelectionnee,
      ajouterPage,
      supprimerPage,
      fileInput,
      ouvrirSelecteurFichier,
      gererUploadFichier,
      supprimerMedia,
      isUploading,
      formatFileSize,
      editingPageId,
      tempPageName,
      startEditingName,
      finishEditingName,
      cancelEditingName,
    };
  },
};
</script>

<template>
  <div class="flex flex-row justify-between items-center bg-white p-2 py-4 drop-shadow-xl">
    <div class="flex flex-row items-center mr-6 p-2">
      <router-link to="/" class="bg-gray-300 hover:bg-gray-400 text-gray-800 font-bold py-2 px-2 rounded-lg inline-flex items-center">
        <svg class="w-6 h-6 text-gray-800 dark:text-gray-700" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
          <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m4 12 8-8 8 8M6 10.5V19a1 1 0 0 0 1 1h3v-3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v3h3a1 1 0 0 0 1-1v-8.5" />
        </svg>
      </router-link>
      <div class="flex flex-row items-center gap-4">
        <img src="../assets/icons/etsflux.svg" alt="ETSFlux logo" class="w-28 ml-6 -mb-4" />
        <h1 class="text-black font-bold text-2xl">Éditeur d'annonces</h1>
      </div>
    </div>
  </div>

  <div class="flex h-screen bg-gray-100">
    <!-- Menu gauche -->
    <div class="w-80 bg-white shadow-lg p-4 flex flex-col">
      <button @click="ajouterPage" class="w-full mb-4 py-3 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg flex items-center justify-center transition-colors">
        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
        </svg>
        Ajouter une page
      </button>

      <div class="flex-1 overflow-hidden">
        <draggable v-model="annonces" item-key="id" class="space-y-2 h-full" :animation="200" handle=".drag-handle">
          <template #item="{ element: annonce }">
            <div :class="['p-3 rounded-lg cursor-pointer transition-all', pageActive === annonce.id ? 'bg-blue-100 border-2 border-blue-500' : 'bg-gray-50 hover:bg-gray-100']" @click="pageActive = annonce.id">
              <div class="flex items-center justify-between">
                <div class="flex items-center flex-1 min-w-0">
                  <svg class="w-5 h-5 text-gray-400 mr-2 drag-handle cursor-move flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z"></path>
                  </svg>

                  <svg v-if="!annonce.media" class="w-6 h-6 text-gray-400 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                  </svg>
                  <svg v-else-if="annonce.mediaType === 'image'" class="w-6 h-6 text-green-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd"></path>
                  </svg>
                  <svg v-else-if="annonce.mediaType === 'video'" class="w-6 h-6 text-red-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M2 6a2 2 0 012-2h6a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zM14.553 7.106A1 1 0 0014 8v4a1 1 0 00.553.894l2 1A1 1 0 0018 13V7a1 1 0 00-1.447-.894l-2 1z"></path>
                  </svg>
                  <svg v-else-if="annonce.mediaType === 'pdf'" class="w-6 h-6 text-blue-500 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
                  </svg>

                  <div class="flex-1 min-w-0">
                    <input v-if="editingPageId === annonce.id" v-model="tempPageName" @click.stop @keyup.enter="finishEditingName(annonce)" @keyup.esc="cancelEditingName" @blur="finishEditingName(annonce)" class="w-full px-2 py-1 text-sm font-medium border border-blue-500 rounded focus:outline-none focus:ring-2 focus:ring-blue-500" autofocus />
                    <p v-else @dblclick.stop="startEditingName(annonce)" class="font-medium text-sm truncate cursor-text" :title="'Double-cliquez pour renommer'">{{ annonce.nom }}</p>
                    <p v-if="annonce.media" class="text-xs text-gray-500 truncate">{{ annonce.mediaName }}</p>
                  </div>
                </div>

                <div class="flex items-center space-x-1 ml-2 flex-shrink-0">
                  <button v-if="editingPageId !== annonce.id" @click.stop="startEditingName(annonce)" class="p-1 hover:bg-blue-100 rounded text-blue-500" title="Renommer">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                    </svg>
                  </button>
                  <button @click.stop="supprimerPage(annonce.id)" class="p-1 hover:bg-red-100 rounded text-red-500" title="Supprimer">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          </template>
        </draggable>
      </div>
    </div>

    <!-- Zone centrale -->
    <div class="flex-1 flex flex-col">
      <div class="bg-white shadow-md p-4">
        <h2 class="text-2xl font-bold text-gray-800">{{ pageSelectionnee?.nom || "Aperçu" }}</h2>
      </div>

      <div class="flex-1 flex flex-col p-8">
        <div class="flex-1 bg-white rounded-lg shadow-lg flex items-center justify-center overflow-hidden relative">
          <div v-if="isUploading" class="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div class="text-center">
              <svg class="animate-spin h-16 w-16 text-white mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <p class="text-white text-lg font-semibold">Sauvegarde en cours...</p>
            </div>
          </div>

          <div v-if="pageSelectionnee?.mediaURL && !isUploading" class="w-full h-full flex items-center justify-center">
            <img v-if="pageSelectionnee.mediaType === 'image'" :src="pageSelectionnee.mediaURL" :alt="pageSelectionnee.mediaName" class="max-w-full max-h-full object-contain" />
            <div v-else-if="pageSelectionnee.mediaType === 'pdf'" class="w-full h-full flex flex-col items-center justify-center p-4">
              <iframe :src="pageSelectionnee.mediaURL" class="w-full h-96 mt-4 border rounded"></iframe>
            </div>
            <video v-else-if="pageSelectionnee.mediaType === 'video'" :src="pageSelectionnee.mediaURL" controls class="max-w-full max-h-full rounded-lg shadow-lg"></video>
          </div>

          <div v-else-if="!isUploading" class="text-center">
            <svg class="w-24 h-24 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
            <p class="text-gray-500 mb-6">Aucun média ajouté</p>
          </div>
        </div>

        <div class="mt-6 bg-white p-6 rounded-lg shadow-lg">
          <div class="flex justify-center space-x-4 mb-4">
            <button v-if="pageSelectionnee" @click="ouvrirSelecteurFichier" :disabled="isUploading" class="px-6 py-3 bg-pink-500 hover:bg-pink-600 text-white rounded-lg flex items-center transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
              </svg>
              Importer un média
            </button>
            <button v-if="pageSelectionnee?.media" @click="supprimerMedia" :disabled="isUploading" class="px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg flex items-center transition-colors shadow-md disabled:opacity-50 disabled:cursor-not-allowed">
              <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
              Supprimer le média
            </button>
          </div>

          <div class="text-center border-t pt-4">
            <p class="text-sm text-gray-600 font-medium">Formats acceptés : Images (JPG, PNG, GIF), Vidéos (MP4, WebM)</p>
            <p class="text-xs text-gray-500 mt-1">Taille maximale : 500 MB</p>
          </div>
        </div>
      </div>

      <input ref="fileInput" type="file" @change="gererUploadFichier" accept="image/*,video/*,application/pdf" class="hidden" />
    </div>

    <!-- Panneau propriétés -->
    <div class="w-80 bg-white shadow-lg p-6 overflow-y-auto">
      <h2 class="text-xl font-bold mb-6">Propriétés</h2>

      <div v-if="pageSelectionnee">
        <div v-if="pageSelectionnee.media" class="mb-6 p-4 bg-blue-50 rounded-lg">
          <h3 class="text-sm font-semibold text-blue-900 mb-2">Média actuel</h3>
          <p class="text-sm text-blue-700">Type : {{ pageSelectionnee.mediaType }}</p>
          <p class="text-sm text-blue-700 truncate">Nom : {{ pageSelectionnee.mediaName }}</p>
          <p v-if="pageSelectionnee.mediaSize" class="text-sm text-blue-700">Taille : {{ formatFileSize(pageSelectionnee.mediaSize) }}</p>
        </div>


        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">Lien URL</label>
          <input 
            v-model="pageSelectionnee.linkURL" 
            type="url" 
            placeholder="https://example.com" 
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" 
          />
          <p class="text-xs text-gray-500 mt-1">Optionnel : Ajouter un lien qui s'affichera avec l'annonce</p>
        </div>
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">Durée d'affichage</label>
          <div class="flex items-center space-x-2">
            <span class="text-sm text-gray-600 w-12">Début</span>
            <input v-model="pageSelectionnee.dureeDebut" type="date" class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div class="flex items-center space-x-2 mt-2">
            <span class="text-sm text-gray-600 w-12">Fin</span>
            <input v-model="pageSelectionnee.dureeFin" type="date" class="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
        </div>

        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">Durée à l'écran (secondes)</label>
          <input v-model.number="pageSelectionnee.dureeAffichage" type="number" min="1" :disabled="pageSelectionnee.mediaType === 'video'" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100" />
          <p v-if="pageSelectionnee.mediaType === 'video'" class="text-xs text-gray-500 mt-1">Les vidéos utilisent leur durée native</p>
        </div>

        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">Transition</label>
          <select v-model="pageSelectionnee.transition" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="none">Aucune</option>
            <option value="fade">Fondu</option>
            <option value="slide-left">Glissement gauche</option>
            <option value="slide-right">Glissement droite</option>
            <option value="slide-up">Glissement haut</option>
            <option value="slide-down">Glissement bas</option>
            <option value="zoom">Zoom</option>
          </select>
        </div>

        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">Mode d'affichage</label>
          <select v-model="pageSelectionnee.modeAffichage" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
            <option value="cover">Couvrir (remplir l'écran)</option>
            <option value="contain">Contenir (afficher tout)</option>
            <option value="stretch">Étirer (déformer si nécessaire)</option>
          </select>
        </div>

        <div v-if="pageSelectionnee.mediaType === 'video'" class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">Répétition de la vidéo</label>
          <div class="flex items-center">
            <input type="checkbox" v-model="pageSelectionnee.loop" class="mr-2" />
            <span class="text-sm">Lire en boucle</span>
          </div>
        </div>
      </div>

      <div v-else class="text-center text-gray-500">
        <p>Sélectionnez une page pour voir ses propriétés</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.drag-handle {
  cursor: move;
  cursor: grab;
}
.drag-handle:active {
  cursor: grabbing;
}
</style>