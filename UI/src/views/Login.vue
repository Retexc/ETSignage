<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/authStore";
import { motion } from "motion-v";
import bgImg from "../assets/images/Login_bg.jpg";

// 🎯 Initialisation
const router = useRouter();
const authStore = useAuthStore();

// 📝 Variables du formulaire
const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref(null);

// 🔐 FONCTION DE CONNEXION
async function onSubmit() {
  // Réinitialiser l'erreur
  error.value = null;
  loading.value = true;

  try {
    // Appel au store pour se connecter
    const result = await authStore.signIn(email.value, password.value);

    if (result.success) {
      // ✅ Connexion réussie !
      console.log("✅ Connexion réussie, redirection...");
      
      // Rediriger vers la page d'accueil (ou où tu veux)
      router.push("/");
    } else {
      // ❌ Erreur de connexion
      console.error("❌ Erreur Supabase complète:", result.error);
      error.value = result.error || "Identifiants incorrects";
      
      // Traduire les erreurs courantes en français
      if (error.value.includes("Invalid login credentials")) {
        error.value = "Email ou mot de passe incorrect";
      } else if (error.value.includes("Email not confirmed")) {
        error.value = "ERREUR SUPABASE: " + error.value + " - Vérifiez dans Supabase → Users que l'email est confirmé";
      }
    }
  } catch (err) {
    console.error("Erreur inattendue:", err);
    error.value = "Une erreur est survenue. Réessayez.";
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* nothing here—everything is in utility classes */
</style>

<template>
  <div
    class="min-h-screen bg-center bg-cover bg-no-repeat"
    :style="{ backgroundImage: `url(${bgImg})` }"
  >
    <div class="flex items-center justify-start h-screen">
      <!-- WHITE CARD -->
      <div class="bg-[#ffffff] w-2/5 h-full p-8 overflow-hidden flex flex-col">
        <motion.div
          :initial="{ opacity: 0, y: 20, filter: 'blur(10px)' }"
          :animate="{
            opacity: 1,
            y: 0,
            filter: 'blur(0px)',
            transition: { duration: 1 },
          }"
        >
        </motion.div>

        <motion.div
          :initial="{ opacity: 0, y: 20, filter: 'blur(10px)' }"
          :animate="{
            opacity: 1,
            y: 0,
            filter: 'blur(0px)',
            transition: { delay: 0.5, duration: 1 },
          }"
          class="flex py-32 px-12 flex-col items-center justify-center space-y-6 w-full text-left"
        >
          <img
            src="../assets/icons/ETS.svg"
            alt="ETS Logo"
            class="w-18 self-start mt-2 mb-8 drop-shadow-2xl"
          />

          <img
            src="../assets/icons/signage.svg"
            alt="Signage Logo"
            class="w-40 self-start mt-2 drop-shadow-2xl"
          />

          <!-- 🚨 MESSAGE D'ERREUR -->
          <div
            v-if="error"
            class="w-full p-3 bg-red-100 border-2 border-red-500 text-red-700 rounded"
          >
            {{ error }}
          </div>

          <!-- Form -->
          <form
            @submit.prevent="onSubmit"
            class="w-full flex flex-col items-left space-y-6 font-bold text-xl"
          >
            <span>Email</span>
            <input
              v-model="email"
              type="email"
              placeholder="votre.email@etsmtl.ca"
              required
              :disabled="loading"
              class="w-full p-3 bg-transparent border-2 border-[#535353] text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#E4022C] text-sm disabled:opacity-50"
            />
            
            <span>Mot de passe</span>
            <input
              v-model="password"
              type="password"
              placeholder="Mot de passe"
              required
              :disabled="loading"
              class="w-full p-3 bg-transparent border-2 border-[#535353] text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#E4022C] text-sm disabled:opacity-50"
            />

            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3 bg-[#E4022C] hover:bg-[#D5052C] text-white font-bold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {{ loading ? "Connexion en cours..." : "Connexion" }}
            </button>

            <!-- Lien vers mot de passe oublié -->
            <router-link
              to="/forgot-password"
              class="text-sm text-[#E4022C] hover:underline self-center"
            >
              Mot de passe oublié ?
            </router-link>
          </form>
        </motion.div>
      </div>
    </div>
  </div>
</template>