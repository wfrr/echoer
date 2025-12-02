import logging

from flask import Flask, jsonify, redirect

from echoer.config import Config

from . import routes


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.url_map.strict_slashes = False
    app.config.from_object(Config)

    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
    app.logger.addHandler(handler)
    app.logger.setLevel(Config.LOG_LEVEL)

    app.register_blueprint(routes.bp)

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"error": "Method Not Allowed"}), 405

    @app.route("/")
    def index():
        return redirect("/echo")

    return app
