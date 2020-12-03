import os

from flask import Flask
from pony.flask import Pony
from flaskr.pony_db import get_news


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        PONY={
            'provider': 'sqlite',
            'filename': 'flaskr.sqlite',
            'create_db': True
        }

    )

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    Pony(app)

    @app.route("/hello")
    def hello():
        return 'Hello, World'

    from . import auth
    app.register_blueprint(auth.bp)

    from . import typer
    app.register_blueprint(typer.bp)
    app.add_url_rule('/', endpoint='index')

    from . import tournaments
    app.register_blueprint(tournaments.bp)

    from . import jumpers
    app.register_blueprint(jumpers.bp)

    from . import ranking
    app.register_blueprint(ranking.bp)

    @app.context_processor
    def inject_news_feed():
        news_feed = get_news()
        return news_feed

    return app
