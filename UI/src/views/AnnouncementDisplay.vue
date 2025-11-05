<template>
  <Header class="fixed top-0 left-0 w-full z-50" />
  
  <div class="fixed inset-0 w-screen h-screen bg-black flex items-center justify-center overflow-hidden pt-16">
    
    <!-- aucune annonce -->
    <div v-if="!annonceActuelle" class="flex items-center justify-center w-full h-full bg-gradient-to-br from-indigo-500 to-purple-600">
      <div class="text-center">
        <svg class="w-32 h-32 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path>
        </svg>
        <h2 class="text-2xl font-semibold text-gray-600 mb-2">Aucune annonce à afficher</h2>
        <p class="text-gray-500">Ajoutez du contenu dans l'éditeur</p>
        <router-link to="/editor" class="mt-4 inline-block px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors">
          Aller à l'éditeur
        </router-link>
      </div>
    </div>

    <!-- Affichage du contenu actuel -->
    <div v-else class="w-full h-full relative overflow-hidden">
      
      <!-- Affichage pour IMAGE -->
      <transition :name="annonceActuelle.transition" mode="out-in">
        <div 
          v-if="annonceActuelle.mediaType === 'image'" 
          :key="annonceActuelle.id"
          class="w-full h-full flex items-center justify-center overflow-hidden"
        >
          <img 
            :src="annonceActuelle.mediaURL"
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
          class="w-full h-full flex items-center justify-center overflow-hidden"
        >
          <video
            ref="videoPlayer"
            :src="annonceActuelle.mediaURL"
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
          class="w-full h-full flex items-center justify-center overflow-hidden p-5 bg-white"
        >
          <iframe 
            :src="annonceActuelle.mediaURL"
            class="w-full h-full"
            @load="onMediaLoaded"
          ></iframe>
        </div>
      </transition>

      <!-- 🆕 Affichage pour URL WEB (quand il n'y a pas de média) -->
      <transition :name="annonceActuelle.transition" mode="out-in">
        <div 
          v-if="!annonceActuelle.mediaType && annonceActuelle.linkURL" 
          :key="'url-' + annonceActuelle.id"
          class="w-full h-full flex items-center justify-center overflow-hidden bg-white"
        >
          <iframe 
            :src="annonceActuelle.linkURL"
            class="w-full h-full border-0"
            @load="onMediaLoaded"
            @error="onMediaError"
            sandbox="allow-same-origin allow-scripts allow-popups allow-forms allow-downloads"
          ></iframe>
        </div>
      </transition>

      <div v-if="showControls && totalAnnonces > 0" class="fixed bottom-8 left-1/2 transform -translate-x-1/2 flex items-center gap-5 bg-black/70 backdrop-blur-lg px-5 py-2.5 rounded-full z-[100] transition-opacity duration-300 md:opacity-0 md:hover:opacity-100">
        <button @click="previousPage" class="w-10 h-10 rounded-full bg-white/20 text-white border-0 cursor-pointer flex items-center justify-center transition-all duration-300 hover:bg-white/30 hover:scale-110">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
          </svg>
        </button>
        
        <div class="text-white text-sm min-w-[60px] text-center">
          {{ pageActuelle + 1 }} / {{ totalAnnonces }}
        </div>
        
        <button @click="nextPage" class="w-10 h-10 rounded-full bg-white/20 text-white border-0 cursor-pointer flex items-center justify-center transition-all duration-300 hover:bg-white/30 hover:scale-110">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
          </svg>
        </button>

        <button @click="togglePause" class="w-10 h-10 rounded-full bg-white/20 text-white border-0 cursor-pointer flex items-center justify-center transition-all duration-300 hover:bg-white/30 hover:scale-110 ml-4">
          <svg v-if="!isPaused" class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 9v6m4-6v6"></path>
          </svg>
          <svg v-else class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path>
          </svg>
        </button>
        
        <button @click="rechargerAnnonces" class="w-10 h-10 rounded-full bg-white/20 text-white border-0 cursor-pointer flex items-center justify-center transition-all duration-300 hover:bg-white/30 hover:scale-110 ml-4" title="Recharger les annonces">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
        </button>
      </div>
    </div>
  </div>
  <AlertBanner />
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useAnnonceStore } from '../stores/annonceStore.js'
import Header from "../components/Header.vue"
import AlertBanner from "../components/AlertBanner.vue"

// Store Pinia
const annonceStore = useAnnonceStore()

// Refs
const videoPlayer = ref(null)
const currentTimer = ref(null)
const showControls = ref(false)
const cycleComplet = ref(false)


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

// Recharger les annonces depuis localStorage
const rechargerAnnonces = async () => {
  console.log('🔄 Rechargement des annonces depuis Supabase...')
  await annonceStore.chargerAnnonces()
  console.log('✅ Annonces rechargées')
}

// Gestion du timer pour passer à la page suivante
const startTimer = () => {
  if (currentTimer.value) {
    clearTimeout(currentTimer.value)
  }
  
  // Démarrer le timer seulement si ce n'est pas une vidéo
  if (!isPaused.value && annonceActuelle.value && annonceActuelle.value.mediaType !== 'video') {
    const duration = annonceActuelle.value.dureeAffichage * 1000 || 5000
    console.log(`⏱️ Timer démarré pour ${duration}ms`)
    currentTimer.value = setTimeout(() => {
      nextPage()
    }, duration)
  }
}

// Navigation
const nextPage = () => {
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
  console.log('✅ Contenu chargé:', annonceActuelle.value?.nom)
  console.log('📄 Type:', annonceActuelle.value?.mediaType || 'URL Web')
  console.log('🔗 URL:', annonceActuelle.value?.linkURL)
  
  // Démarrer le timer pour les images, PDFs et URLs web
  if (annonceActuelle.value?.mediaType === 'image' || 
      annonceActuelle.value?.mediaType === 'pdf' ||
      (!annonceActuelle.value?.mediaType && annonceActuelle.value?.linkURL)) {
    startTimer()
  }
}

const onVideoLoaded = () => {
  console.log('✅ Vidéo chargée:', annonceActuelle.value?.nom)
  if (videoPlayer.value && !isPaused.value) {
    videoPlayer.value.play().catch(err => {
      console.error('❌ Erreur lecture vidéo:', err)
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
  console.error('❌ Erreur de chargement:', error)
  console.log('⚠️ Le contenu ne peut pas être chargé - passage au suivant...')
  setTimeout(() => {
    nextPage()
  }, 2000)
}

// Gestion de la sortie de veille
const handleVisibilityChange = async () => {
  if (document.visibilityState === 'visible') {
    console.log('Page visible - Vérification des médias...')
    
    await rechargerAnnonces()
    
    if (videoPlayer.value && annonceActuelle.value?.mediaType === 'video') {
      videoPlayer.value.load()
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
    console.log('📢 Annonce changée:', newVal.nom)
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
onMounted(async () => {
  document.body.classList.add('overflow-hidden')
  document.documentElement.classList.add('overflow-hidden')
  
  await annonceStore.chargerAnnonces()

  console.log('📊 Annonces chargées:', annonceStore.annonces.length)
  console.log('📊 Annonces valides:', totalAnnonces.value)
  
  // Démarrer la lecture
  annonceStore.demarrerLecture()
  
  // Démarrer le timer si nécessaire
  if (annonceActuelle.value) {
    console.log('Démarrage avec:', annonceActuelle.value.nom)
    startTimer()
  }

  // Écouter les changements de visibilité 
  document.addEventListener('visibilitychange', handleVisibilityChange)
  
  window.addEventListener('keydown', handleKeyPress)
})

onUnmounted(() => {
  document.body.classList.remove('overflow-hidden')
  document.documentElement.classList.remove('overflow-hidden')
  
  if (currentTimer.value) {
    clearTimeout(currentTimer.value)
  }
  annonceStore.arreterLecture()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
  window.removeEventListener('keydown', handleKeyPress)
})

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
      e.preventDefault()
      rechargerAnnonces()
      break
  }
}
</script>

<style scoped>
:deep(body), 
:deep(html) {
  overflow: hidden !important;
  scrollbar-width: none; 
  -ms-overflow-style: none; 
}

:deep(body)::-webkit-scrollbar,
:deep(html)::-webkit-scrollbar {
  display: none; 
}

iframe {
  overflow: hidden !important;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

iframe::-webkit-scrollbar {
  display: none;
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
</style>