from flask import Blueprint

bp = Blueprint("ping", __name__)

@bp.route("/")
def main():
    return "pong"