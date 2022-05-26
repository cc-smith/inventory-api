import datetime
from os import O_WRONLY
from google.cloud import datastore
from flask import Blueprint, request
import json
from . import constants
from .queryResults import QueryResults
from .jwtToken import JwtToken

bp = Blueprint('store', __name__, url_prefix='/stores')

client = datastore.Client()

env = 'dev'
if env == 'dev':
    store_url = 'http://127.0.0.1:8080/stores/'
    item_url = 'http://127.0.0.1:8080/items/'
else:
    store_url = 'https://inventory-api-350817.uc.r.appspot.com/stores/'
    item_url = 'https://inventory-api-350817.uc.r.appspot.com/items/'
    
# validate headers
@bp.before_request
def validate_header():
    allowed_mimetypes = ['application/json', '']
    if str(request.accept_mimetypes) != "*/*":
        if request.accept_mimetypes not in allowed_mimetypes:
            return {"Error": "Not Acceptable"}, 406

# get all stores and add a new store
@bp.route('', methods=['GET', 'POST'])
def stores_get_post():
    # get the authenticated user
    jwt_payload = JwtToken.verify_jwt(request)
    if jwt_payload.error:
        return jwt_payload.error

    # retrieve stores owned by current authenticated user
    if request.method == 'GET':
        # fetch the stores in paginated form
        query = client.query(kind=constants.stores)
        query.add_filter( 'owner_id', '=', jwt_payload.owner_id)
        results = QueryResults.paginate_results(query, constants.stores)
        return json.dumps(results.output), 200

    # add new store
    if request.method == 'POST':
        content = request.get_json()
        now = str(datetime.datetime.now())

        new_store = datastore.entity.Entity(key=client.key(constants.stores))
        new_store.update(
            {
                "name": content["name"],
                "type": content["type"],
                "location": content["location"],
                "owner_id": jwt_payload.owner_id,
                "owner_emaiL": jwt_payload.owner_email,
                "creation_date": now,
                "last_modified_date": now,
                "items": [],
            }
        )
        client.put(new_store)

        # return the new store object
        store_key = client.key(constants.stores, new_store.key.id)
        new_store = client.get(key=store_key)
        new_store["id"] = new_store.key.id
        new_store["self"] = store_url + str(new_store.key.id)
        return json.dumps(new_store), 201

    else:
        return '', 405

# Edit a store, delete a store, get a store by id
@bp.route('/<id>', methods=['GET', 'PATCH', 'PUT', 'DELETE'])
def stores_put_delete_get(id):
    # get the authenticated user
    jwt_payload = JwtToken.verify_jwt(request)
    if jwt_payload.error:
        return jwt_payload.error

    # fetch the store object
    store_key = client.key(constants.stores, int(id))
    store = client.get(key=store_key)
    if not store:
        return {"Error": "No store with this store id exists"}, 404

    # verify that the current user has access to this entity
    if jwt_payload.owner_id != store["owner_id"]:
        return 'Access denied', 403

    # get store 
    if request.method == 'GET':
        store["id"] = store.key.id
        store["self"] = store_url + str(store.key.id)
        return json.dumps(store), 200

    # edit a store
    elif request.method == 'PUT':
        content = request.get_json()
        now = str(datetime.datetime.now())
        store.update(
            {
            "name": content["name"],
            "type": content["type"],
            "location": content["location"],
            "last_modified_date": now,
            }
        )
        client.put(store)
        store["id"] = store.key.id
        return json.dumps(store), 201

    # replace store attributes
    elif request.method == 'PATCH':
        content = request.get_json()
        for attribute in content:
            store.update({attribute: content[attribute]}
        )
        client.put(store)
        store["id"] = store.key.id
        return json.dumps(store), 200

    # delete store
    elif request.method == 'DELETE':
        # remove any items currently in the store
        for item in store['items']:
            item_key = client.key(constants.items, int(item['id']))
            item = client.get(key=item_key)
            item.update({"store": None})
            client.put(item)

        client.delete(store_key)
        return '', 204

    else:
        return '', 405

@bp.route('/<store_id>/items/<item_id>', methods=['PUT', 'DELETE'])
def items_put_delete(item_id, store_id):
    # get the authenticated user
    jwt_payload = JwtToken.verify_jwt(request)
    if jwt_payload.error:
        return jwt_payload.error

    # get the item
    item_key = client.key(constants.items, int(item_id))
    item = client.get(key=item_key)

    # get the store
    store_key = client.key(constants.stores, int(store_id))
    store = client.get(key=store_key)

    # error, store or item does not exist
    if not store or not item:
            return {"Error": "The specified store and/or item does not exist"}, 404

    # error, store or item does not belong to the authenticated user
    if jwt_payload.owner_id != store["owner_id"] or jwt_payload.owner_id != item["owner_id"]:
        return 'Access denied', 403

    # Put a item on a store
    if request.method == 'PUT':
        # error, already a store in the item
        if item["store"]:
            return {"Error": "The item is already in another store"}, 403

        # add the store to the item
        else:
            item_object = {
                "id": item.key.id,
                "name": item["name"],
                "self": item_url + str(item.key.id)
            }
            store_object = {
                "id": store.key.id,
                "name": store["name"],
                "self": store_url + str(store.key.id)
            }
            # update the store's items
            store['items'].append(item_object)
            client.put(store)

            # upate the item's store
            item.update({"store": store_object})
            client.put(item)

            return '', 204

    # remove item from store
    elif request.method == 'DELETE':
        # check if item is in the store
        match = next(item for item in store['items'] if item["id"] == int(item_id))
        if not match:
            return {"Error": "Item not found in store"}, 404

        # check item is assigned to this store
        elif item["store"]["id"] != int(store_id):
            return {"Error": "This item is not assigned to this store"}, 404
        
        else:
            # remove store from item
            item.update({"store": None})
            client.put(item)

            # remove item from store
            store['items'].remove(match)
            client.put(store)
            return '', 204
    else:
        return '', 405

@bp.route('/<store_id>/items', methods=['GET'])
def items_get(store_id):
    if request.method == 'GET':
        # get the store
        store_key = client.key(constants.stores, int(store_id))
        store = client.get(key=store_key)

        # error, invalid store id
        if not store:
            return {"Error": "No store with this store id exists"}, 404

        # get the list of items in the store
        items = []
        for item in store['items']:
            item_key = client.key(constants.items, int(item['id']))
            items.append(item_key)
        return {"items": client.get_multi(items)}
    else:
        return '', 405
