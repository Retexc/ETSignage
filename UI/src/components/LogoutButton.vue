<template>
  <div class="flex flex-col gap-3 p-4 border-t border-gray-200">
    <!-- email de l'utilisateur -->
    <div
      v-if="authStore.isAuthenticated"
      class="p-2 px-8 bg-gray-100 rounded-lg"
    >
      <p class="text-sm text-gray-700 font-medium truncate">
        {{ authStore.userEmail }}
      </p>
    </div>

    <!-- Bouton de déconnexion -->
    <button
      @click="handleLogout"
      :disabled="loading"
      class="flex items-center justify-center gap-2 px-4 py-2.5 bg-red-500 hover:bg-red-600 active:bg-red-700 text-white font-semibold rounded-lg transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed hover:shadow-md active:scale-95"
      title="Se déconnecter"
    >
      <svg
        class="w-5 h-5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
        />
      </svg>

      <span v-if="!loading">Déconnexion</span>
      <span v-else>Déconnexion...</span>
    </button>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/authStore";

// Initialisation
const router = useRouter();
const authStore = useAuthStore();
const loading = ref(false);

// déconnexion
async function handleLogout() {


  loading.value = true;

  try {
    // Appeler la fonction de déconnexion du store
    const result = await authStore.signOut();

    if (result.success) {
      console.log("👋 Déconnexion réussie");
      // Rediriger vers la page de login
      router.push("/login");
    } else {
      console.error("❌ Erreur de déconnexion");
      alert("Erreur lors de la déconnexion");
    }
  } catch (err) {
    console.error("Erreur inattendue:", err);
    alert("Erreur lors de la déconnexion");
  } finally {
    loading.value = false;
  }
}
</script>
