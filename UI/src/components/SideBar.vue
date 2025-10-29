<script setup>
import { useRouter } from "vue-router";
import { onMounted, onUnmounted } from "vue";
import { useUpdateStore } from "../composables/useUpdateStore.js";
import LogoutButton from "./LogoutButton.vue";

const router = useRouter();
const { updateState, checkForUpdates, clearNotification } = useUpdateStore();

function logout() {
  // clear session/cookie, then:
  router.push("/login");
}

let updateCheckInterval = null;

onMounted(() => {
  // Check for updates immediately
  checkForUpdates();

  // Check for updates every 30 minutes (1800000ms)
  updateCheckInterval = setInterval(checkForUpdates, 1800000);
});

onUnmounted(() => {
  if (updateCheckInterval) {
    clearInterval(updateCheckInterval);
  }
});

// Clear update notification when user visits settings
function navigateToSettings() {
  clearNotification();
  router.push("/settings");
}
</script>

<template>
  <div class="flex min-h-screen">
    <div class="flex flex-col h-screen w-64 text-black bg-[#FFFFFF]">
      <!-- LOGO -->
      <div class="py-4 px-6">
        <a href="/">
          <img
            src="../assets/icons/etsignage.svg"
            alt="Bdeblogo"
            class="w-40 mb-2 mt-8 -ml-1"
          />
        </a>
      </div>

      <nav class="flex-1 overflow-y-auto">
        <div class="mb-10">
          <router-link
            to="/console"
            class="flex items-center font-bold px-6 py-2.5 gap-2 hover:text-red-600"
            active-class="text-red-400"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="28"
              height="28"
              fill="currentColor"
              class="bi bi-display"
              viewBox="0 0 16 16"
            >
              <path
                d="M0 4s0-2 2-2h12s2 0 2 2v6s0 2-2 2h-4q0 1 .25 1.5H11a.5.5 0 0 1 0 1H5a.5.5 0 0 1 0-1h.75Q6 13 6 12H2s-2 0-2-2zm1.398-.855a.76.76 0 0 0-.254.302A1.5 1.5 0 0 0 1 4.01V10c0 .325.078.502.145.602q.105.156.302.254a1.5 1.5 0 0 0 .538.143L2.01 11H14c.325 0 .502-.078.602-.145a.76.76 0 0 0 .254-.302 1.5 1.5 0 0 0 .143-.538L15 9.99V4c0-.325-.078-.502-.145-.602a.76.76 0 0 0-.302-.254A1.5 1.5 0 0 0 13.99 3H2c-.325 0-.502.078-.602.145"
              />
            </svg>

            Aperçu
          </router-link>
        </div>

        <div class="mb-10">
          <router-link
            to="/Editor"
            class="flex items-center font-bold px-6 py-2.5 gap-2 hover:text-red-600"
            active-class="text-red-400"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="28"
              height="28"
              fill="currentColor"
              class="bi bi-pencil-square"
              viewBox="0 0 16 16"
            >
              <path
                d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z"
              />
              <path
                fill-rule="evenodd"
                d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5z"
              />
            </svg>

            Éditeur d'annonces
          </router-link>
        </div>

        <div class="mb-10">
          <div class="relative">
            <router-link
              to="/settings"
              @click="navigateToSettings"
              class="flex items-center font-bold px-6 py-2.5 gap-2 hover:text-red-600"
              active-class="text-red-400"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="28"
                height="28"
                fill="currentColor"
                class="bi bi-gear"
                viewBox="0 0 16 16"
              >
                <path
                  d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492M5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0"
                />
                <path
                  d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115z"
                />
              </svg>

              Paramètres
            </router-link>

            <!-- Update notification pill -->
            <div
              v-if="updateState.available"
              class="absolute top-2 right-2 w-3 h-3 bg-blue-400 rounded-full animate-pulse border-2 border-[#0A0A0A]"
              title="Mise à jour disponible"
            ></div>
          </div>
        </div>
      </nav>
      <LogoutButton />
    </div>
  </div>
</template>
