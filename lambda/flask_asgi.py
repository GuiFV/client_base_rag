from asgiref.wsgi import WsgiToAsgi

# Your Flask app
from app import app

# Wrapper
asgi_app = WsgiToAsgi(app)
