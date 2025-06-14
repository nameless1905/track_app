import json
from random import randint
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio



class WSConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()  # await обязательно!

        try:
            for i in range(1000):
                await self.send(json.dumps({"message": randint(1, 100)}))
                await asyncio.sleep(1)  # Неблокирующая задержка
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            await self.close()  # Закрываем соединение при ошибк