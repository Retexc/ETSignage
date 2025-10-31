<script setup>
import { onMounted, watch, computed, ref } from 'vue';
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

// Vérifier si l'utilisateur est connecté au démarrage de l'app
onMounted(async () => {
  console.log('🚀 App démarrée - Vérification de l\'authentification...');
  
  authStore.initAuthListener();
  
  // Vérifier s'il y a un utilisateur connecté
  const user = await authStore.checkUser();
  
  // Si personne n'est connecté ET qu'on n'est pas déjà sur /login ou /password
  if (!user && route.path !== '/login' && route.path !== '/password') {
    console.log('❌ Pas d\'utilisateur connecté - Redirection vers /login');
    router.push('/login');
  } else if (user) {
    console.log('✅ Utilisateur connecté:', user.email);
  }
  
  isAppReady.value = true;
});

watch(() => route.path, () => {
  isRouteReady.value = false;
  setTimeout(() => {
    isRouteReady.value = true;
  }, 50);
}, { immediate: true });

watch(() => authStore.user, (newUser) => {
  if (!newUser && route.path !== '/login' && route.path !== '/password') {
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