from flask import Flask

from echoer.config import Config

from . import routes


# TODO: logging
# TODO: error handling
# TODO: tests
# TODO: packaging
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    app.register_blueprint(routes.bp)

    return app
