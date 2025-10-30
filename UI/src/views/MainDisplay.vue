<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import BusRow from "../components/BusRow.vue";
import MetroRow from "../components/MetroRow.vue";
import STMLogo from "../assets/icons/STM.png";
import Background from "../assets/images/login_bg.jpg"

// Data from the API
const buses = ref([]);
const metroLines = ref([]);
const loading = ref(true);
const error = ref(null);

// Sort buses by arrival time
const sortedBuses = computed(() => {
  return [...buses.value].sort((a, b) => {
    const timeA = a.arrival_time;
    const timeB = b.arrival_time;
    
    if (typeof timeA === 'number' && typeof timeB === 'number') {
      return timeA - timeB;
    }
    
    if (typeof timeA === 'string' && typeof timeB === 'string') {
      return timeA.localeCompare(timeB);
    }

    if (typeof timeA === 'number') return -1;
    if (typeof timeB === 'number') return 1;
    
    return 0;
  });
});

// Function to fetch data from the backend
const fetchData = async () => {
  try {
    const response = await fetch("http://localhost:5000/api/data");
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    buses.value = data.buses || [];
    metroLines.value = data.metro_lines || [];
    
    loading.value = false;
    error.value = null;
  } catch (err) {
    console.error("Error fetching data:", err);
    error.value = "Unable to load transit data";
    loading.value = false;
  }
};

// Refresh interval (every 30 seconds)
let refreshInterval = null;

onMounted(() => {
  fetchData();
  refreshInterval = setInterval(fetchData, 30000);
});

onBeforeUnmount(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});
</script>

<template>
<div class="min-h-screen bg-cover bg-center relative overflow-hidden" :style="{ backgroundImage: `url(${Background})` }">
  <div class="absolute inset-0 bg-black/50 z-0"></div>
  
    <!-- Loading State -->
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center z-50">
      <div class="flex flex-col items-center space-y-12">
        <div class="w-12 h-12 border-4 border-white/20 border-t-white rounded-full animate-spin"></div>
        <p class="text-white/80 text-lg font-medium">Chargement des données de transport...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="absolute inset-0 flex items-center justify-center z-50">
      <div class="flex flex-col items-center gap-4 text-white">
        <p class="text-xl font-semibold">{{ error }}</p>
        <button @click="fetchData" class="px-6 py-3 bg-white text-indigo-900 rounded-lg font-semibold hover:bg-gray-100 transition">
          Réessayer
        </button>
      </div>
    </div>

    <!-- Main Content - Single View -->
    <div v-else class="relative z-20">
      <div class="relative min-h-screen flex items-center justify-center overflow-hidden">
        <div class="w-full flex flex-col items-center justify-center py-8">
          
          <!-- Bus Section -->
          <div class="flex flex-col w-full mb-6">
            
            <div v-if="sortedBuses.length === 0" class="flex items-center justify-center min-h-[200px]">
              <p class="text-white/60 text-xl">Aucun autobus à afficher</p>
            </div>

            <TransitionGroup 
              v-else
              name="bus-list" 
              tag="div" 
              class="flex flex-col"
              move-class="transition-all duration-600 ease-out"
              enter-active-class="transition-all duration-600 ease-out delay-100"
              leave-active-class="transition-all duration-600 ease-out absolute left-8 w-[calc(100%-4rem)]"
              enter-from-class="opacity-0 -translate-x-8"
              leave-to-class="opacity-0 translate-x-8"
            >
              <BusRow
                v-for="bus in sortedBuses"
                :key="bus.trip_id"
                :bus="bus"
              />
            </TransitionGroup>
          </div>

          <!-- Metro Section -->
          <div class="flex flex-col w-full mt-8">
            <div class="h-px bg-white/20 mx-8 mb-8"></div>
            
            <div v-if="metroLines.length === 0" class="flex items-center justify-center min-h-[200px]">
              <p class="text-white/60 text-xl">Aucune information sur le métro</p>
            </div>

            <TransitionGroup 
              v-else
              name="metro-list" 
              tag="div" 
              class="flex flex-col"
              move-class="transition-all duration-600 ease-out"
              enter-active-class="transition-all duration-600 ease-out delay-100"
              leave-active-class="transition-all duration-600 ease-out absolute left-8 w-[calc(100%-4rem)]"
              enter-from-class="opacity-0 -translate-x-8"
              leave-to-class="opacity-0 translate-x-8"
            >
              <MetroRow
                v-for="line in metroLines"
                :key="line.name"
                :line="line"
              />
            </TransitionGroup>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Bus list transitions */
.bus-list-move,
.bus-list-enter-active,
.bus-list-leave-active {
  transition: all 0.6s ease-out;
}

.bus-list-enter-from {
  opacity: 0;
  transform: translateX(-2rem);
}

.bus-list-leave-to {
  opacity: 0;
  transform: translateX(2rem);
}

.bus-list-leave-active {
  position: absolute;
  left: 2rem;
  width: calc(100% - 4rem);
}

/* Metro list transitions */
.metro-list-move,
.metro-list-enter-active,
.metro-list-leave-active {
  transition: all 0.6s ease-out;
}

.metro-list-enter-from {
  opacity: 0;
  transform: translateX(-2rem);
}

.metro-list-leave-to {
  opacity: 0;
  transform: translateX(2rem);
}

.metro-list-leave-active {
  position: absolute;
  left: 2rem;
  width: calc(100% - 4rem);
}
</style>