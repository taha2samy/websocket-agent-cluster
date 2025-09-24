from django.urls import path
from brocker.consumers import BrokerConsumer

websocket_urlpatterns = [
    path("ws/brocker/", BrokerConsumer.as_asgi()),
]
