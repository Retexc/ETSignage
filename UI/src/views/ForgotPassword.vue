<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { supabase } from "../lib/supabaseClient";
import { motion } from "motion-v";
import bgImg from "../assets/images/Login_bg.jpg";

// 🎯 Initialisation
const router = useRouter();

// 📝 Variables du formulaire
const email = ref("");
const loading = ref(false);
const error = ref(null);
const success = ref(false);
const emailSent = ref(false);

// 📧 FONCTION D'ENVOI D'EMAIL DE RÉINITIALISATION
async function onSubmit() {
  // Réinitialiser les messages
  error.value = null;
  success.value = false;
  loading.value = true;

  try {
    // Envoyer l'email de réinitialisation via Supabase
    const { error: resetError } = await supabase.auth.resetPasswordForEmail(
      email.value,
      {
        redirectTo: `${window.location.origin}/reset-password`,
      }
    );

    if (resetError) {
      error.value = resetError.message || "Erreur lors de l'envoi de l'email";
      console.error("Erreur réinitialisation:", resetError);
    } else {
      // ✅ Email envoyé !
      emailSent.value = true;
      success.value = true;
      console.log("✅ Email de réinitialisation envoyé");
    }
  } catch (err) {
    console.error("Erreur inattendue:", err);
    error.value = "Une erreur est survenue. Réessayez.";
  } finally {
    loading.value = false;
  }
}

// 🔙 Retour à la page de connexion
function goBack() {
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
            Mot de passe oublié ?
          </h1>

          <!-- MESSAGE SI PAS ENCORE ENVOYÉ -->
          <p v-if="!emailSent" class="text-sm text-gray-600 self-start">
            Entrez votre adresse email et nous vous enverrons un lien pour
            réinitialiser votre mot de passe.
          </p>

          <!-- 🚨 MESSAGE D'ERREUR -->
          <div
            v-if="error"
            class="w-full p-3 bg-red-100 border-2 border-red-500 text-red-700 rounded"
          >
            {{ error }}
          </div>

          <!-- ✅ MESSAGE DE SUCCÈS -->
          <div
            v-if="success && emailSent"
            class="w-full p-4 bg-green-100 border-2 border-green-500 text-green-700 rounded"
          >
            <p class="font-semibold mb-2">✅ Email envoyé !</p>
            <p class="text-sm">
              Un email de réinitialisation a été envoyé à
              <strong>{{ email }}</strong>
            </p>
            <p class="text-sm mt-2">
              Vérifiez votre boîte de réception et cliquez sur le lien pour
              réinitialiser votre mot de passe.
            </p>
          </div>

          <!-- Form -->
          <form
            v-if="!emailSent"
            @submit.prevent="onSubmit"
            class="w-full flex flex-col items-left space-y-4 font-bold text-lg"
          >
            <span class="text-sm">Adresse email</span>
            <input
              v-model="email"
              type="email"
              placeholder="votre.email@etsmtl.ca"
              required
              :disabled="loading"
              class="w-full p-3 bg-transparent border-2 border-[#535353] text-black placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-[#E4022C] text-sm disabled:opacity-50"
            />

            <div class="flex space-x-4 pt-4">
              <button
                type="button"
                @click="goBack"
                :disabled="loading"
                class="flex-1 py-3 bg-gray-500 hover:bg-gray-600 text-white font-bold disabled:opacity-50 transition-all"
              >
                Retour
              </button>

              <button
                type="submit"
                :disabled="loading"
                class="flex-1 py-3 bg-[#E4022C] hover:bg-[#D5052C] text-white font-bold disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {{ loading ? "Envoi..." : "Envoyer le lien" }}
              </button>
            </div>
          </form>

          <!-- Bouton retour après envoi -->
          <button
            v-if="emailSent"
            @click="goBack"
            class="w-full py-3 bg-gray-500 hover:bg-gray-600 text-white font-bold transition-all"
          >
            Retour à la connexion
          </button>
        </motion.div>
      </div>
    </div>
  </div>
</template>
