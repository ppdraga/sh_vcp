import os
from aiohttp import web
import aiohttp_jinja2
import jinja2

from settings import config, BASE_DIR
from routes import setup_routes


app = web.Application()
app['config'] = config
setup_routes(app)
aiohttp_jinja2.setup(app,
    loader=jinja2.FileSystemLoader(str(os.path.join(BASE_DIR, 'templates'))))
web.run_app(app, port=8088)
