import json

import bottle
from bottle import request, response, route

import go

import uuid

DEBUG = True
GSM_POOL = dict()

@route('/move', method='OPTIONS')
@route('/move', method='POST')
def move():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'origin, x-csrftoken, content-type, accept'

    if request.method == 'OPTIONS':
        return 'received options request'

    if not request.get_cookie('betago_user_guid'):
        player_uuid = str(uuid.uuid4())
        response.set_cookie('betago_user_guid', player_uuid)
    else:
        player_uuid = request.get_cookie('betago_user_guid')

    if DEBUG:
        print 'BODY: ', str(request.body.read())
        print 'JSON: ', request.json

    incoming_bundle = request.json

    if player_uuid not in GSM_POOL:
        gsm = go.GameStateManager()
        GSM_POOL[player_uuid] = gsm
    else:
        gsm = GSM_POOL[player_uuid]

    return gsm.do_workflow(incoming_bundle)

if __name__ == "__main__":
    # TODO: initialize your model here
    bottle.run(host='0.0.0.0', debug=True)
