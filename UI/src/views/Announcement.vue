<template>
  <Header />
  
  <!-- Conteneur principal -->
  <div class="announcement-container">
    
    <!-- Si aucune annonce avec média -->
    <div v-if="!annonceActuelle" class="no-content">
      <div class="text-center">
        <svg class="w-32 h-32 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
        </svg>
        <h2 class="text-2xl font-semibold text-gray-600 mb-2">Aucune annonce à afficher</h2>
        <p class="text-gray-500">Ajoutez du contenu dans l'éditeur</p>
        <router-link to="/editor" class="mt-4 inline-block px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg">
          Aller à l'éditeur
        </router-link>
      </div>
    </div>

    <!-- Affichage du média actuel -->
    <div v-else class="media-display">
      
      <!-- Affichage pour IMAGE -->
      <transition :name="annonceActuelle.transition" mode="out-in">
        <div 
          v-if="annonceActuelle.mediaType === 'image'" 
          :key="annonceActuelle.id"
          class="media-wrapper"
        >
          <img 
            :src="annonceActuelle.media"
            :alt="annonceActuelle.nom"
            :class="getMediaClass(annonceActuelle.modeAffichage)"
            @load="onMediaLoaded"
            @error="onMediaError"
          >
        </div>
      </transition>

      <!-- Affichage pour VIDEO -->
      <transition :name="annonceActuelle.transition" mode="out-in">
        <div 
          v-if="annonceActuelle.mediaType === 'video'" 
          :key="annonceActuelle.id"
          class="media-wrapper"
        >
          <video
            ref="videoPlayer"
            :src="annonceActuelle.media"
            :class="getMediaClass(annonceActuelle.modeAffichage)"
            :loop="annonceActuelle.loop"
            autoplay
            muted
            @ended="onVideoEnd"
            @error="onMediaError"
            @loadedmetadata="onVideoLoaded"
          >
            Votre navigateur ne supporte pas la lecture de vidéos.
          </video>
        </div>
      </transition>

      <!-- Affichage pour PDF -->
      <transition :name="annonceActuelle.transition" mode="out-in">
        <div 
          v-if="annonceActuelle.mediaType === 'pdf'" 
          :key="annonceActuelle.id"
          class="media-wrapper pdf-wrapper"
        >
          <iframe 
            :src="annonceActuelle.media"
            class="w-full h-full"
            @load="onMediaLoaded"
          ></iframe>
        </div>
      </transition>
    </div>

    <!-- Contrôles de navigation (optionnel, pour tester) -->
    <div v-if="showControls && totalAnnonces > 0" class="controls">
      <button @click="previousPage" class="control-btn">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
        </svg>
      </button>
      
      <div class="page-indicator">
        {{ pageActuelle + 1 }} / {{ totalAnnonces }}
      </div>
      
      <button @click="nextPage" class="control-btn">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
        </svg>
      </button>

      <button @click="togglePause" class="control-btn ml-4">
        <svg v-if="!isPaused" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6"></path>
        </svg>
        <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
        </svg>
      </button>
      
      <!-- 🆕 NOUVEAU : Bouton pour recharger manuellement -->
      <button @click="rechargerAnnonces" class="control-btn ml-4" title="Recharger les annonces">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAnnonceStore } from '../stores/annonceStore.js'
import Header from "../components/Header.vue"

// Store Pinia
const annonceStore = useAnnonceStore()

// Refs
const videoPlayer = ref(null)
const currentTimer = ref(null)
const showControls = ref(true) // Mettre à false pour cacher les contrôles
const cycleComplet = ref(false) // 🆕 Pour savoir si on a fait un cycle complet

// Computed
const annonceActuelle = computed(() => annonceStore.annonceActuelle)
const totalAnnonces = computed(() => annonceStore.totalAnnonces)
const pageActuelle = computed(() => annonceStore.pageActuelle)
const isPaused = computed(() => annonceStore.isPaused)

// Méthodes pour gérer les classes CSS selon le mode d'affichage
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

// 🆕 NOUVELLE FONCTION : Recharger les annonces depuis localStorage
const rechargerAnnonces = () => {
  console.log('🔄 Rechargement des annonces...')
  annonceStore.chargerLocal()
  console.log('✅ Annonces rechargées')
}

// Gestion du timer pour passer à la page suivante
const startTimer = () => {
  if (currentTimer.value) {
    clearTimeout(currentTimer.value)
  }
  
  if (!isPaused.value && annonceActuelle.value && annonceActuelle.value.mediaType !== 'video') {
    const duration = annonceActuelle.value.dureeAffichage * 1000 || 5000
    currentTimer.value = setTimeout(() => {
      nextPage()
    }, duration)
  }
}

// Navigation
const nextPage = () => {
  // 🆕 AMÉLIORATION : Détecter quand on revient au début
  const totalPages = totalAnnonces.value
  const pageAvant = pageActuelle.value
  
  annonceStore.pageSuivante()
  
  // Si on revient à la page 0, c'est qu'on a fait un cycle complet
  if (pageAvant === totalPages - 1 && annonceStore.pageActuelle === 0) {
    console.log('🔄 Cycle complet terminé - Rechargement des données...')
    rechargerAnnonces()
  }
}

const previousPage = () => {
  const newIndex = pageActuelle.value - 1
  if (newIndex >= 0) {
    annonceStore.allerALaPage(newIndex)
  } else {
    annonceStore.allerALaPage(totalAnnonces.value - 1)
  }
}

const togglePause = () => {
  if (isPaused.value) {
    annonceStore.reprendreLecture()
    startTimer()
  } else {
    annonceStore.pauseLecture()
    if (currentTimer.value) {
      clearTimeout(currentTimer.value)
    }
  }
}

// Événements média
const onMediaLoaded = () => {
  console.log('✅ Média chargé:', annonceActuelle.value?.nom)
  if (annonceActuelle.value?.mediaType === 'image' || annonceActuelle.value?.mediaType === 'pdf') {
    startTimer()
  }
}

const onVideoLoaded = () => {
  console.log('✅ Vidéo chargée:', annonceActuelle.value?.nom)
  if (videoPlayer.value && !isPaused.value) {
    videoPlayer.value.play().catch(err => {
      console.error('❌ Erreur lecture vidéo:', err)
      // En cas d'erreur, passer au suivant après 2 secondes
      setTimeout(() => nextPage(), 2000)
    })
  }
}

const onVideoEnd = () => {
  console.log('🎬 Vidéo terminée')
  if (!annonceActuelle.value?.loop) {
    nextPage()
  }
}

const onMediaError = (error) => {
  console.error('❌ Erreur média:', error)
  console.log('⚠️ Le média ne peut pas être chargé - passage au suivant...')
  // Passer au média suivant après 2 secondes en cas d'erreur
  setTimeout(() => {
    nextPage()
  }, 2000)
}

// 🆕 NOUVEAU : Gestion de la sortie de veille
const handleVisibilityChange = () => {
  if (document.visibilityState === 'visible') {
    console.log('👀 Page visible - Vérification des médias...')
    
    // Recharger les annonces au cas où les liens blob auraient expiré
    rechargerAnnonces()
    
    // Relancer la vidéo si nécessaire
    if (videoPlayer.value && annonceActuelle.value?.mediaType === 'video') {
      videoPlayer.value.load() // Recharger la vidéo
      if (!isPaused.value) {
        videoPlayer.value.play().catch(err => {
          console.error('❌ Erreur relance vidéo après veille:', err)
        })
      }
    }
  }
}

// Watchers
watch(annonceActuelle, (newVal) => {
  if (newVal) {
    startTimer()
  }
})

watch(isPaused, (newVal) => {
  if (videoPlayer.value) {
    if (newVal) {
      videoPlayer.value.pause()
    } else {
      videoPlayer.value.play()
    }
  }
})

// Lifecycle
onMounted(() => {
  // Charger les annonces depuis le localStorage
  annonceStore.chargerLocal()
  
  // Démarrer la lecture
  annonceStore.demarrerLecture()
  
  // Démarrer le timer si nécessaire
  if (annonceActuelle.value) {
    startTimer()
  }

  // 🆕 NOUVEAU : Écouter les changements de visibilité (sortie de veille)
  document.addEventListener('visibilitychange', handleVisibilityChange)
  
  // Gestion des raccourcis clavier (optionnel)
  window.addEventListener('keydown', handleKeyPress)
})

onUnmounted(() => {
  if (currentTimer.value) {
    clearTimeout(currentTimer.value)
  }
  annonceStore.arreterLecture()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  window.removeEventListener('keydown', handleKeyPress)
})

// Gestion des touches clavier (optionnel)
const handleKeyPress = (e) => {
  if (!showControls.value) return
  
  switch(e.key) {
    case 'ArrowLeft':
      previousPage()
      break
    case 'ArrowRight':
      nextPage()
      break
    case ' ':
      e.preventDefault()
      togglePause()
      break
    case 'r':
    case 'R':
      // 🆕 Raccourci clavier pour recharger (touche R)
      e.preventDefault()
      rechargerAnnonces()
      break
  }
}
</script>

<style scoped>
.announcement-container {
  width: 100%;
  height: 100vh;
  background: black;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.no-content {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.media-display {
  width: 100%;
  height: 100%;
  position: relative;
}

.media-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pdf-wrapper {
  padding: 20px;
  background: white;
}

/* Contrôles de navigation */
.controls {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 20px;
  background: rgba(0, 0, 0, 0.7);
  padding: 10px 20px;
  border-radius: 50px;
  backdrop-filter: blur(10px);
}

.control-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.control-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: scale(1.1);
}

.page-indicator {
  color: white;
  font-size: 14px;
  min-width: 60px;
  text-align: center;
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

/* Mode plein écran pour production */
@media (min-width: 768px) {
  .controls {
    opacity: 0;
    transition: opacity 0.3s;
  }
  
  .announcement-container:hover .controls {
    opacity: 1;
  }
}
</style>