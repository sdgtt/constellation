from flask import Flask
from flask.helpers import get_root_path
from dash import Dash
import dash_bootstrap_components as dbc
from flask_cors import CORS


def create_app():
    server = Flask(__name__)
    CORS(server)

    register_dashapps(server)
    # register_extensions(server)
    register_blueprints(server)

    return server


def register_dashapps(server):
    from app.score_card.app import layout, register_callbacks

    # Meta tags for viewport responsiveness
    meta_viewport = {
        "name": "viewport",
        "content": "width=device-width, initial-scale=1, shrink-to-fit=no",
    }
    score_card = Dash(
        __name__,
        server=server,
        url_base_pathname="/constellation/scorecard/",
        assets_folder=get_root_path(__name__) + "/static",
        meta_tags=[meta_viewport],
        external_stylesheets=[dbc.themes.SANDSTONE],
    )

    with server.app_context():
        score_card.title = "Score Card"
        score_card.layout = layout
        register_callbacks(score_card)


def register_blueprints(server):
    from app.app import server_bp

    server.register_blueprint(server_bp, url_prefix="/constellation")
