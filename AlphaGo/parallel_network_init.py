
from AlphaGo.geekgo import GameState
import os
import json
import random
import numpy as np
from random import shuffle
from AlphaGo import geek_util
import re
import subprocess
import uuid

WHITE = -1
BLACK = +1
EMPTY = 0
PASS_MOVE = None


def init_cnnpolicynetwork():
	from AlphaGo.models.policy import CNNPolicy
	global policy
	train_folder = 'D:\\ps\\club\\Go\\models'
	metapath = os.path.join(train_folder, '0516.policy.model.json')
	weights_file=os.path.join(train_folder, 'tomSL.00010.hdf5');

	#with open(metapath) as metafile:
	#    metadata = json.load(metafile)
	#arch = {'filters_per_layer': 128} # args to CNNPolicy.create_network()
	#policy = CNNPolicy(feature_list=metadata['feature_list'], **arch);
	policy = CNNPolicy.load_model(metapath);
	policy.model.load_weights(weights_file);

def init_cnnValueNetwork():
	from AlphaGo.models.value import CNNValue
	train_folder = 'D:\\ps\\club\\Go\\models'
	metapath = os.path.join(train_folder, 'value_model.json')
	weights_file=os.path.join(train_folder, 'valNetTrain500Pairs.weights.00009.hdf5');

	with open(metapath) as metafile:
	    metadata = json.load(metafile)
	arch = {'filters_per_layer': 128} # args to CNNPolicy.create_network()
	VALUENET = CNNValue.load_model(metapath)
	VALUENET.model.load_weights(weights_file);
	return VALUENET

def value_network(state, VALUENET):
	value = VALUENET.eval_state(state)
	#print ('vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv', value, state.history, len(state.history), state.current_player)
	return value[0]	
