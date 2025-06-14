<template>
    <div class="bg-blue-500 pt-10 pb-10">
    <div class="w-3/5 bg-white pt-10 pb-10 m-auto rounded-xl shadow-xl shadow-gray-200 mt-20">
    <div class="video-container ">
      
      <canvas ref="videoCanvas" width="1000" height="750"></canvas>
      <div class="controls text-white">
        <button  class="py-2 border border-slate-300 rounded-md hover:border-slate-600 cursor-pointer bg-blue-500"  @click="startStream">Начать трансляцию </button>
        <button class="py-2 border border-slate-300 rounded-md hover:border-slate-600 cursor-pointer bg-blue-500" @click="stopStream">Остановить трансляцию</button>
       
      </div>
    </div>
    </div>
  </div>
  </template>
  
  <script setup>
 
  import { ref, onBeforeUnmount } from 'vue'


  const props = defineProps({
    points: Object,
    
    videoFileName: String,
  })
  
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
  if (socket.value) socket.value.close();

  console.log("Инициализация canvas..."); // 🚨
  ctx.value = videoCanvas.value.getContext('2d');

  console.log("Подключение к WebSocket..."); // 🚨
  socket.value = new WebSocket('/ws/get_stream_crossroud/');

  socket.value.onopen = () => {
    console.log('✅ WebSocket connected'); // 🚨 Должно появиться при успешном подключении
    
    socket.value.send(JSON.stringify({
      type: 'start_stream',
      videoFileName:props.videoFileName,
      points:props.points,
      
    }));
  };

  socket.value.onmessage = (event) => {
    console.log('Получены данные:', event.data); // 🚨 Должно появляться при получении кадра
    try {
      const data = JSON.parse(event.data);
      if (data.type === 'video_frame') {
        drawFrame(data.frame);
      }
    } catch (e) {
      console.error('Ошибка парсинга:', e);
    }
  };

  socket.value.onerror = (error) => {
    console.error('❌ WebSocket error:', error); // 🚨 При ошибках подключения
  };

  socket.value.onclose = () => {
    console.log('WebSocket disconnected'); // 🚨 При закрытии соединения
  };
};

  const stopStream = () => {
    if (socket.value) {
      socket.value.send(JSON.stringify({
        type: 'stop_stream'
      }))
    }
  }
  
  const drawFrame = (base64Frame) => {
        const img = new Image();
        
        img.onload = () => {
            ctx.value.clearRect(0, 0, videoCanvas.value.width, videoCanvas.value.height);
            ctx.value.drawImage(img, 0, 0, videoCanvas.value.width, videoCanvas.value.height);
        };
        
        img.onerror = () => {
            console.error("Ошибка загрузки изображения");
        };
        
        img.src = `data:image/jpeg;base64,${base64Frame}`;
    };
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