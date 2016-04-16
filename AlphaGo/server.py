import json

import bottle
from bottle import request, response, route

import go

import uuid

DEBUG = True
GSM_POOL = dict()
GSM_IP_POOL = dict()
import os
import argparse
import json
#import cPickle as pickle
import six.moves.cPickle as pickle
import random
import numpy as np
from keras.callbacks import ModelCheckpoint
from AlphaGo.models.policy import CNNPolicy

#def __init__(self, *args, **kwargs):
train_folder = '/home/yimlin/betago_workspace/deploy'
metapath = os.path.join(train_folder, 'all_feat_model.json')
with open(metapath) as metafile:
    metadata = json.load(metafile)
weights_file= os.path.join(train_folder, 'weights.3rdEpoch.hdf5');
arch = {'filters_per_layer': 128, 'layers': 12} # args to CNNPolicy.create_network()
policy = CNNPolicy(feature_list=metadata['feature_list'], **arch);
policy.model.load_weights(weights_file);
policy.model.compile(loss='categorical_crossentropy', optimizer='sgd')
#bottle.__init__(self, *args, **kwargs)

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
        print 'size_gsm_pool: ', len(GSM_POOL)

    incoming_bundle = request.json
    client_ip = request.environ.get('REMOTE_ADDR')

    sessionId = ""
    if ('sessionId' in incoming_bundle):
        sessionId = incoming_bundle['sessionId']
        if (sessionId ==""):
            sessionId = str(uuid.uuid4())
            incoming_bundle['sessionId'] = sessionId

    if (sessionId ==""):
        sessionId = client_ip;
        incoming_bundle['sessionId'] = sessionId

    if sessionId not in GSM_IP_POOL:
        gsm = go.GameStateManager(policy)
        GSM_IP_POOL[sessionId] = gsm
    else:
        gsm = GSM_IP_POOL[sessionId]

    resp = gsm.do_workflow(incoming_bundle)

    if DEBUG:
        gsm.print_board()

    return resp

if __name__ == "__main__":
    # TODO: initialize your model here
    
    bottle.run(host='0.0.0.0', port=8080, debug=True)
