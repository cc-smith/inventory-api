from google.cloud import datastore
from flask import Flask, request, jsonify, _request_ctx_stack, g
import requests
from functools import wraps
import json

from urllib.request import urlopen
from jose import jwt

from os import environ as env
from werkzeug.exceptions import HTTPException

from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask import jsonify


ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

CLIENT_ID = env.get("CLIENT_ID")
CLIENT_SECRET = env.get("CLIENT_SECRET")
DOMAIN = env.get("DOMAIN")
ALGORITHMS = ["RS256"]


class JwtTest:
    def __init__(self, request, owner_id=None, owner_email=None, error=None):
        self.request = request
        self.owner_id = owner_id
        self.owner_email = owner_email
        self.error = error

    @classmethod
    # Verify the JWT in the request's Authorization header
    def verify_jwt(cls, request):

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization'].split()
            token = auth_header[1]
        else:
            error = {"code": "no auth header", "description":"Authorization header is missing"}, 401
            return (cls, error)
        
        jsonurl = urlopen("https://"+ DOMAIN+"/.well-known/jwks.json")
        jwks = json.loads(jsonurl.read())
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.JWTError:
            error = {"code": "invalid_headerr", "description": "Invalid header. Use an RS256 signed JWT Access Token"}, 401
            return (cls, error)

        if unverified_header["alg"] == "HS256":
            error = {"code": "invalid_header", "description": "Invalid header. Use an RS256 signed JWT Access Token"}, 401
            return (cls, error)

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
                error = {"code": "token_expired",
                                "description": "token is expired"}, 401
                return (cls, error)
            except jwt.JWTClaimsError:
                
                error = {"code": "invalid_claims",
                                "description":
                                    "incorrect claims,"
                                    " please check the audience and issuer"}, 401
                return (cls, error)

            except Exception:
                error = {"code": "invalid_header",
                                "description":
                                    "Unable to parse authentication"
                                    " token."}, 401
                return (cls, error)
                
            owner_id = payload["sub"]
            owner_email = payload["email"]
            error = ''
            return cls(owner_id, owner_email, error)
        else:
            error = {"code": "no_rsa_key",
                                "description":
                                    "No RSA key in JWKS"}, 401
            return (cls, error)

