import json
from urllib.request import urlopen
from dotenv import find_dotenv, load_dotenv

from jose import JWTError
from os import environ as env
from flask import Flask, request, jsonify, _request_ctx_stack
from google.cloud import datastore
from authlib.integrations.flask_client import OAuth
from jose import jwt

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

    
def create_app():
    app = Flask(__name__)
    app.secret_key = env.get("APP_SECRET_KEY")

    CLIENT_ID = env.get("CLIENT_ID")
    CLIENT_SECRET = env.get("CLIENT_SECRET")
    DOMAIN = env.get("DOMAIN")

    oauth = OAuth(app)

    auth0 = oauth.register(
        'auth0',
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        api_base_url="https://" + DOMAIN,
        access_token_url="https://" + DOMAIN + "/oauth/token",
        authorize_url="https://" + DOMAIN + "/authorize",
        client_kwargs={
            'scope': 'openid profile email',
        },
    )

    register_blueprints(app)
    return app


def register_blueprints(app):
    from .routes import store
    from .routes import item
    from .routes import user

    app.register_blueprint(user.bp)
    app.register_blueprint(item.bp)
    app.register_blueprint(store.bp)