from flask import Blueprint, request
from google.cloud import datastore
import json
import constants
client = datastore.Client()

bp = Blueprint('user', __name__, url_prefix='/users')

env = ''

if env == 'dev':
    store_url = 'http://127.0.0.1:8080/stores/'
    item_url = 'http://127.0.0.1:8080/items/'
else:
    store_url = 'https://hw4-smitchr8.uc.r.appspot.com/stores/'
    item_url = 'https://hw4-smitchr8.uc.r.appspot.com/items/'