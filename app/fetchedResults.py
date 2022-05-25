from flask import request


class FetchedResults:
    def __init__(self, query, object_type, output=None):
        self.query = query
        self.object_type = object_type
        self.output = output

    @classmethod
    def fetch_paginated_results(cls, query, object_type):
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
            
        else:
            next_url = None
        for e in results:
            e["id"] = e.key.id
        output = {object_type: results}
        if next_url:
            output["next"] = next_url

        return cls(query, object_type, output)