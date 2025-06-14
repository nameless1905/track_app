<template>
   <div class=" bg-blue-500  mx-auto">
    <div class="video-analyzer">
      <div class="controls-top flex justify-center items-center">
    <div class="text-xl text-white font-bold w-150 h-auto">
      <h1 >Постройте периметры зон входа и выхода на перекрестке.</h1>
      <h1 >Нажмите кнопку "Загрузить кадр" и сделайте разметку
          периметров зон сначала входа на перекресток потом выхода
          для каждого направления 
      </h1>
    </div>
    <video autoplay loop muted playsinline class="w-150 h-auto">
    <source src="/src/assets/crossroud_an.webm" type="video/webm">
    
    </video>
  </div>
      <div class="controls-top flex justify-center items-center">
        
        <button @click="loadFrame" class="btn-load" :disabled="loading">
          {{ loading ? 'Loading...' : 'Загрузить кадр' }}
        </button>
       
      </div>
  
      <div v-if="loading" class="loading">
        Loading frame...
      </div>
      <div v-show="imageLoaded" class="w-9/10 bg-white pt-10 pb-10 m-auto rounded-xl shadow-xl shadow-gray-200 mt-20">
      <div  class="canvas-wrapper">
        <h1 class="text-slate-700 text-2xl   px-20">{{message}}</h1>
        <canvas
          ref="canvas"
          @click="handleClick"
         
          class="analyzer-canvas"
        ></canvas>
        <button @click="clearCanvas" class="btn-clear" :disabled="!imageLoaded">
          Стереть точки
        </button>
        <div class="points-history">
          <h3>Выбранные точки: ({{ points.length }}):</h3>
          <ul v-if="points.length > 0">
            <li v-for="(point, index) in points" :key="index">
              {{ index + 1 }}. ({{ Math.round(point.x) }}, {{ Math.round(point.y) }})
            </li>
          </ul>
          <p v-else class="no-points">Нажмите на изоображение для добавления точки</p>
        </div>
        <button v-if="PointComplite" @click="sendData" class="btn-load" >
          Выбрать область
        </button>
      </div>
      </div>
     
    </div>
   </div>
  </template>
  
  <script setup>
  import { ref, onMounted, watchEffect } from 'vue'
  import axios from 'axios'
  
      const props = defineProps({
          videoFileName:String,
        })
      // Refs
      const canvas = ref(null)
      const loading = ref(false)
      const points = ref([])
      const image = ref(new Image())
      const imageLoaded = ref(false)
      const PointComplite = ref(false)
      const emit = defineEmits(['data-sent'])
      const message =ref('Постройте периметры в первом направлении')
      
      const ctx = ref(null)
  
      // Methods
      const loadFrame = async () => {
        try {
          console.log("Начало загрузки кадра...") // 🚨
          loading.value = true
          imageLoaded.value = false
          console.log(props.videoFileName)
          const response = await axios.get('/api/first-frame/', {
            responseType: 'blob',
            timeout: 5000 ,
            params: {  
              videoFileName: props.videoFileName,
            },
          })
          
          console.log("Получен ответ:", response) // 🚨
          
          const imageUrl = URL.createObjectURL(response.data)
          console.log("Создан URL изображения:", imageUrl) // 🚨
          
          image.value.onload = () => {
            console.log("Изображение загружено в DOM") // 🚨
            initCanvas()
            loading.value = false
            imageLoaded.value = true
          }
          
          image.value.onerror = (e) => {
            console.error("Ошибка загрузки изображения:", e) // 🚨
            loading.value = false
          }
          
          image.value.src = imageUrl
          
        } catch (error) {
          console.error("Ошибка при запросе:", error) // 🚨
          loading.value = false
        }
      }
  
      const initCanvas = () => {
          if (!canvas.value) {
            console.error("Canvas element not found!");
            return;
          }
  
          ctx.value = canvas.value.getContext('2d');
          if (!ctx.value) {
            console.error("Canvas context not available!");
            return;
          }
  
          // Проверка свойств изображения
          if (!image.value) {
            console.error("Image not loaded!");
            return;
          }
  
          console.log("Image natural size:", image.value.naturalWidth, image.value.naturalHeight);
          console.log("Image display size:", image.value.width, image.value.height);
  
          // Устанавливаем размеры canvas
          
          canvas.value.width = image.value.naturalWidth   || image.value.width;
          canvas.value.height = image.value.naturalHeight || image.value.height;
  
          console.log("Canvas size set to:", canvas.value.width, canvas.value.height);
          console.log("Image complete:", image.value.complete);
          console.log("Image src:", image.value.src);
  
          // Перерисовка без таймаута (если не нужно ждать)
          drawFrame();
        };
  
        const drawFrame = () => {
        if (!ctx.value || !canvas.value) return;
        
        // Полная очистка canvas
        ctx.value.clearRect(0, 0, canvas.value.width, canvas.value.height);
        
        // Проверка готовности изображения
        if (!image.value.complete) {
          console.warn("Изображение не готово!");
          return;
        }
        
        // Рисуем изображение
        ctx.value.drawImage(
          image.value, 
          0, 
          0, 
          image.value.width, 
          image.value.height,
          0,
          0,
          canvas.value.width,
          canvas.value.height
        );
        
        // Рисуем все точки и соединяем их линиями
        if (points.value.length > 0) {
          // Рисуем первую точку
          drawPoint(points.value[0]);
          
          // Рисуем линии и остальные точки
          for (let i = 1; i < points.value.length; i++) {
            drawPoint(points.value[i]);
            if((i+1) % 4 === 0){
                drawLine(points.value[i-1], points.value[i],i);
                console.log(1)
                drawLine(points.value[i-3], points.value[i],i);

                
            }
            else if(![5,9,13,17,21,25,29].includes(i+1)){
                
                drawLine(points.value[i-1], points.value[i],i);
            }
            
          }
        }
        if( points.value.length  === 32){
          
          PointComplite.value = true;
        }
        
        console.log("Canvas перерисован");
      }
  
      const handleClick = (event) => {
        if (!canvas.value  || !imageLoaded.value || points.value.length > 31) return;
        
        const rect = canvas.value.getBoundingClientRect();
        const scaleX = canvas.value.width / rect.width;
        const scaleY = canvas.value.height / rect.height;
        
        const x = Math.floor((event.clientX - rect.left) * scaleX);
        const y = Math.floor((event.clientY - rect.top) * scaleY);
            // Добавляем новую точку
        points.value.push({ x, y });
        
        // Перерисовываем canvas с новыми точками и линиями
        drawFrame();
      }
  
      const drawPoint = (point) => {
        if (!ctx.value) return;
        console.log('DrawPoint')
        ctx.value.beginPath();
        ctx.value.arc(point.x, point.y, 5, 0, Math.PI * 2);
        ctx.value.fillStyle = 'red';
        ctx.value.fill();
        
        // Добавляем текст с координатами
        ctx.value.fillStyle = 'black';
        ctx.value.font = '12px Arial';
        ctx.value.fillText(
          `${Math.round(point.x)}, ${Math.round(point.y)}`,
          point.x + 10,
          point.y - 5
        );
      }
  
      const drawLine = (start, end,index_point) => {
        if (!ctx.value) return;
        console.log('DrowLine')
        
        ctx.value.beginPath();
        ctx.value.moveTo(start.x, start.y);
        ctx.value.lineTo(end.x, end.y);
        switch(true){
            case index_point < 9:
                
                ctx.value.strokeStyle = 'red';
                break;
            case index_point< 17:
               
                ctx.value.strokeStyle = 'green';
                break;
            case index_point < 25:
                
                ctx.value.strokeStyle = 'yellow';
                break;
            case index_point < 33:
                
                ctx.value.strokeStyle = 'blue';
                break;

        }
       
        ctx.value.lineWidth = 2;
        ctx.value.stroke();
      }
      const clearCanvas = () => {
        points.value = []
        drawFrame()
      }
  
      const sendData = () => {
        emit('data-sent',{points:points.value})
      };
    
      watchEffect(() => {
        const length = points.value.length
          console.log(length)
          if (length < 8) {
            message.value = "Постройте периметры в первом направлении"
          } else if (length < 16) {
            message.value = "Постройте периметры во втором направлении"
          } else if (length < 24) {
            message.value = "Постройте периметры в третьем направлении"
          } else if (length < 32) {
            message.value = "Постройте периметры в четвертом направлении"
          } else {
            message.value = "Все периметры построены!" 
          }
        })
          
  </script>
  
  <style scoped>
  .video-analyzer {
    max-width: 1000px;
    margin: 0 auto;
    padding: 20px;
    font-family: Arial, sans-serif;
  }
  
  .controls-top {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
  }
  
  .btn-load, .btn-clear {
    padding: 8px 16px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
    transition: all 0.2s;
  }
  
  .btn-load {
  font-size: 18px;
  font-weight: bold;
  background: #4CAF50;
  color: white;
}

.btn-load:hover:not(:disabled) {
  font-size: 18px;
  font-weight: bold;
  background: #45a049;
}

.btn-load:disabled {
  font-size: 18px;
  font-weight: bold;
  background: #cccccc;
  cursor: not-allowed;
}

.btn-clear {
  font-size: 18px;
  font-weight: bold;
  background: #ff4444;
  color: white;
}

.btn-clear:hover:not(:disabled) {
  background: #cc0000;
}

.btn-clear:disabled {
  font-size: 18px;
  font-weight: bold;
  background: #f1f1f1;
  color: #aaa;
  cursor: not-allowed;
}
  .loading {
    padding: 20px;
    text-align: center;
    font-size: 1.1rem;
    color: #666;
  }
  
  .no-image {
    padding: 40px;
    text-align: center;
    font-size: 1.2rem;
    color: #888;
    border: 2px dashed #ddd;
    border-radius: 8px;
  }
  
  .canvas-wrapper {
    display: flex;
    flex-direction: column;
    gap: 20px;
    align-items: flex-start;
  }
  
  .analyzer-canvas {
    border: 2px solid #ddd;
    background: #f8f8f8;
    width: 100%; /* или фиксированная ширина */
    height: auto;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  .points-history {
    background: #f5f5f5;
    padding: 15px;
    border-radius: 4px;
    border: 1px solid #eee;
    width: 100%;
  }
  
  .points-history h3 {
    margin: 0 0 10px 0;
    font-size: 1rem;
    color: #333;
  }
  
  .points-history ul {
    list-style: none;
    padding: 0;
    margin: 0;
    max-height: 200px;
    overflow-y: auto;
  }
  
  .points-history li {
    padding: 5px 0;
    border-bottom: 1px solid #e0e0e0;
    font-family: monospace;
  }
  
  .points-history li:last-child {
    border-bottom: none;
  }
  
  .no-points {
    color: #888;
    margin: 0;
    font-style: italic;
  }
  </style>