from django.shortcuts import render

from django.http import JsonResponse 

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import os
from django.core.files.storage import default_storage

from myapp.speed_control import speed_contr

from django.http import HttpResponse
import cv2
import numpy as np
from django.views.decorators.csrf import csrf_exempt

@api_view(['POST'])
def upload_video(request):
    if 'video' not in request.FILES:
        return Response(
            {'error': 'Видеофайл не найден'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    video_file = request.FILES['video']
    title = request.POST.get('title', 'Без названия')
    
    # Проверка типа файла (опционально)
    allowed_extensions = ['.mp4', '.mov', '.avi']
    ext = os.path.splitext(video_file.name)[1].lower()
    if ext not in allowed_extensions:
        return Response(
            {'error': 'Недопустимый формат видео'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Сохранение файла
    file_path = default_storage.save(f'videos/{video_file.name}', video_file)
    
  
    
    return Response({
        'success': True,
        'file_path': file_path,
        'title': title,
        'size': video_file.size
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def get_video(request):
    speed_contr()
    return JsonResponse({"status":"success"})



@csrf_exempt
def first_frame(request):
    if request.method == 'GET':
        video_file_name = request.GET.get('videoFileName') 
        print(video_file_name)
        video_path = f'media/videos/{video_file_name}'
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return HttpResponse(status=500)
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            return HttpResponse(status=500)
        
        # Конвертируем кадр в JPEG с хорошим качеством
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return HttpResponse(buffer.tobytes(), content_type='image/jpeg')
    
    return HttpResponse(status=405)



