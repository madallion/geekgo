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

    if request.get_cookie('betago_user_guid'):
        player_uuid = request.get_cookie('betago_user_guid')
    else:
        player_uuid = str(uuid.uuid4())
        response.set_cookie('betago_user_guid', player_uuid)

    if DEBUG:
        print 'input: ', str(request.body.read())
        print 'user_uuid: ', player_uuid, 
        print 'size_gsm_pool: ', len(GSM_POOL)

    incoming_bundle = request.json

    if player_uuid not in GSM_POOL:
        gsm = go.GameStateManager()
        GSM_POOL[player_uuid] = gsm
    else:
        gsm = GSM_POOL[player_uuid]

    resp = gsm.do_workflow(incoming_bundle)

    if DEBUG:
        gsm.print_board()

    return resp

if __name__ == "__main__":
    # TODO: initialize your model here
    bottle.run(host='0.0.0.0', debug=True)
