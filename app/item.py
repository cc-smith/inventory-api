import datetime
from flask import Blueprint, request
from google.cloud import datastore
import json

from . import constants
from .queryResults import QueryResults
from .JWTtest import JwtTest

bp = Blueprint('item', __name__, url_prefix='/items')

client = datastore.Client()
now = str(datetime.datetime.now())

env = 'dev'
if env == 'dev':
    url = 'http://127.0.0.1:8080/items/'
else:
    url = 'https://inventory-api-350817.uc.r.appspot.com/items/'

# validate header
@bp.before_request
def validate_header():
    allowed_mimetypes = ['application/json', '']
    if str(request.accept_mimetypes) != "*/*":
        if request.accept_mimetypes not in allowed_mimetypes:
            return {"Error": "Not Acceptable"}, 406

@bp.route('', methods=['POST', 'GET'])
def items_get_post():
    # get the authenticated user
    jwt = JwtTest.verify_jwt(request)
    if jwt.error:
        return jwt.error

    # retrieve stores owned by current authenticated user
    if request.method == 'GET':
        # fetch the stores in paginated form
        query = client.query(kind=constants.items)
        query.add_filter( 'owner_id', '=', JwtTest.owner_id)
        results = QueryResults.paginate_results(query, constants.items)
        return json.dumps(results.output), 200

    # add a new item
    elif request.method == 'POST':
        content = request.get_json()

        new_item = datastore.entity.Entity(key=client.key(constants.items))
        new_item.update(
            {
                "name": content["name"],
                "quantity": content["quantity"],
                "price":  content["price"],
                "category":  content["category"],
                "owner_id": JwtTest.owner_id,
                "owner_emaiL": JwtTest.owner_email,
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
    
    else:
        return '', 405

@bp.route('/<id>', methods=['GET', 'PATCH', 'PUT', 'DELETE'])
def stores_put_patch_delete_get(id):
    # get the authenticated user
    jwt = JwtTest.verify_jwt(request)
    if jwt.error:
        return jwt.error

    # fetch the item object
    item_key = client.key(constants.items, int(id))
    item = client.get(key=item_key)
    if not item:
        return {"Error": "No item with this item id exists"}, 404

    # get item 
    if request.method == 'GET':
        item["id"] = item.key.id
        item["self"] = item + str(item.key.id)
        return json.dumps(item), 200

    # edit an item
    elif request.method == 'PATCH':
        content = request.get_json()
        now = str(datetime.datetime.now())
        item.update(
             {
                "name": content["name"],
                "quantity": content["quantity"],
                "price":  content["price"],
                "category":  content["category"],
                "last_modified_date": now,
            }
        )
        client.put(item)
        item["id"] = item.key.id
        return json.dumps(item), 200

    # replace item attributes
    elif request.method == 'PUT':
        content = request.get_json()
        for attribute in content:
            item.update({attribute: content[attribute]}
        )
        client.put(item)
        item["id"] = item.key.id
        return json.dumps(item), 200

    # delete item
    elif request.method == 'DELETE':
        # remove relationship with store
        if item['store']:
            # get item's store
            store_key = client.key(constants.stores, int(item['store']['id']))
            store = client.get(key=store_key)
            
            # remove item from store's list of items
            match = next(item for item in store['items'] if item['id'] == int(id))
            store['items'].remove(match)
            client.put(store)

        client.delete(item_key)
        return '', 204
    
    else:
        return '', 405

    





