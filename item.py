from flask import Blueprint, request
from google.cloud import datastore
import json
from json2html import *
import constants

client = datastore.Client()

bp = Blueprint('item', __name__, url_prefix='/items')

env = ''

if env == 'dev':
    url = 'http://127.0.0.1:8080/items/'
else:
    url = 'https://hw4-smitchr8.uc.r.appspot.com/items/'

@bp.route('', methods=['POST', 'GET'])
def items_get_post():
    # Create a item
    if request.method == 'POST':
        content = request.get_json()
        # error: missing attributes
        if len(content) < 3:
            error_message = {
                "Error": "The request object is missing at least one of the required attributes"}
            return error_message, 400
        # add the item
        else:
            new_item = datastore.entity.Entity(key=client.key(constants.items))
            new_item.update(
                {
                    "volume": content["volume"],
                    "item":  content["item"],
                    "creation_date":  content["creation_date"],
                    "carrier":  None
                }
            )
            client.put(new_item)

            # return the new item object
            item_key = client.key(constants.items, new_item.key.id)
            item = client.get(key=item_key)
            new_item["id"] = new_item.key.id
            new_item["self"] = url + str(new_item.key.id)
            return json.dumps(new_item), 201

    # Get all items
    elif request.method == 'GET':
        query = client.query(kind=constants.items)
        q_limit = int(request.args.get('limit', '3'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit=q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + \
                str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
        output = {"items": results}
        if next_url:
            output["next"] = next_url
        return json.dumps(output), 200

    else:
        return 'Method not recognized'


@bp.route('/<id>', methods=['DELETE', 'GET'])
def items_get_delete(id):

    # delete a item
    if request.method == 'DELETE':
        key = client.key(constants.items, int(id))
        item = client.get(key=key)
        if item:
            # remove the item from its boat
            boat_key = client.key(constants.boats, int(item['carrier']['id']))
            boat = client.get(key=boat_key)
            if boat:
                for item in boat['items']:
                    if item['id'] == int(id):
                        boat['items'].remove(item)
                client.put(boat)

            # delete the item
            client.delete(key)
            return '', 204
        else:
            return {"Error": "No item with this item_id exists"}, 404

    # Get a item by id
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


