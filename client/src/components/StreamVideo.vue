<template>
  <div class="video-container">
    <canvas ref="videoCanvas" width="640" height="480"></canvas>
    <div class="controls">
      <button  class="py-2 border border-slate-300 rounded-md hover:border-slate-600 cursor-pointer"  @click="startStream">Start Stream</button>
      <button class="py-2 border border-slate-300 rounded-md hover:border-slate-600 cursor-pointer" @click="stopStream">Stop Stream</button>
      <label>
        Frame Rate:
        <input type="number" v-model.number="frameRate" min="1" max="60">
      </label>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount } from 'vue'

const videoCanvas = ref(null)
const socket = ref(null)
const frameRate = ref(10)
const ctx = ref(null)

onBeforeUnmount(() => {
  if (socket.value) {
    socket.value.close()
  }
})

const startStream = () => {
  // Очищаем предыдущее соединение
  if (socket.value) {
    socket.value.close()
  }

  // Инициализация canvas
  ctx.value = videoCanvas.value.getContext('2d')

  // Подключение к WebSocket
  socket.value = new WebSocket('/ws/video_stream/')

  socket.value.onopen = () => {
    console.log('WebSocket connected')
    socket.value.send(JSON.stringify({
      type: 'start_stream',
      frame_rate: frameRate.value
    }))
  }

  socket.value.onmessage = (event) => {
    const data = JSON.parse(event.data)
    if (data.type === 'video_frame') {
      drawFrame(data.frame)
    }
  }

  socket.value.onclose = () => {
    console.log('WebSocket disconnected')
  }
}

const stopStream = () => {
  if (socket.value) {
    socket.value.send(JSON.stringify({
      type: 'stop_stream'
    }))
  }
}

const drawFrame = (base64Frame) => {
  const img = new Image()
  img.onload = () => {
    ctx.value.clearRect(0, 0, videoCanvas.value.width, videoCanvas.value.height)
    ctx.value.drawImage(img, 0, 0)
  }
  img.src = `data:image/jpeg;base64,${base64Frame}`
}
</script>

<style scoped>
.video-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

canvas {
  border: 1px solid #ccc;
  background-color: #f0f0f0;
}

.controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

button {
  padding: 8px 16px;
  cursor: pointer;
}
</style>