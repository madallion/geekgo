import json

import bottle
from bottle import request, route

import go

@route('/move', method='POST')
def move():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

    incoming_bundle = request.json

    return go.do_workflow(incoming_bundle)

if __name__ == "__main__":
    # TODO: initialize your model here
    bottle.run(host='0.0.0.0')
