import os
from typing import Dict, Iterable, List, Optional, Set

import cv2
import numpy as np
import base64
from tqdm import tqdm

import supervision as sv

from ultralytics import YOLO

import asyncio

import json

from channels.generic.websocket import AsyncWebsocketConsumer

class GetStreamCrossroud(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream_active = False
        self.videoFileName=""
        self.points = []

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        self.stream_active = False

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        
        if data['type'] == 'start_stream':
            self.stream_active = True
            print(self.stream_active,data['type'] )
            self.videoFileName = data.get('videoFileName')
            self.points = data.get('points').get('points')
            print(type(self.points))
            print(self.points)
            for point in self.points:
                x = point['x']
                y = point['y']
                print(f"Координаты: x = {x}, y = {y}")
            print(self.videoFileName)
            asyncio.create_task(self.generate_and_send_frames())
        
        elif data['type'] == 'stop_stream':
            self.stream_active = False
        

    async def generate_and_send_frames(self):
        pastel_colors = [
            "#F4A4B4",  # Пастельно-красный 
            "#A1E8AF",  # Пастельно-зелёный 
            "#FFF2A1",  # Пастельно-жёлтый 
            "#A1C2F4"   # Пастельно-синий 
        ]
        COLORS_POLIGON = sv.ColorPalette.from_hex(pastel_colors)
        
        

        coords = [[point['x'], point['y']] for point in self.points]

        
        polygons = [coords[i:i+4] for i in range(0, len(coords), 4)]

        
        INPUT = [np.array(polygon) for polygon in polygons[:8:2]]  
        OUTPUT = [np.array(polygon) for polygon in polygons[1:8:2]]


        

        class AutoStreamAnalysis:
            def __init__(self) -> None:
                self.object_intput: Dict[int, int] = {}
                self.transition_between_zones: Dict[int, Dict[int, Set[int]]] = {}

            def update_stream(
                self,
                detections: sv.Detections,
                detections_input: List[sv.Detections],
                detections_output: List[sv.Detections],
            ) -> sv.Detections:
                for input_zone, tracker_input_zone in enumerate(detections_input):
                    for tracker_id in tracker_input_zone.tracker_id:
                        self.object_intput.setdefault(tracker_id, input_zone)

                for output_zone, tracker_output_zone in enumerate(detections_output):
                    for tracker_id in tracker_output_zone.tracker_id:
                        if tracker_id in self.object_intput:
                            input_zone = self.object_intput[tracker_id]
                            self.transition_between_zones.setdefault(output_zone, {})
                            self.transition_between_zones[output_zone].setdefault(input_zone, set())
                            self.transition_between_zones[output_zone][input_zone].add(tracker_id)
                if len(detections) > 0:
                    detections.class_id = np.vectorize(
                        lambda x: self.object_intput.get(x, -1)
                    )(detections.tracker_id)
                else:
                    detections.class_id = np.array([], dtype=int)
                return detections[detections.class_id != -1]


        def create_zone(
            polygons: List[np.ndarray],
            triggering_anchors: Iterable[sv.Position] = [sv.Position.CENTER],
        ) -> List[sv.PolygonZone]:
            return [
                sv.PolygonZone(
                    polygon=polygon,
                    triggering_anchors=triggering_anchors,
                )
                for polygon in polygons
            ]


        class DataProcessing:
            def __init__(
                self,
                consumer: AsyncWebsocketConsumer,
                original_video: str,
                
                conf: float = 0.3,
                
            ) -> None:
                self.consumer = consumer 
                self.conf = conf
                
                self.original_video = original_video
                

                self.model = YOLO("yolov8x.pt")
                self.tracker = sv.ByteTrack()

                self.video_info = sv.VideoInfo.from_video_path(original_video)
                self.input = create_zone(INPUT, [sv.Position.CENTER])
                self.output = create_zone(OUTPUT, [sv.Position.CENTER])

                self.box_annotator = sv.BoxAnnotator(color=COLORS_POLIGON)
                self.label_annotator = sv.LabelAnnotator(
                    color=COLORS_POLIGON, text_color=sv.Color.BLACK
                )
                self.trace_annotator = sv.TraceAnnotator(
                    color=COLORS_POLIGON, position=sv.Position.CENTER, trace_length=100, thickness=2
                )
                self.stream_analysis = AutoStreamAnalysis()

            async def processing(self):
                
                generator = sv.get_video_frames_generator(
                    source_path=self.original_video
                )

               
                for frame in tqdm(generator, total=self.video_info.total_frames):
                    if not self.consumer.stream_active:
                            break
                    annotated_frame = self.processing_one_frame(frame)
                    _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
                    base64_frame = base64.b64encode(buffer).decode('utf-8')
                    print(f"Отправка кадра. Размер base64: {len(base64_frame)}")  
            
                    await self.consumer.send(json.dumps({
                        "type": "video_frame",
                        "frame": base64_frame
                    }))
                    await asyncio.sleep(1 / 30)
                    cv2.imshow("Processing VideoFile", annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                cv2.destroyAllWindows()

            def annotate_one_frame(
                self, frame: np.ndarray, detections: sv.Detections
            ) -> np.ndarray:
                annotated_frame = frame.copy()
                #анотирование зон входа и выхода
                for i, (zone_input, zone_output) in enumerate(zip(self.input, self.output)):
                    annotated_frame = sv.draw_polygon(
                        annotated_frame, zone_input.polygon, COLORS_POLIGON.colors[i]
                    )
                    annotated_frame = sv.draw_polygon(
                        annotated_frame, zone_output.polygon, COLORS_POLIGON.colors[i]
                    )
                #список меток
                labels = [f"#{tracker_id}" for tracker_id in detections.tracker_id]
                annotated_frame = self.trace_annotator.annotate(annotated_frame, detections)
                
                annotated_frame = self.box_annotator.annotate(annotated_frame, detections)
                #добавление списка меток в анотатор
                annotated_frame = self.label_annotator.annotate(
                    annotated_frame, detections, labels
                )
                #рисуем количество машин въезжающих в зону 

                for id_zone, zone_output in enumerate(self.output):
                    poligon_center = sv.get_polygon_center(polygon=zone_output.polygon)
                    if id_zone in self.stream_analysis.transition_between_zones:
                        transition_between_zones = self.stream_analysis.transition_between_zones[id_zone]
                        for i, input_zone in enumerate(transition_between_zones):
                            count = len(self.stream_analysis.transition_between_zones[id_zone][input_zone])
                            text_anchor = sv.Point(x=poligon_center.x, y=poligon_center.y + 40 * i)
                            annotated_frame = sv.draw_text(
                                scene=annotated_frame,
                                text=str(count),
                                text_anchor=text_anchor,
                                background_color=COLORS_POLIGON.colors[input_zone],
                            )

                return annotated_frame

            def processing_one_frame(self, frame: np.ndarray) -> np.ndarray:
                results = self.model(
                    frame,verbose=False, conf=self.conf, iou=0.7
                )[0]
                detections = sv.Detections.from_ultralytics(results)
                vehicle_mask = np.isin(detections.class_id, np.array([2, 3, 5, 7]))
                detections = detections[vehicle_mask]
                detections.class_id = np.zeros(len(detections))
                #добавление идентификатока трекера
                detections = self.tracker.update_with_detections(detections)

                detections_input = []
                detections_output = []

                for zone_input, zone_output in zip(self.input, self.output):
                    tracker_input_zone = detections[zone_input.trigger(detections=detections)]
                    detections_input.append(tracker_input_zone)
                    tracker_output_zone = detections[zone_output.trigger(detections=detections)]
                    detections_output.append(tracker_output_zone)

                detections = self.stream_analysis.update_stream(
                    detections, detections_input, detections_output
                )
                return self.annotate_one_frame(frame, detections)


        original_video=f'media/videos/{self.videoFileName}'
        
        
        start_video_analysis = DataProcessing(
                original_video=original_video,
                consumer=self,
                conf=0.3,
                
            )
        await start_video_analysis.processing()