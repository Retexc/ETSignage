<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { supabase } from "../lib/supabaseClient";
import { motion } from "motion-v";
import bgImg from "../assets/images/Login_bg.jpg";

// 🎯 Initialisation
const router = useRouter();

// 📝 Variables du formulaire
const newPassword = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const error = ref(null);
const success = ref(false);
const validToken = ref(false);

// 🔍 Vérifier que le token est valide au chargement
onMounted(async () => {
  // Vérifier si on a un token de récupération dans l'URL
  const hashParams = new URLSearchParams(window.location.hash.substring(1));
  const accessToken = hashParams.get("access_token");
  const type = hashParams.get("type");

  if (type === "recovery" && accessToken) {
    validToken.value = true;
    console.log("✅ Token de récupération valide détecté");
  } else {
    error.value =
      "Lien invalide ou expiré. Veuillez demander un nouveau lien.";
    console.error("❌ Pas de token de récupération valide");
  }
});

// 🔄 FONCTION DE RÉINITIALISATION DU MOT DE PASSE
async function onSubmit() {
  // Réinitialiser les messages
  error.value = null;
  success.value = false;

  // ✅ Vérification : les mots de passe correspondent ?
  if (newPassword.value !== confirmPassword.value) {
    error.value = "Les mots de passe ne correspondent pas";
    return;
  }

  // ✅ Vérification : le mot de passe est assez long ?
  if (newPassword.value.length < 6) {
    error.value = "Le mot de passe doit contenir au moins 6 caractères";
    return;
  }

  loading.value = true;

  try {
    // Mettre à jour le mot de passe via Supabase
    const { error: updateError } = await supabase.auth.updateUser({
      password: newPassword.value,
    });

    if (updateError) {
      error.value =
        updateError.message || "Erreur lors de la réinitialisation";
      console.error("Erreur update:", updateError);
    } else {
      // ✅ Succès !
      success.value = true;
      console.log("✅ Mot de passe réinitialisé avec succès");

      // Réinitialiser le formulaire
      newPassword.value = "";
      confirmPassword.value = "";

      // Rediriger vers login après 3 secondes
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    }
  } catch (err) {
    console.error("Erreur inattendue:", err);
    error.value = "Une erreur est survenue. Réessayez.";
  } finally {
    loading.value = false;
  }
}

// 🔙 Retour à la page de connexion
function goToLogin() {
  router.push("/login");
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
          class="flex py-24 px-12 flex-col items-center justify-center space-y-6 w-full text-left"
        >
          <img
            src="../assets/icons/etsignage.svg"
            alt="ETS Signage Logo"
            class="w-56 self-start mt-2 mb-8 -ml-2 drop-shadow-2xl"
          />

          <h1 class="text-left self-start text-3xl font-bold text-[#E4022C]">
            Nouveau mot de passe
          </h1>

          <!-- 🚨 MESSAGE D'ERREUR -->
          <div
            v-if="error"
            class="w-full p-3 bg-red-100 border-2 border-red-500 text-red-700 rounded"
          >
            {{ error }}
          </div>

          <!-- ✅ MESSAGE DE SUCCÈS -->
          <div
            v-if="success"
            class="w-full p-4 bg-green-100 border-2 border-green-500 text-green-700 rounded"
          >
            <p class="font-semibold mb-2">✅ Mot de passe réinitialisé !</p>
            <p class="text-sm">
              Votre mot de passe a été changé avec succès.
            </p>
            <p class="text-sm mt-2">
              Redirection vers la page de connexion dans 3 secondes...
            </p>
          </div>

          <!-- Form -->
          <form
            v-if="validToken && !success"
            @submit.prevent="onSubmit"
            class="w-full flex flex-col items-left space-y-4 font-bold text-lg"
          >
            <span class="text-sm">Nouveau mot de passe</span>
            <input
              v-model="newPassword"
              type="password"
              placeholder="Nouveau mot de passe (min. 6 caractères)"
              required
              :disabled="loading"
              class="w-full p-3 bg-transparent border-2 border-[#535353] text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#E4022C] text-sm disabled:opacity-50"
            />

            <span class="text-sm">Confirmer le mot de passe</span>
            <input
              v-model="confirmPassword"
              type="password"
              placeholder="Confirmer le mot de passe"
              required
              :disabled="loading"
              class="w-full p-3 bg-transparent border-2 border-[#535353] text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#E4022C] text-sm disabled:opacity-50"
            />

            <button
              type="submit"
              :disabled="loading"
              class="w-full py-3 bg-[#E4022C] hover:bg-[#D5052C] text-white font-bold disabled:opacity-50 disabled:cursor-not-allowed transition-all mt-4"
            >
              {{ loading ? "Réinitialisation..." : "Réinitialiser" }}
            </button>
          </form>

          <!-- Bouton retour si token invalide ou après succès -->
          <button
            v-if="!validToken || success"
            @click="goToLogin"
            class="w-full py-3 bg-gray-500 hover:bg-gray-600 text-white font-bold transition-all"
          >
            Retour à la connexion
          </button>
        </motion.div>
      </div>
    </div>
  </div>
</template>
