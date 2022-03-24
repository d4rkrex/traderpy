from flask import Flask
from traderpy.controllers import ping
from traderpy.controllers import trader

def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.register_blueprint(ping.bp, url_prefix="/ping")
    app.register_blueprint(trader.bp, url_prefix="/webhook")
    return app