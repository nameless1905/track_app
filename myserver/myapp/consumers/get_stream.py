import base64
import json
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
import cv2
from ultralytics import YOLO
import supervision as sv
from collections import defaultdict, deque


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
        image_points = np.array([self.point1, self.point2, self.point3, self.point4])

        REAL_W= self.width
        REAL_H = self.height

        real_points = np.array(
            [
                [0, 0],
                [ REAL_W - 1, 0],
                [ REAL_W - 1,REAL_H - 1],
                [0, REAL_H - 1],
            ]
        )
        original_video = f'media/videos/{self.videoFileName}'
        
        
     


        class CoordTransform:
            def __init__(self, original: np.ndarray, final: np.ndarray) -> None:
                original = original.astype(np.float32)
                final = final.astype(np.float32)
                self.matrix = cv2.getPerspectiveTransform(original,final)

            def transformation(self, points: np.ndarray) -> np.ndarray:
                if points.size == 0:
                    return points

                
                new_points = cv2.perspectiveTransform(points.reshape(-1, 1, 2).astype(np.float32), self.matrix)
                return new_points.reshape(-1, 2)

        video_info = sv.VideoInfo.from_video_path(video_path = original_video)
        model = YOLO("yolov8x.pt")
        
   
        conf = 0.3  
      

        tracker = sv.ByteTrack(
            frame_rate=video_info.fps ,
            track_activation_threshold=conf
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

        generator = sv.get_video_frames_generator(source_path=original_video)

        zone = sv.PolygonZone(polygon=image_points)
        transform = CoordTransform(original=image_points, final=real_points)

        history = defaultdict(lambda: deque(maxlen=video_info.fps))


        
        for frame in generator:
            if not self.stream_active:
                break
            result = model(frame)[0]
            detections = sv.Detections.from_ultralytics(result)
            
            vehicle_mask = np.isin(detections.class_id, np.array([2, 3, 5, 7]))
    
            detections = detections[vehicle_mask]
            detections = detections[detections.confidence > conf]
            detections = detections[zone.trigger(detections)]
            detections = detections.with_nms(threshold=0.7)
            detections =  tracker.update_with_detections(detections=detections)

            coordinats = detections.get_anchors_coordinates(
                anchor=sv.Position.BOTTOM_CENTER
            )
            coordinats = transform.transformation(points=coordinats).astype(int)

            for id, [_, y] in zip(detections.tracker_id,coordinats):
                history[id].append(y)

            labels = []
            for id in detections.tracker_id:
                if len(history[id]) < video_info.fps / 2:
                    labels.append(f"#{id}")
                else:
                  
                    S = abs(history[id][-1] - history[id][0])
                    time = len(history[id]) / video_info.fps
                    speed = S / time * 3.6
                    labels.append(f"#{id} {int(speed)} km/h")
            print(len(labels))
            print(labels)
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
            print(f"Отправка кадра. Размер base64: {len(base64_frame)}")  

            await self.send(json.dumps({
                "type": "video_frame",
                "frame": base64_frame
            }))
            await asyncio.sleep(1 / 30)

            
            cv2.imshow("frame", annotated_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        cv2.destroyAllWindows()
