#!/usr/bin/env python
# standard libraries
import os
import json
import uuid

# relevant third-party libraries
import bottle
from bottle import request, response, route


# local modules
from AlphaGo.models.policy import CNNPolicy
import AlphaGo.geekgo
import AlphaGo.gsm as GameStateMan

# global variables
DEBUG = True
GSM_POOL = dict()
POLICY = None


def init_cnnpolicynetwork():
    global POLICY
    #train_folder = '/home/yimlin/betago_workspace/deploy'
    train_folder = 'D:\\yimlin\\models'
    metapath = os.path.join(train_folder, '46feats_model_0515.json')
    weights_file = os.path.join(train_folder, 'weights.models_redoSL-continueOn8thEpoch_20160509.hdf5')
    POLICY = CNNPolicy.load_model(metapath);
    POLICY.model.load_weights(weights_file);

def init_cnnValueNetwork():
	from AlphaGo.models.value import CNNValue
	global VALUENET
	train_folder = 'D:\\yimlin\\models'
	metapath = os.path.join(train_folder, 'value_model.json')
	weights_file=os.path.join(train_folder, 'value.100games.weights.00009-bugfixed.hdf5');
	VALUENET = CNNValue.load_model(metapath)
	VALUENET.model.load_weights(weights_file);


@route('/move', method='OPTIONS')
@route('/move', method='POST')
def move():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'origin, x-csrftoken, content-type, accept'

    if request.method == 'OPTIONS':
        return 'received options request'

    incoming_bundle = request.json

    # determine what session id to use
    if ('sessionId' in incoming_bundle and (incoming_bundle['sessionId'] !="" )):
        session_id = incoming_bundle['sessionId']
        print session_id
    else:
        session_id = str(uuid.uuid4())
    incoming_bundle['sessionId'] = session_id
    print session_id

    # retrieve or create GameStateManager
    if session_id not in GSM_POOL:
        gsm = GameStateMan.GameStateManager(POLICY, VALUENET)
        GSM_POOL[session_id] = gsm
    else:
        gsm = GSM_POOL[session_id]

    resp = gsm.do_workflow(incoming_bundle)
    resp['sessionId'] = session_id

    if DEBUG:
        gsm.print_board()
        print 'input: ', str(request.body.read())
        print 'size_gsm_pool: ', len(GSM_POOL)

    return resp


if __name__ == "__main__":
    init_cnnpolicynetwork()
    init_cnnValueNetwork()
    bottle.run(host='0.0.0.0', port=80, debug=True)
