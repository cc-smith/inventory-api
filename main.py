from google.cloud import datastore
from flask import Flask, request, jsonify, _request_ctx_stack
import requests
import store, item, user
from functools import wraps
import json

from urllib.request import urlopen
from flask_cors import cross_origin
from jose import jwt

import os
from os import environ as env
from werkzeug.exceptions import HTTPException

from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for
from authlib.integrations.flask_client import OAuth
from urllib.parse import urlencode


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")
app.register_blueprint(user.bp)
app.register_blueprint(store.bp)
app.register_blueprint(item.bp)
client = datastore.Client()

# Update the values of the following 3 variables
CLIENT_ID = env.get("CLIENT_ID")
CLIENT_SECRET = env.get("CLIENT_SECRET")
DOMAIN = env.get("DOMAIN")
ALGORITHMS = ["RS256"]

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


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response








# Verify the JWT in the request's Authorization header
def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        raise AuthError({"code": "no auth header",
                            "description":
                                "Authorization header is missing"}, 401)
    
    jsonurl = urlopen("https://"+ DOMAIN+"/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
        print("************UNVERIFIED_HDR", unverified_header)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}

    for key in jwks["keys"]:
        if "kid" in key.keys():
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=CLIENT_ID,
                issuer="https://"+ DOMAIN+"/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                            "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                            "description":
                                "incorrect claims,"
                                " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Unable to parse authentication"
                                " token."}, 401)

        return request.get_json()
    else:
        raise AuthError({"code": "no_rsa_key",
                            "description":
                                "No RSA key in JWKS"}, 401)



@app.route('/')
def index():
    return "Please navigate to /boats to use this API"
# Create a lodging if the Authorization header contains a valid JWT
# @app.route('/boats', methods=['POST'])
# def boats_post():
#     if request.method == 'POST':
#         try:
#             payload = verify_jwt(request)
#             content = request.get_json()
#             new_boat = datastore.entity.Entity(key=client.key("boats"))
#             new_boat.update({"name": content["name"], "type": content["type"],
#             "length": content["length"], "public": content["public"], "owner": payload["sub"]})
#             client.put(new_boat)
#             return jsonify(id=new_boat.key.id), 201
#         except:
            # return '', 401
        

# @app.route('/boats', methods=['GET'])
# def boats_get():
#     if request.method == 'GET':
#         query = client.query(kind='boats')
#         try:
#             payload = verify_jwt(request)
#             owner = payload["sub"]
#             query.add_filter("owner", "=", owner)
#             results = list(query.fetch())
#             for e in results:
#                 e["id"] = e.key.id
#             return json.dumps(results), 200
#         except:
#             query.add_filter("public", "=", True)
#             results = list(query.fetch())
#             for e in results:
#                 e["id"] = e.key.id
#             return json.dumps(results), 200

# @app.route('/owners/<owner_id>/boats', methods=['GET'])
# def owners_get(owner_id):
#     if request.method == 'GET':
#         query = client.query(kind='boats')
#         query.add_filter("owner", "=", str(owner_id))
#         query.add_filter("public", "=", True)
#         results = list(query.fetch())
#         for e in results:
#             e["id"] = e.key.id
#         return json.dumps(results), 200
#     else:
#         return jsonify(error='Method not recogonized')

# @app.route('/boats/<boat_id>', methods=['DELETE'])
# def boats_delete(boat_id):
#     if request.method == 'DELETE':
#         try:
#             payload = verify_jwt(request)
#             owner = payload["sub"]
#             key = client.key('boats', int(boat_id))
#             boat = client.get(key=key)
#             if boat and boat["owner"] == owner:
#                 client.delete(key)
#                 return '', 204
#             else:
#                 return '', 403
#         except:
#             return '', 401

#     else:
#         return jsonify(error='Method not recogonized')

# Decode the JWT supplied in the Authorization header
# @app.route('/decode', methods=['GET'])
# def decode_jwt():
#     payload = verify_jwt(request)
#     return payload          

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

