<script setup>
import { RouterLink, RouterView } from 'vue-router'
import HelloWorld from './components/HelloWorld.vue'
import UploadVideo from './components/UploadVideo.vue'

import GetFirstFrame from './components/GetFirstFrame.vue'

import { ref , computed} from 'vue';
import axios from 'axios';

import StreamVideo from './components/StreamVideo.vue'
import GetStream from './components/GetStream.vue'
import GetStreamCrossroud from './components/GetStreamCrossroud.vue'

import GetFirstFrameCrossroud from './components/GetFirstFrameCrossroud.vue'

import MyFooter from './components/MyFooter.vue'
import MyHeader from './components/MyHeader.vue'

const mess = ref('');
const data = ref("")
const socket2 = ref(null)

const points = ref(null) 

const pointsCrossroud = ref(null) 
const size = ref(null)


const firstNumber = ref(null)
const secondNumber = ref(null)
const savedNumbers = ref(null)

const videoFileName = ref(null)

const changeTask = ref(0)

// Проверка валидности формы
const isFormValid = computed(() => {
  return firstNumber.value !== null && 
         secondNumber.value !== null &&
         Number.isInteger(firstNumber.value) && 
         Number.isInteger(secondNumber.value)
})

// Валидация ввода (только целые числа)
const validateNumber = (event) => {
  if (['e', 'E', '+', '-', '.'].includes(event.key)) {
    event.preventDefault()
  }
}

// Сохранение чисел и очистка полей
const saveNumbers = () => {
  if (isFormValid.value) {
    size.value = {
      height: firstNumber.value,
      width: secondNumber.value
    }
    
    // Очищаем поля
    firstNumber.value = null
    secondNumber.value = null
  }
}

socket2.value = new WebSocket('ws://127.0.0.1:8000/ws/some-url/')

socket2.value.onmessage = (event) =>{
  data.value = JSON.parse(event.data).message

}

const getVideo = async() => {
  await axios.post(
      'http://127.0.0.1:8000/api/get-video/'
      )
      .then(response=> console.log('Скрипт запущен',response.data))
      .catch(error => console.error('Ошибка:',error));
      
}

const handleData =  (data) =>{
  points.value = data
  console.log('Полученные данных',data)
}

const handleFileName =  (data) =>{
  videoFileName.value = data
  
}
const handleDataCrossroud =  (data) =>{
  pointsCrossroud.value = data
  console.log('Полученные данных',data)
}
</script>

<template>
  <my-header/>
  <div class=" bg-white   text-slate-500 ">
    <img 
  src="/src/assets/new_banner.png" 
  alt="баннер" 
  class="w-full h-auto max-h-150 block"
>
    <upload-video @file-name-sent='handleFileName'/>
    <div  v-if = "videoFileName" class="flex px-8 py-8  mx-auto bg-slate-700   justify-center items-center gap-5 margin: 0 auto;
    padding: 20px;" >
      <div class="grid gap-4 mx-auto">
        <img 
          src="/src/assets/speed_control.png" 
           
          class="w-150 h-auto rounded-lg"
        >
        <button @click="changeTask = 1" class="py-2 border border-slate-300 rounded-md hover:border-slate-600 cursor-pointer  bg-blue-500 text-white px-4 text-l font-bold">Расчет скорости</button>
      </div>
      <div class="grid gap-4  mx-auto">
        <img 
          src="/src/assets/traffic.png" 
           
          class="w-150 h-auto rounded-lg"
        >
        <button @click="changeTask = 2" class="py-2 border border-slate-300 rounded-md hover:border-slate-600 cursor-pointer  bg-blue-500 text-white px-4 text-l font-bold">Анализ потока на перекрестке </button>
      </div>
    </div>
    <div v-if="changeTask == 2" >
      <get-first-frame-crossroud  :videoFileName="videoFileName" @data-sent='handleDataCrossroud'/>
    
      <get-stream-crossroud v-if="pointsCrossroud" :points="pointsCrossroud" :videoFileName="videoFileName"/>
    </div>
    
    <div v-if="changeTask == 1">
      <get-first-frame  :videoFileName="videoFileName" @data-sent='handleData'/>


<div v-if = "points" class=" px-8 py-8 items-center justify-center  bg-slate-700 text-white gap-5 grid">
  <h1 class="px-50 text-xl">Введите реальные размеры периметра зоны</h1>
  <div class="flex px-8 py-8 items-center justify-center  gap-5 margin: 0 auto; padding: 20px;">
  
  <div >
    <label for="firstNumber">Введите длину:</label>
    <input
      class="py-2 border border-slate-300 rounded-md hover:border-slate-600 cursor-pointer bg-white text-slate-500"
      type="number"
      v-model.number="firstNumber"
      @keydown="validateNumber"
      
    />
  </div>
  
  <div >
    <label for="secondNumber">Введите ширину:</label>
    <input
      class="py-2 border border-slate-300 rounded-md hover:border-slate-600 cursor-pointer bg-white text-slate-500"
      type="number"
      v-model.number="secondNumber"
      @keydown="validateNumber"
      
    />
  </div>
  
  <button
    class="py-2 border border-slate-300 rounded-md hover:border-slate-600 cursor-pointer bg-blue-500"
    @click="saveNumbers"
    :disabled="!isFormValid"
    
  >
    Сохранить 
  </button>
  
  <div v-if="size" >
    <p>Сохранённые значения: {{ size.height}},{{ size.width }} </p>
  </div>
</div>
</div>

<get-stream v-if="size" :points="points" :size="size" :videoFileName="videoFileName"/>
    </div>
   

  </div>

  <my-footer/>
    
</template>

<style scoped>

</style>
