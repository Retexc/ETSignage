
<template>
    <Header />
  <div class="video-container">
    <video
      ref="videoPlayer"
      class="w-full h-full object-cover"
      autoplay
      muted
      @ended="onVideoEnd"
      @error="onVideoError"
    >
      <source :src="ETSVids" type="video/mp4">
      Your browser does not support the video tag.
    </video>
  </div>
</template>

<script setup>
import ETSVids from "../assets/ETS.mp4";
import Header from "../components/Header.vue";
import { ref, onMounted } from 'vue'

const videoPlayer = ref(null)
const videoSrc = ref('/path/to/video.mp4')

const onVideoEnd = () => {
  console.log('Video finished playing')
  // Trigger next content or loop
}

const onVideoError = (error) => {
  console.error('Video error:', error)
}

onMounted(() => {
  // Can control video programmatically
  if (videoPlayer.value) {
    videoPlayer.value.volume = 0.5
  }
})
</script>

<style scoped>
.video-container {
  width: 100%;
  height: 100vh;
  background: black;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>