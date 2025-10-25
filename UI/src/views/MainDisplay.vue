<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import Loading from "./Loading.vue";
import Display from "./Display.vue";
import Announcement from "./Announcement.vue";
import EndDisplay from "./EndDisplay.vue";

const showLoading = ref(true);
const showEndDisplay = ref(false);
const isTransitioning = ref(false);

// Slide animation states
const yellowSlide = ref(-100);
const whiteSlide = ref(-120);
const overlayComplete = ref(false);

let displayTimer = null;

const displayTimeMinutes = ref(1);

const loadDisplayTime = () => {
  try {
    const saved = localStorage.getItem("titleCard-totalDisplayTime");
    if (saved) {
      displayTimeMinutes.value = JSON.parse(saved);
    }
  } catch (error) {
    console.error("Error loading display time:", error);
  }
};

const displayTimeMs = computed(() => displayTimeMinutes.value * 60 * 1000);

const defaultColors = {
  principalTextColor: "#FFFFFF",
  secondaryTextColor: "#6B7280",
  backgroundColor: "#000000",
  pillColor: "#FFFFFF",
  pillTextColor: "#000000",
};

const colorsFromStorage = computed(() => {
  try {
    const savedColors = localStorage.getItem("titleCard-colors");
    return savedColors ? JSON.parse(savedColors) : defaultColors;
  } catch (error) {
    console.error("Error loading colors from localStorage:", error);
    return defaultColors;
  }
});

const backgroundColor = computed(() => colorsFromStorage.value.backgroundColor);


const watchLocalStorage = () => {
  setInterval(() => {
    try {
      const saved = localStorage.getItem("titleCard-totalDisplayTime");
      if (saved) {
        const savedValue = JSON.parse(saved);
        if (savedValue !== displayTimeMinutes.value) {
          displayTimeMinutes.value = savedValue;
          console.log(
            `Display time updated to ${displayTimeMinutes.value} minutes`
          );

          if (
            !showLoading.value &&
            !showEndDisplay.value &&
            !isTransitioning.value
          ) {
            if (displayTimer) {
              clearTimeout(displayTimer);
              displayTimer = setTimeout(() => {
                startTransitionToEnd();
              }, displayTimeMs.value);
              console.log(
                `Display timer restarted for ${displayTimeMinutes.value} minutes`
              );
            }
          }
        }
      }
    } catch (error) {}
  }, 1000);
};

onMounted(() => {
  console.log("MainDisplay mounted");
  loadDisplayTime();
  watchLocalStorage();
});

onBeforeUnmount(() => {
  if (displayTimer) {
    clearTimeout(displayTimer);
  }
});
</script>

<template>
  <div class="app-container">
<announcement></announcement>

  </div>
</template>

<style scoped>
.app-container {
  position: relative;
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.transition-overlay {
  transition: opacity 0.8s ease-in-out;
}

.transition-overlay.fade-out {
  opacity: 0;
  pointer-events: none;
}
</style>
