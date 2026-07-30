import logging

from flask import Flask, jsonify, redirect
from logstash_async.handler import AsynchronousLogstashHandler, LogstashFormatter

from echoer.config import Config

from . import routes


def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.url_map.strict_slashes = False
    app.config.from_object(Config)

    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)

    match Config.LOG_TARGET:
        case "STDOUT":
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
            )
        case "LOGSTASH":
            handler = AsynchronousLogstashHandler(
                host=Config.LOGSTASH_HOST,
                port=Config.LOGSTASH_PORT,
                transport="logstash_async.transport.BeatsTransport",
                database_path="",
                ssl_verify=False,
            )
            handler.setFormatter(LogstashFormatter())
        case _:
            raise AssertionError("Invalid LOG_TARGET")

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
