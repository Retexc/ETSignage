<template>
  <div class="relative w-full h-screen overflow-hidden bg-gray-100 p-8">
    <div class="announcement-preview bg-white rounded-lg shadow-lg overflow-hidden h-full relative">
      
      <!-- Conteneur d'affichage -->
      <div class="absolute inset-0 w-full h-full bg-black flex items-center justify-center overflow-hidden">
        
        <!-- Si aucune annonce -->
        <div v-if="!currentAnnonce" class="flex items-center justify-center w-full h-full bg-gradient-to-br from-indigo-500 to-purple-600">
          <div class="text-center">
            <svg class="w-32 h-32 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
            </svg>
            <h2 class="text-2xl font-semibold text-white mb-2">Aucune annonce à afficher</h2>
            <p class="text-gray-200">Ajoutez du contenu dans l'éditeur</p>
          </div>
        </div>

        <!-- Affichage du média actuel -->
        <div v-else class="w-full h-full relative overflow-hidden">
          
          <!-- Affichage pour IMAGE -->
          <transition :name="currentAnnonce.transition" mode="out-in">
            <div 
              v-if="currentAnnonce.mediaType === 'image'" 
              :key="'img-' + currentAnnonce.id + '-' + currentPage"
              class="w-full h-full flex items-center justify-center overflow-hidden"
            >
              <img 
                :src="currentAnnonce.mediaURL"
                :alt="currentAnnonce.nom"
                :class="getMediaClass(currentAnnonce.modeAffichage)"
                @load="onMediaLoaded"
              >
            </div>
          </transition>

          <!-- Affichage pour VIDEO -->
          <transition :name="currentAnnonce.transition" mode="out-in">
            <div 
              v-if="currentAnnonce.mediaType === 'video'" 
              :key="'vid-' + currentAnnonce.id + '-' + currentPage"
              class="w-full h-full flex items-center justify-center overflow-hidden"
            >
              <video
                ref="videoPlayer"
                :src="currentAnnonce.mediaURL"
                :class="getMediaClass(currentAnnonce.modeAffichage)"
                :loop="currentAnnonce.loop"
                autoplay
                muted
                @ended="onVideoEnd"
                @loadedmetadata="onVideoLoaded"
              >
                Votre navigateur ne supporte pas la lecture de vidéos.
              </video>
            </div>
          </transition>

          <!-- Affichage pour PDF -->
          <transition :name="currentAnnonce.transition" mode="out-in">
            <div 
              v-if="currentAnnonce.mediaType === 'pdf'" 
              :key="'pdf-' + currentAnnonce.id + '-' + currentPage"
              class="w-full h-full flex items-center justify-center overflow-hidden p-5 bg-white"
            >
              <iframe 
                :src="currentAnnonce.mediaURL"
                class="w-full h-full"
                @load="onMediaLoaded"
              ></iframe>
            </div>
          </transition>

          <!-- 🆕 Affichage pour URL WEB (quand il n'y a pas de média) -->
          <transition :name="currentAnnonce.transition" mode="out-in">
            <div 
              v-if="!currentAnnonce.mediaType && currentAnnonce.linkURL" 
              :key="'url-' + currentAnnonce.id + '-' + currentPage"
              class="w-full h-full flex items-center justify-center overflow-hidden bg-white"
            >
              <iframe 
                :src="currentAnnonce.linkURL"
                class="w-full h-full border-0"
                @load="onMediaLoaded"
                @error="onMediaError"
                sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-downloads"
              ></iframe>
            </div>
          </transition>

          <!-- Indicateur de page -->
          <div class="absolute bottom-4 right-4 bg-black/70 backdrop-blur-lg px-4 py-2 rounded-full z-50">
            <div class="text-white text-sm font-medium">
              {{ currentPage + 1 }} / {{ totalAnnonces }}
            </div>
          </div>

          <!-- Badge "PREVIEW" -->
          <div class="absolute top-4 left-4 bg-red-500 backdrop-blur-lg px-4 py-2 rounded-full z-50 flex items-center gap-2">
            <div class="w-2 h-2 bg-white rounded-full animate-pulse"></div>
            <span class="text-white text-xs font-bold uppercase">Aperçu</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

import { useAnnonceStore } from '../stores/annonceStore.js'

// Store Pinia
const annonceStore = useAnnonceStore()

// État local du Preview
const allAnnonces = ref([])
const currentPage = ref(0)
const currentAnnonce = ref(null)
const totalAnnonces = ref(0)

const videoPlayer = ref(null)
const currentTimer = ref(null)
const refreshTimer = ref(null)

// Méthodes pour gérer les classes CSS
const getMediaClass = (mode) => {
  switch(mode) {
    case 'cover':
      return 'w-full h-full object-cover'
    case 'contain':
      return 'w-full h-full object-contain'
    case 'stretch':
      return 'w-full h-full object-fill'
    default:
      return 'w-full h-full object-cover'
  }
}

// Charger les annonces depuis Supabase
const loadAnnonces = async () => {
  try {
    // Charger depuis Supabase (qui reconstruit automatiquement les mediaURL)
    await annonceStore.chargerAnnonces()
    const annonces = annonceStore.annonces
    
    // Filtrer les annonces avec média OU avec linkURL
    const validAnnonces = annonces.filter(a => 
      a.media !== null || (a.linkURL && a.linkURL.trim() !== '')
    )
    
    console.log('📊 [PREVIEW] Annonces valides trouvées:', validAnnonces.length)
    
    // Si la liste a changé, réinitialiser
    if (JSON.stringify(validAnnonces.map(a => a.id)) !== JSON.stringify(allAnnonces.value.map(a => a.id))) {
      console.log('🔄 [PREVIEW] Nouvelles annonces détectées:', validAnnonces.length)
      allAnnonces.value = validAnnonces
      totalAnnonces.value = validAnnonces.length
      
      // Réinitialiser à la première page si nécessaire
      if (currentPage.value >= validAnnonces.length) {
        currentPage.value = 0
      }
      
      // Mettre à jour l'annonce actuelle
      if (validAnnonces.length > 0) {
        currentAnnonce.value = validAnnonces[currentPage.value]
        console.log('✅ [PREVIEW] Annonce actuelle:', currentAnnonce.value.nom)
        console.log('📄 [PREVIEW] Type:', currentAnnonce.value.mediaType || 'URL Web')
        if (currentAnnonce.value.linkURL) {
          console.log('🔗 [PREVIEW] URL:', currentAnnonce.value.linkURL)
        }
      } else {
        currentAnnonce.value = null
      }
    }
  } catch (error) {
    console.error('❌ [PREVIEW] Erreur chargement:', error)
  }
}

// Passer à la page suivante
const nextPage = () => {
  if (allAnnonces.value.length === 0) return
  
  console.log('➡️ [PREVIEW] Page suivante...')
  currentPage.value = (currentPage.value + 1) % allAnnonces.value.length
  currentAnnonce.value = allAnnonces.value[currentPage.value]
  
  console.log(`📄 [PREVIEW] Page ${currentPage.value + 1}/${totalAnnonces.value}:`, currentAnnonce.value.nom)
  
  // Si on revient au début, recharger les données
  if (currentPage.value === 0) {
    console.log('🔄 [PREVIEW] Cycle complet - Rechargement...')
    loadAnnonces()
  }
}

// Démarrer le timer
const startTimer = () => {
  if (currentTimer.value) {
    clearTimeout(currentTimer.value)
  }
  
  // Démarrer le timer pour tout sauf les vidéos
  if (currentAnnonce.value && currentAnnonce.value.mediaType !== 'video') {
    const duration = (currentAnnonce.value.dureeAffichage || 5) * 1000
    console.log(`⏱️ [PREVIEW] Timer démarré: ${duration}ms`)
    currentTimer.value = setTimeout(() => {
      nextPage()
    }, duration)
  }
}

// Événements média
const onMediaLoaded = () => {
  console.log('✅ [PREVIEW] Contenu chargé:', currentAnnonce.value?.nom)
  startTimer()
}

const onVideoLoaded = () => {
  console.log('✅ [PREVIEW] Vidéo chargée:', currentAnnonce.value?.nom)
  if (videoPlayer.value) {
    videoPlayer.value.play().catch(err => {
      console.error('❌ [PREVIEW] Erreur lecture vidéo:', err)
      setTimeout(() => nextPage(), 2000)
    })
  }
}

const onVideoEnd = () => {
  console.log('🎬 [PREVIEW] Vidéo terminée')
  if (!currentAnnonce.value?.loop) {
    nextPage()
  }
}

const onMediaError = (error) => {
  console.error('❌ [PREVIEW] Erreur de chargement:', error)
  console.log('⚠️ [PREVIEW] Le contenu ne peut pas être chargé - passage au suivant...')
  setTimeout(() => {
    nextPage()
  }, 2000)
}

// Lifecycle
onMounted(async () => {
  console.log('🚀 [PREVIEW] Démarrage du preview...')
  
  // 🆕 Initialiser IndexedDB
  await annonceStore.chargerAnnonces()
  
  // Chargement initial
  await loadAnnonces()
  
  // Démarrer le timer si on a du contenu
  if (currentAnnonce.value) {
    if (currentAnnonce.value.mediaType === 'image' || 
        currentAnnonce.value.mediaType === 'pdf' ||
        (!currentAnnonce.value.mediaType && currentAnnonce.value.linkURL)) {
      startTimer()
    }
  }

  // Recharger toutes les 2 secondes pour détecter les nouveaux contenus
  refreshTimer.value = setInterval(() => {
    loadAnnonces()
  }, 2000)
})

onUnmounted(() => {
  console.log('🛑 [PREVIEW] Arrêt du preview...')
  
  if (currentTimer.value) {
    clearTimeout(currentTimer.value)
  }
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
  }
})
</script>

<style scoped>
/* Container du preview */
.announcement-preview {
  position: relative;
}

.announcement-preview :deep(*) {
  max-width: 100%;
  box-sizing: border-box;
}

/* Transitions */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.slide-left-enter-active, .slide-left-leave-active {
  transition: transform 0.5s;
}
.slide-left-enter-from {
  transform: translateX(100%);
}
.slide-left-leave-to {
  transform: translateX(-100%);
}

.slide-right-enter-active, .slide-right-leave-active {
  transition: transform 0.5s;
}
.slide-right-enter-from {
  transform: translateX(-100%);
}
.slide-right-leave-to {
  transform: translateX(100%);
}

.slide-up-enter-active, .slide-up-leave-active {
  transition: transform 0.5s;
}
.slide-up-enter-from {
  transform: translateY(100%);
}
.slide-up-leave-to {
  transform: translateY(-100%);
}

.slide-down-enter-active, .slide-down-leave-active {
  transition: transform 0.5s;
}
.slide-down-enter-from {
  transform: translateY(-100%);
}
.slide-down-leave-to {
  transform: translateY(100%);
}

.zoom-enter-active, .zoom-leave-active {
  transition: transform 0.5s, opacity 0.5s;
}
.zoom-enter-from {
  transform: scale(0);
  opacity: 0;
}
.zoom-leave-to {
  transform: scale(2);
  opacity: 0;
}

/* Animation du badge */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>