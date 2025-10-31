<script setup>
import { onMounted, watch, computed } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from './stores/authStore';
import Sidebar from "./components/SideBar.vue";
import './style.css';


const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

// Computed pour savoir si on est sur une page "display"
const isDisplayPage = computed(() => {
  return route.path === '/display' || route.path === '/stm';
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
});


watch(() => authStore.user, (newUser) => {
  if (!newUser && route.path !== '/login' && route.path !== '/password') {
    console.log('👋 Utilisateur déconnecté - Redirection vers /login');
    router.push('/login');
  }
});
</script>

<template>
  <!-- Pour les pages display/stm: affichage en plein écran sans le layout du dashboard -->
  <div v-if="isDisplayPage" class="fixed inset-0 w-screen h-screen bg-black">
    <router-view />
  </div>

  <!-- Pour toutes les autres pages: layout normal avec sidebar -->
  <div v-else id="app" class="flex min-h-screen bg-[#F0F0F0]">
    <Sidebar 
      v-if="$route.path !== '/Editor' && 
            $route.path !== '/login' && 
            $route.path !== '/password'&& 
            $route.path !== '/forgot-password'&& 
            $route.path !== '/reset-password'"
    />

    <div class="flex-1 overflow-auto bg-[#F0F0F0]">
      <router-view />
    </div>
  </div>
</template>

<style>
</style>