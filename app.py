from flask import Flask
from controllers import trader, ping

def create_app():
    app = Flask(__name__)
    app.url_map.strict_slashes = False
    app.register_blueprint(ping.bp, url_prefix="/ping")
    app.register_blueprint(trader.bp, url_prefix="/webhook")
    return app

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        app.run(host="0.0.0.0", port=8080)