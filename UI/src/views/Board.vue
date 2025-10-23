<script setup>
import { ref, watch, onMounted, computed } from "vue";
import { motion } from "motion-v";
import ImageSelectorField from "../components/ImageSelectorField.vue";
import placeholderBg from '../assets/images/background.png';

const previewImage = ref('');
const recentImages = ref([]);
const slots = ref([]);
const elementScale = ref(1.0); // Changed from overlayOpacity to elementScale
const MAX_RECENTS = 4;
const defaultBackground = '../assets/images/background.png';

function onPreviewError(e) {
  e.target.src = defaultBackground;
}

function addToRecent(url) {
  if (!url) return;
  if (url.startsWith('blob:')) return;

  recentImages.value = recentImages.value.filter(i => i !== url);
  recentImages.value.unshift(url);
  if (recentImages.value.length > MAX_RECENTS) {
    recentImages.value.length = MAX_RECENTS;
  }
}

// Watch element scale changes and persist to localStorage
watch(elementScale, (newValue) => {
  try {
    localStorage.setItem('displayElementScale', JSON.stringify(newValue));
    updateServerScale(newValue);
  } catch (e) {
    console.warn('failed to save element scale', e);
  }
}, { immediate: false });

watch(
  recentImages,
  v => {
    try {
      localStorage.setItem('recentBgImages', JSON.stringify(v.slice(0, MAX_RECENTS)));
    } catch {}
  },
  { deep: true }
);

async function updateServerScale(scale) {
  try {
    const promises = [
      fetch('/admin/display/scale', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scale })
      }),
      fetch('http://127.0.0.1:5001/admin/display/scale', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scale })
      })
    ];
    
    await Promise.allSettled(promises);
  } catch (err) {
    console.error('Failed to update server scale', err);
  }
}

onMounted(async () => {
  try {
    const stored = localStorage.getItem('recentBgImages');
    if (stored) {
      recentImages.value = JSON.parse(stored).slice(0, MAX_RECENTS);
    }
  } catch (e) {
    console.warn('failed to load recentImages', e);
  }

  // Load saved element scale
  try {
    const storedScale = localStorage.getItem('displayElementScale');
    if (storedScale) {
      elementScale.value = JSON.parse(storedScale);
    }
  } catch (e) {
    console.warn('failed to load element scale', e);
  }

  try {
    const r = await fetch('/admin/backgrounds');
    if (r.ok) {
      const data = await r.json();
      slots.value = Array.isArray(data) ? data : [];
      if (slots.value[0] && slots.value[0].path) {
        previewImage.value = slots.value[0].path;
      }
    }
  } catch (e) {
    console.warn('failed to load slots', e);
  }
});

// Keep your existing file upload and selectRecent functions unchanged

function handleScaleChange(e) {
  elementScale.value = parseFloat(e.target.value);
}
</script>

<template>
  <motion.div
    class="flex max-h-screen bg-[#0f0f0f]"
    :initial="{ opacity: 0, y: 20, filter: 'blur(10px)' }"
    :animate="{
      opacity: 1,
      y: 0,
      filter: 'blur(0px)',
      transition: { duration: 0.5 },
    }"
  >
    <div class="flex-1 flex flex-col p-6 space-y-6 mt-18 ml-5 mr-5">
      <!-- Header -->
      <div class="flex items-center justify-between w-full">
        <div class="space-y-1 w-full">
          <h2 class="text-4xl font-bold text-white">Tableau</h2>
          <p class="text-xl text-white">Modifier les paramètres du tableau.</p>
          <hr class="border-t border-[#404040] mt-3" />
        </div>
      </div>

      <!-- Settings -->
      <div class="flex flex-col gap-4">
        <!-- Element Scale Control -->
        <div class="flex flex-col gap-2">
          <label class="text-white font-medium">Taille des éléments</label>
          <div class="flex items-center gap-4">
            <span class="text-white text-sm">50%</span>
            <input
              type="range"
              min="0.5"
              max="2.0"
              step="0.1"
              :value="elementScale"
              @input="handleScaleChange"
              class="flex-1 h-2 bg-gray-600 rounded-lg appearance-none cursor-pointer
                     [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5 
                     [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-blue-500 
                     [&::-webkit-slider-thumb]:cursor-pointer [&::-webkit-slider-thumb]:border-2 
                     [&::-webkit-slider-thumb]:border-blue-800"
            />
            <span class="text-white text-sm">200%</span>
            <div class="text-white text-sm font-medium min-w-[3rem]">
              {{ Math.round(elementScale * 100) }}%
            </div>
          </div>
          <p class="text-gray-400 text-sm">
            Ajustez la taille des éléments sur l'écran.
          </p>
        </div>

        <div class="flex flex-col">
          <h3 class="text-2xl font-bold text-white">Rafraîchissement automatique</h3>
          <p class="text-xl text-white">Après son temps d'affichage, le tableau se rafraîchira automatiquement.</p>            
        </div>
      </div>
    </div>
  </motion.div>
</template>