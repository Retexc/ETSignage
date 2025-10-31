<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import { motion } from "motion-v";
import Preview from "../components/Preview.vue";
import playIcon from "../assets/icons/play.svg";
import stopIcon from "../assets/icons/stop-circle.svg";
import { useRouter } from "vue-router";
const running = ref(false);
let statusTimer = null;

async function updateStatus() {
  try {
    const resp = await fetch("/admin/status");
    const { running: isUp } = await resp.json();
    running.value = isUp;
  } catch (e) {
    console.error("Error fetching status:", e);
  }
}

const router = useRouter();

function goToExternal() {
  const displayUrl = `${window.location.protocol}//${window.location.host}/display`;
  console.log("Generated URL:", displayUrl);

  window.open(displayUrl, "_blank", "noopener");
}
async function toggleApp() {
  console.log("🔘 button clicked, running =", running.value);
  const url = running.value ? "/admin/stop" : "/admin/start";
  try {
    const resp = await fetch(url, { method: "POST" });
    console.log(await resp.json());
  } catch (e) {
    console.error("Error toggling app:", e);
  }
  updateStatus();
}

const btnLabel = computed(() => (running.value ? "Arrêter" : "Démarrer"));
const btnIcon = computed(() => (running.value ? stopIcon : playIcon));
const btnClass = computed(() =>
  running.value
    ? "bg-red-400 hover:bg-red-500 rounded-lg"
    : "bg-blue-400 hover:bg-blue-500 rounded-lg"
);
const statusText = computed(() =>
  running.value ? "État : Actif" : "État : Arrêté"
);
const statusTextColor = computed(() =>
  running.value ? "text-green-400" : "text-red-500"
);

onMounted(() => {
  updateStatus();
  statusTimer = setInterval(updateStatus, 2000);
});
onBeforeUnmount(() => {
  clearInterval(statusTimer);
});
</script>

<template>
  <div class="flex flex-col h-full overflow-hidden relative">
    <!-- ─── Animated Console Section ─── -->
    <motion.div
      :initial="{ opacity: 0, y: 20, filter: 'blur(10px)' }"
      :animate="{
        opacity: 1,
        y: 0,
        filter: 'blur(0px)',
        transition: { duration: 0.6 },
      }"
      class="flex-1"
    >
      <Preview />
    </motion.div>

    <!-- ─── Button on top of console-log (bottom right) ─── -->
    <button
      @click="goToExternal"
      class="flex flex-row items-center gap-1.5 px-4 btn btn-link bg-blue-400 font-black rounded-2xl p-2 absolute bottom-12 left-12 z-10 hover:bg-blue-500 transition-colors"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="16"
        height="16"
        fill="currentColor"
        class="bi bi-box-arrow-up-right"
        viewBox="0 0 16 16"
      >
        <path
          fill-rule="evenodd"
          d="M8.636 3.5a.5.5 0 0 0-.5-.5H1.5A1.5 1.5 0 0 0 0 4.5v10A1.5 1.5 0 0 0 1.5 16h10a1.5 1.5 0 0 0 1.5-1.5V7.864a.5.5 0 0 0-1 0V14.5a.5.5 0 0 1-.5.5h-10a.5.5 0 0 1-.5-.5v-10a.5.5 0 0 1 .5-.5h6.636a.5.5 0 0 0 .5-.5"
        />
        <path
          fill-rule="evenodd"
          d="M16 .5a.5.5 0 0 0-.5-.5h-5a.5.5 0 0 0 0 1h3.793L6.146 9.146a.5.5 0 1 0 .708.708L15 1.707V5.5a.5.5 0 0 0 1 0z"
        />
      </svg>
      Accéder au tableau
    </button>
  </div>
</template>

<style scoped>
/* ensure full‐height so motion has space */
:host {
  display: block;
  height: 100%;
}
</style>
