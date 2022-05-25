# import json
# from urllib.request import urlopen

# from jose import JWTError
# import store, item, user
# from os import environ as env
# from flask import Flask, request, jsonify, _request_ctx_stack
# from google.cloud import datastore
# from authlib.integrations.flask_client import OAuth
# from jose import jwt
# def create_app():
#     app = Flask(__name__)
#     app.secret_key = env.get("APP_SECRET_KEY")

#     client = datastore.Client()


#     # Update the values of the following 3 variables
#     CLIENT_ID = env.get("CLIENT_ID")
#     CLIENT_SECRET = env.get("CLIENT_SECRET")
#     DOMAIN = env.get("DOMAIN")
#     ALGORITHMS = ["RS256"]

#     oauth = OAuth(app)

#     auth0 = oauth.register(
#         'auth0',
#         client_id=CLIENT_ID,
#         client_secret=CLIENT_SECRET,
#         api_base_url="https://" + DOMAIN,
#         access_token_url="https://" + DOMAIN + "/oauth/token",
#         authorize_url="https://" + DOMAIN + "/authorize",
#         client_kwargs={
#             'scope': 'openid profile email',
#         },
#     )
    
#     app.register_blueprint(user.bp)
#     app.register_blueprint(item.bp)
#     app.register_blueprint(store.bp)
#     return app

    