
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from brocker.middleware import AuthMiddlewareBroker
from brocker.routing import websocket_urlpatterns

class MiddlewareDistributor:
    """
    ASGI middleware that routes WebSocket connections to different middleware
    based on the request path.
    
    Currently:
    - Uses AuthMiddlewareDevice for paths starting with '/ws/brocker/'
    - Closes the WebSocket connection for any other paths
    """
    def __init__(self, inner_app):
        self.inner_app = inner_app

    async def __call__(self, scope, receive, send):
        # Check if the WebSocket path matches /ws/brocker/
        print("Brocker path matched, checking path:", scope["path"])
        if scope["path"].startswith("/ws/brocker/"):
            
            # Pass the connection through AuthMiddlewareDevice
            inner_app = AuthMiddlewareBroker(self.inner_app)
        else:
            # Close the connection if the path does not match
            await send({
                "type": "websocket.close",
                "code": 4000,  # Custom close code
            })
            return

        # Call the selected inner application
        return await inner_app(scope, receive, send)


# Combine WebSocket patterns (from your routing)
websocket_patterns = websocket_urlpatterns  # only brocker for now

# ASGI application
application = ProtocolTypeRouter({
    # Handle traditional HTTP requests with Django
    "http": get_asgi_application(),
    
    # Handle WebSocket connections via our custom distributor
    "websocket": MiddlewareDistributor(
        URLRouter(websocket_patterns)
    ),
})
