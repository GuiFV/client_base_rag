from mangum import Mangum
from flask_asgi import asgi_app

handler = Mangum(asgi_app, lifespan="off")
