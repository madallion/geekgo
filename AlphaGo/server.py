import json

import bottle
from bottle import request, route

import go

@route('/move', method='POST')
def move(self):
    incoming_bundle = request.json

    return go.do_workflow(incoming_bundle)

if __name__ == "__main__":
    # TODO: initialize your model here
    bottle.run()
