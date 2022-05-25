import datetime
from flask import Blueprint, request
from google.cloud import datastore
import json
from . import constants
from .fetchedResults import FetchedResults
from .verify_jwt import verify_jwt

bp = Blueprint('item', __name__, url_prefix='/items')

client = datastore.Client()

env = 'dev'
if env == 'dev':
    url = 'http://127.0.0.1:8080/items/'
else:
    url = 'https://inventory-api-350817.uc.r.appspot.com/items/'

@bp.route('', methods=['POST', 'GET'])
def items_get_post():
    # get the authenticated user
    decoded_jwt = verify_jwt(request)
    owner_id = decoded_jwt["sub"]
    owner_email = decoded_jwt["email"]

    # add a new item
    if request.method == 'POST':
        now = str(datetime.datetime.now())
        content = request.get_json()

        new_item = datastore.entity.Entity(key=client.key(constants.items))
        new_item.update(
            {
                "name": content["name"],
                "quantity": content["quantity"],
                "price":  content["price"],
                "category":  content["category"],
                "owner_id": owner_id,
                "owner_emaiL": owner_email,
                "creation_date": now,
                "last_modified_date": now,
                "store": None
            }
        )
        client.put(new_item)

        # return the new item object
        item_key = client.key(constants.items, new_item.key.id)
        item = client.get(key=item_key)
        new_item["id"] = new_item.key.id
        new_item["self"] = url + str(new_item.key.id)
        return json.dumps(new_item), 201

    # retrieve stores owned by current authenticated user
    elif request.method == 'GET':
        # fetch the stores in paginated form
        query = client.query(kind=constants.items)
        query.add_filter( 'owner_id', '=', owner_id)
        results = FetchedResults.fetch_paginated_results(query, constants.items)
        return json.dumps(results.output), 200

@bp.route('/<id>', methods=['DELETE', 'GET'])
def items_get_delete(id):

    # delete a item
    if request.method == 'DELETE':
        key = client.key(constants.items, int(id))
        item = client.get(key=key)
        if item:
            # remove the item from its store
            store_key = client.key(constants.stores, int(item['store']['id']))
            store = client.get(key=store_key)
            if store:
                for item in store['items']:
                    if item['id'] == int(id):
                        store['items'].remove(item)
                client.put(store)

            # delete the item
            client.delete(key)
            return '', 204
        else:
            return {"Error": "No item with this item_id exists"}, 404

    # Get an item by id
    elif request.method == 'GET':
        if id == 'null':
            return 200
        item_key = client.key(constants.items, int(id))
        item = client.get(key=item_key)
        if item:
            item["id"] = item.key.id
            item["self"] = url + str(item.key.id)
            return json.dumps(item), 200
        # error, no item with this id
        else:
            return {"Error": "No item with this item_id exists"}, 404
    else:
        return 'Method not recognized'


