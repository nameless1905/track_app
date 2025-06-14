import base64
import json
import numpy as np
from io import BytesIO
from PIL import Image
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio

from random import randint
from time import sleep

from collections import defaultdict, deque

import cv2

from ultralytics import YOLO


import asyncio

from fastapi import FastAPI, WebSocket

import supervision as sv


class GetStreamConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream_active = False
        self.frame_rate = 10  # FPS по умолчанию
        self.point1 = [0,0]
        self.point2 = [0,0]
        self.point3 = [0,0]
        self.point4 = [0,0]

        self.width = 0
        self.height = 0

        self.videoFileName=""

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        self.stream_active = False

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        
        if data['type'] == 'start_stream':
            self.stream_active = True
            self.frame_rate = data.get('frame_rate', 10)
            print(type(data.get('point1')))
            self.point1 = [data.get('point1').get('x'),data.get('point1').get('y')]
            print(self.point1)
            
            self.point2 = [data.get('point2').get('x'),data.get('point2').get('y')]
            print(self.point2)
            
            self.point3 = [data.get('point3').get('x'),data.get('point3').get('y')]
            print(self.point3)
            
            self.point4 = [data.get('point4').get('x'),data.get('point4').get('y')]
            print(self.point4)


            self.width = data.get('size').get('width')
            self.height = data.get('size').get('height')
            print(self.width,self.height)
            self.videoFileName = data.get('videoFileName')
            print(self.point4)
            asyncio.create_task(self.generate_and_send_frames())
        
        elif data['type'] == 'stop_stream':
            self.stream_active = False

    async def generate_and_send_frames(self):
        SOURCE = np.array([self.point1, self.point2, self.point3, self.point4])

        TARGET_WIDTH = self.width
        TARGET_HEIGHT = self.height

        TARGET = np.array(
            [
                [0, 0],
                [TARGET_WIDTH - 1, 0],
                [TARGET_WIDTH - 1, TARGET_HEIGHT - 1],
                [0, TARGET_HEIGHT - 1],
            ]
        )
        source_video_path = f'/home/nameless/Documents/trak_app/myserver/media/videos/{self.videoFileName}'
        target_video_path = 'new_tr.mp4'
        confidence_threshold=0.3,
        iou_threshold=0.7



        class ViewTransformer:
            def __init__(self, source: np.ndarray, target: np.ndarray) -> None:
                source = source.astype(np.float32)
                target = target.astype(np.float32)
                self.m = cv2.getPerspectiveTransform(source, target)

            def transform_points(self, points: np.ndarray) -> np.ndarray:
                if points.size == 0:
                    return points

                reshaped_points = points.reshape(-1, 1, 2).astype(np.float32)
                transformed_points = cv2.perspectiveTransform(reshaped_points, self.m)
                return transformed_points.reshape(-1, 2)

        video_info = sv.VideoInfo.from_video_path(video_path=source_video_path)
        model = YOLO("yolov8x.pt")

        # Убедитесь, что confidence_threshold и video_info.fps — это числа
        confidence_threshold = 0.3  # Пример значения
        frame_rate = video_info.fps  # Должно быть числом, например, 30.0

        byte_track = sv.ByteTrack(
            frame_rate=frame_rate,
            track_activation_threshold=confidence_threshold
        )

        thickness = sv.calculate_optimal_line_thickness(
            resolution_wh=video_info.resolution_wh
        )
        text_scale = sv.calculate_optimal_text_scale(resolution_wh=video_info.resolution_wh)
        box_annotator = sv.BoxAnnotator(thickness=thickness)
        label_annotator = sv.LabelAnnotator(
            text_scale=text_scale,
            text_thickness=thickness,
            text_position=sv.Position.BOTTOM_CENTER,
        )
        trace_annotator = sv.TraceAnnotator(
            thickness=thickness,
            trace_length=video_info.fps * 2,
            position=sv.Position.BOTTOM_CENTER,
        )

        frame_generator = sv.get_video_frames_generator(source_path=source_video_path)

        polygon_zone = sv.PolygonZone(polygon=SOURCE)
        view_transformer = ViewTransformer(source=SOURCE, target=TARGET)

        coordinates = defaultdict(lambda: deque(maxlen=video_info.fps))


        with sv.VideoSink(target_video_path, video_info) as sink:
                for frame in frame_generator:
                    if not self.stream_active:
                        break
                    result = model(frame)[0]
                    detections = sv.Detections.from_ultralytics(result)
                    detections = detections[detections.confidence > confidence_threshold]
                    detections = detections[polygon_zone.trigger(detections)]
                    detections = detections.with_nms(threshold=iou_threshold)
                    detections = byte_track.update_with_detections(detections=detections)

                    points = detections.get_anchors_coordinates(
                        anchor=sv.Position.BOTTOM_CENTER
                    )
                    points = view_transformer.transform_points(points=points).astype(int)

                    for tracker_id, [_, y] in zip(detections.tracker_id, points):
                        coordinates[tracker_id].append(y)

                    labels = []
                    for tracker_id in detections.tracker_id:
                        if len(coordinates[tracker_id]) < video_info.fps / 2:
                            labels.append(f"#{tracker_id}")
                        else:
                            coordinate_start = coordinates[tracker_id][-1]
                            coordinate_end = coordinates[tracker_id][0]#
                            distance = abs(coordinate_start - coordinate_end)
                            time = len(coordinates[tracker_id]) / video_info.fps
                            speed = distance / time * 3.6
                            labels.append(f"#{tracker_id} {int(speed)} km/h")

                    annotated_frame = frame.copy()
                    annotated_frame = trace_annotator.annotate(
                        scene=annotated_frame, detections=detections
                    )
                    annotated_frame = box_annotator.annotate(
                        scene=annotated_frame, detections=detections
                    )
                    annotated_frame = label_annotator.annotate(
                        scene=annotated_frame, detections=detections, labels=labels
                    )

                    _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    base64_frame = base64.b64encode(buffer).decode('utf-8')
                    print(f"Отправка кадра. Размер base64: {len(base64_frame)}")  # 🚨 Должно быть > 0
        
                    await self.send(json.dumps({
                        "type": "video_frame",
                        "frame": base64_frame
                    }))
                    await asyncio.sleep(1 / 30)

                    sink.write_frame(annotated_frame)
                    cv2.imshow("frame", annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                cv2.destroyAllWindows()

    

        
            
   
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