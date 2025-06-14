<template>
    <div class="flex justify-center px-8 py-8 items-center gap-5  mx-auto bg-blue-500">
      <input 
          class="py-2 border border-slate-300 rounded-md hover:border-slate-600 cursor-pointer  bg-white"
          type="file" 
          accept="video/*" 
          @change="handleFileChange" 
          ref="fileInput"
        />
        <button 
          class="py-2 border border-slate-300 rounded-md hover:border-slate-600 cursor-pointer bg-blue-500 text-white px-4 text-l font-bold"
          @click="uploadVideo" :disabled="!videoFile">
          {{ uploadButtonText }}
        </button>
        <div v-if="progress > 0 && progress < 100">
          Прогресс: {{ progress }}%
          <progress :value="progress" max="100"></progress>
        </div>
        <p v-if="message" class=" text-xl font-bold text-white absolute right-100 ">{{ message }}</p>
    </div>
</template>


<script setup>

import { ref } from 'vue';
import axios from 'axios';

const videoFileName = ref(null)
const videoFile = ref(null);
const progress = ref(0);
const message = ref('');
const isError = ref(false);
const uploadButtonText = ref('Загрузить видео');
const fileInput = ref(null);

const handleFileChange = (event) => {
  videoFile.value = event.target.files[0];
  message.value = '';
  videoFileName.value = videoFile.value.name
};

const showMessage = (text, error = false) => {
  message.value = text;
  isError.value = error;
};

const resetForm = () => {
  videoFile.value = null;
  progress.value = 0;
  fileInput.value.value = '';
};

const uploadVideo = async () => {
  if (!videoFile.value) {
    showMessage('Выберите видеофайл', true);
    return;
  }

  const formData = new FormData();
  formData.append('video', videoFile.value);
  formData.append('title', 'Мое видео');

  try {
    uploadButtonText.value = 'Загрузка...';
    const response = await axios.post(
      '/api/upload-video/', 
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
          
        },
        onUploadProgress: (progressEvent) => {
          progress.value = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
        }
      }
    );

    showMessage('Видео успешно загружено!');
    emit('upload-success', response.data);
    emit('file-name-sent', videoFileName.value)
    resetForm();
  } catch (error) {
    const errorMsg = error.response?.data?.error || 'Ошибка загрузки';
    showMessage(errorMsg, true);
    console.error('Ошибка:', error);
  } finally {
    uploadButtonText.value = 'Загрузить видео';
  }
};

const emit = defineEmits(['upload-success','file-name-sent']);

</script>