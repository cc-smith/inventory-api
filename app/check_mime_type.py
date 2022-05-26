from flask import request


def check_mime_type():
    allowed_mimetypes = ['application/json', 'text/html', '']
    if str(request.accept_mimetypes) != "*/*":
        if request.accept_mimetypes not in allowed_mimetypes:
            return {"Error": "Not Acceptable"}, 406