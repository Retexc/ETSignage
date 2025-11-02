<script setup>
import { onMounted, onUnmounted, watch, computed, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from './stores/authStore';
import Sidebar from "./components/SideBar.vue";
import './style.css';

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const isAppReady = ref(false);
const isRouteReady = ref(false);

const isDisplayPage = computed(() => {
  return route.path === '/display' || route.path === '/stm';
});

const shouldShowContent = computed(() => {
  return isAppReady.value && isRouteReady.value;
});

// 🎯 Liste des routes publiques (qui ne nécessitent PAS de connexion)
const publicRoutes = ['/login', '/password', '/forgot-password', '/reset-password', '/display', '/stm'];

// ⏰ Fonction qui détecte l'activité de l'utilisateur
// À chaque fois que l'utilisateur bouge la souris, clique, tape, ou fait défiler,
// on réinitialise le timer d'inactivité
function handleUserActivity() {
  // On réinitialise le timer seulement si l'utilisateur est connecté
  // et qu'on n'est pas sur une page publique
  if (authStore.isAuthenticated && !publicRoutes.includes(route.path)) {
    authStore.resetInactivityTimer();
  }
}

// Vérifier si l'utilisateur est connecté au démarrage de l'app
onMounted(async () => {
  console.log('🚀 App démarrée - Vérification de l\'authentification...');
  
  // Initialiser l'écoute des changements d'authentification
  authStore.initAuthListener();
  
  // Vérifier s'il y a un utilisateur connecté
  const user = await authStore.checkUser();
  
  // Si personne n'est connecté ET qu'on n'est pas sur une route publique
  if (!user && !publicRoutes.includes(route.path)) {
    console.log('❌ Pas d\'utilisateur connecté - Redirection vers /login');
    router.push('/login');
  } else if (user) {
    console.log('✅ Utilisateur connecté:', user.email);
  }
  
  isAppReady.value = true;

  // ⏰ Ajouter les écouteurs d'événements pour détecter l'activité
  // Ces événements vont réinitialiser le timer à chaque fois que l'utilisateur fait quelque chose
  window.addEventListener('mousemove', handleUserActivity);
  window.addEventListener('mousedown', handleUserActivity);
  window.addEventListener('keypress', handleUserActivity);
  window.addEventListener('scroll', handleUserActivity);
  window.addEventListener('touchstart', handleUserActivity);
});

// ⏰ Nettoyer les écouteurs quand l'app se ferme
onUnmounted(() => {
  window.removeEventListener('mousemove', handleUserActivity);
  window.removeEventListener('mousedown', handleUserActivity);
  window.removeEventListener('keypress', handleUserActivity);
  window.removeEventListener('scroll', handleUserActivity);
  window.removeEventListener('touchstart', handleUserActivity);
  
  // Arrêter le timer d'inactivité
  authStore.clearInactivityTimer();
});

watch(() => route.path, (newPath) => {
  isRouteReady.value = false;
  setTimeout(() => {
    isRouteReady.value = true;
  }, 50);

  // ⏰ Gestion du timer selon la route
  // Si on va sur une route publique, on arrête le timer
  if (publicRoutes.includes(newPath)) {
    authStore.clearInactivityTimer();
  } 
  // Si on va sur une route protégée et qu'on est connecté, on démarre le timer
  else if (authStore.isAuthenticated) {
    authStore.startInactivityTimer();
  }
}, { immediate: true });

watch(() => authStore.user, (newUser) => {
  if (!newUser && !publicRoutes.includes(route.path)) {
    console.log('👋 Utilisateur déconnecté - Redirection vers /login');
    router.push('/login');
  }
});
</script>

<template>
  <div v-if="!shouldShowContent" class="fixed inset-0 w-screen h-screen bg-black flex items-center justify-center z-50">
    <div class="text-white">
      <div class="animate-spin h-8 w-8 border-4 border-white border-t-transparent rounded-full"></div>
    </div>
  </div>

  <transition name="app-fade" mode="out-in">
    <div v-if="shouldShowContent && isDisplayPage" class="fixed inset-0 w-screen h-screen bg-black">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </div>

    <div v-else-if="shouldShowContent" id="app" class="flex min-h-screen bg-[#F0F0F0]">
      <Sidebar 
        v-if="$route.path !== '/Editor' && 
              $route.path !== '/login' && 
              $route.path !== '/password'&& 
              $route.path !== '/forgot-password'&& 
              $route.path !== '/reset-password'"
      />

      <div class="flex-1 overflow-auto bg-[#F0F0F0]">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
  </transition>
</template>

<style scoped>
.app-fade-enter-active,
.app-fade-leave-active {
  transition: opacity 0.3s ease;
}

.app-fade-enter-from,
.app-fade-leave-to {
  opacity: 0;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease;
}

.page-fade-enter-from,
.page-fade-leave-to {
  opacity: 0;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>