from django.urls import re_path

from . import consumers # We'll create this file next
 
websocket_urlpatterns = [
    re_path(r'ws/live_stats/$', consumers.StatsConsumer.as_asgi()),
] 