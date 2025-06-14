import base64
import json
import numpy as np
from io import BytesIO
from PIL import Image
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio


class VideoStreamConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream_active = False
        self.frame_rate = 10  # FPS по умолчанию

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        self.stream_active = False

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        
        if data['type'] == 'start_stream':
            self.stream_active = True
            self.frame_rate = data.get('frame_rate', 10)
            asyncio.create_task(self.generate_and_send_frames())
        
        elif data['type'] == 'stop_stream':
            self.stream_active = False

    async def generate_and_send_frames(self):
        while self.stream_active:
            # Генерация случайного изображения
            frame = self.generate_random_frame()
            
            # Отправка кадра
            await self.send_frame(frame)
            
            # Задержка для контроля FPS
            await asyncio.sleep(1 / self.frame_rate)

    def generate_random_frame(self, width=640, height=480):
        """Генерирует случайное RGB изображение"""
        random_array = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        img = Image.fromarray(random_array, 'RGB')
        
        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return buffer.getvalue()

    async def send_frame(self, frame_bytes):
        """Отправляет кадр в формате base64"""
        frame_base64 = base64.b64encode(frame_bytes).decode('utf-8')
        await self.send(text_data=json.dumps({
            'type': 'video_frame',
            'frame': frame_base64
        }))
