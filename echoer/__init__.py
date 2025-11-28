import logging

from echoer.config import Config

from . import routes


# TODO: tests
# TODO: packaging
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    for handler in app.logger.handlers:
        app.logger.removeHandler(handler)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
    app.logger.addHandler(handler)
    app.logger.setLevel(Config.LOG_LEVEL)

    app.register_blueprint(routes.bp)

    return app
