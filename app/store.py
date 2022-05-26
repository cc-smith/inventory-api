import datetime
from google.cloud import datastore
from flask import Blueprint, request
import json
from . import constants
from .queryResults import QueryResults
from .verify_jwt import verify_jwt

bp = Blueprint('store', __name__, url_prefix='/stores')

client = datastore.Client()

env = 'dev'
if env == 'dev':
    store_url = 'http://127.0.0.1:8080/stores/'
    item_url = 'http://127.0.0.1:8080/items/'
else:
    store_url = 'https://inventory-api-350817.uc.r.appspot.com/stores/'
    item_url = 'https://inventory-api-350817.uc.r.appspot.com/items/'
    
#Get all stores and add a new store
@bp.route('', methods=['GET', 'POST'])
def stores_get_post():
    
    # get the authenticated user
    decoded_jwt = verify_jwt(request)
    owner_id = decoded_jwt["sub"]
    owner_email = decoded_jwt["email"]

    # retrieve stores owned by current authenticated user
    if request.method == 'GET':
        # fetch the stores in paginated form
        query = client.query(kind=constants.stores)
        query.add_filter( 'owner_id', '=', owner_id)
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
                "owner_id": owner_id,
                "owner_emaiL": owner_email,
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

# Edit a store, delete a store, get a store by id
@bp.route('/<id>', methods=['GET', 'PATCH', 'PUT', 'DELETE'])
def stores_put_delete_get(id):
    # fetch the store object
    store_key = client.key(constants.stores, int(id))
    store = client.get(key=store_key)

    if not store:
        return {"Error": "No store with this store id exists"}, 404

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

@bp.route('/<store_id>/items/<item_id>', methods=['PUT', 'DELETE'])
def items_put_delete(item_id, store_id):
    # Put a item on a store
    if request.method == 'PUT':
        # get the item
        item_key = client.key(constants.items, int(item_id))
        item = client.get(key=item_key)
        # get the store
        store_key = client.key(constants.stores, int(store_id))
        store = client.get(key=store_key)

        # error, store and/or item not found
        if not store or not item:
            return {"Error": "The specified store and/or item does not exist"}, 404

        # error, already a store in the item
        elif item["store"]:
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
            # update the store's item
            store['items'].append(item_object)
            client.put(store)

            # upate the item's store
            item.update({"store": store_object})
            client.put(item)

            return '', 204

    # remove item from store
    elif request.method == 'DELETE':
        # get the item
        item_key = client.key(constants.items, int(item_id))
        item = client.get(key=item_key)
        # get the store
        store_key = client.key(constants.stores, int(store_id))
        store = client.get(key=store_key)

        # error, store and/or item not found
        if not store or not item:
            return {"Error": "No store with this store_id is itemed with the item with this item_id"}, 404

        # check if item is on store
        flag = False
        for x in store['items']:
            if x['id'] == int(item_id):
                flag = True
                continue
        if flag is False:
            return {"Error": "No store with this store_id is itemed with the item with this item_id"}, 404

        # check item is assigned to this store
        if item["store"]["id"] != int(store_id):
            return {"Error": "No store with this store_id contains this item with this item_id"}, 404
        
        else:
            # remove store from item
            item.update({"carrier": None})
            client.put(item)

            # remove item from store
            for item in store['items']:
                if item['id'] == int(item_id):
                    store['items'].remove(item)
            client.put(store)
            return '', 204

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
        if 'items' in store.keys():
            for item in store['items']:
                item_key = client.key(constants.items, int(item['id']))
                items.append(item_key)
        return {"items": client.get_multi(items)}
