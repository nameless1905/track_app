from django.urls import path

from myapp.consumers import GetStreamConsumer, VideoStreamConsumer, WSConsumer, GetStreamCrossroud



websocket_urlpatterns = [
    path('ws/video_stream/', VideoStreamConsumer.as_asgi()),
    path('ws/some-url/', WSConsumer.as_asgi()),
    path('ws/get_stream/', GetStreamConsumer.as_asgi()),
     path('ws/get_stream_crossroud/', GetStreamCrossroud.as_asgi()),
]