from importlib.resources import contents
from flask import Blueprint, request
from google.cloud import datastore
import json
from . import constants
client = datastore.Client()
# from main import verify_jwt
from os import environ as env

bp = Blueprint('user', __name__, url_prefix='/users')
# excludes route form jwt verification
def exclude_from_auth(func):
    func._exclude_from_auth = True
    return func

@bp.route('', methods=['GET', 'POST'])
@exclude_from_auth  # do not require jwt verification for this route
def get_users():
    # verify the token and get the requiest body
    if request.method == 'GET':
        query = client.query(kind='users')
        results = list(query.fetch())
        for e in results:
            e["id"] = e.key.id
        return json.dumps(results), 200

    elif request.method == 'POST':
        content = request.get_json(force=True)
        # check if user already exists
        query = client.query(kind=constants.users)
        query.add_filter("sub", "=", content['sub'])
        results = list(query.fetch())
        if results:
            return '', 200

        # add new user
        new_user = datastore.entity.Entity(key=client.key(constants.users))
        new_user.update(
            {"name": content["name"],
                "sub": content["sub"],
            })
        client.put(new_user)

        # return the new user object
        user_key = client.key(constants.users, new_user.key.id)
        new_user = client.get(key=user_key)
        new_user["id"] = new_user.key.id
        return json.dumps(new_user), 201

    
@bp.route('/<id>', methods=['DELETE'])
def delete_user(id):
    if request.method == 'DELETE':
    # get the user
        user_key = client.key(constants.users, int(id))
        user = client.get(key=user_key)
        if user:
            client.delete(user_key)
            return '', 204
        # user id not found
    else:
        return {"Error": "No user with this user_id exists"}, 404