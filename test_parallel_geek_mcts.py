
from AlphaGo.geekgo import GameState
from AlphaGo.geek_mcts import ParallelMCTS
from AlphaGo.geek_mcts import TreeNode
import random
import unittest

import os
import argparse
import json
import cPickle as pickle
#import six.moves.cPickle as pickle
import random
import numpy as np
import AlphaGo.gsm as GameStateMan

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
	global VALUENET
	train_folder = 'D:\\ps\\club\\Go\\models'
	metapath = os.path.join(train_folder, 'value_model.json')
	weights_file=os.path.join(train_folder, 'value.100games.weights.00009-bugfixed.hdf5');

	with open(metapath) as metafile:
	    metadata = json.load(metafile)
	arch = {'filters_per_layer': 128} # args to CNNPolicy.create_network()
	VALUENET = CNNValue.load_model(metapath)
	VALUENET.model.load_weights(weights_file);

def value_network(state):
	value = VALUENET.eval_state(state)
	print (value, state.history, len(state.history), state.current_player)
	return value	

class TestMCTS(unittest.TestCase):

	def setUp(self):
		metapath = 'D:\\ps\\club\\Go\\exp\\2-7win1-17.bug.sgf'
		with open(metapath, 'r') as metafile:
			gs = geek_util.sgf_to_gamestate(metafile.read())
		self.aiColor = BLACK
		self.gs = gs
		self.mcts = ParallelMCTS(self.gs, self.value_network, self.policy_network, self.rollout_policy_random, lmbda=0.5, n_search=1, c_puct = 2.5, playout_depth = 5, rollout_limit = 500)
		self.mcts.aiColor = self.aiColor
		
		#gs = GameState()
		#gs.do_move((3, 15))  # B
		#gs.do_move((15, 3))  # W
		#gs.do_move((15, 15))  # B
		#self.mcts.aiColor = WHITE
		init_cnnValueNetwork()
		init_cnnpolicynetwork()
		gsm = GameStateMan.GameStateManager(policy, VALUENET)
		gsm.game_state_instance = gs
		gsm.print_board()

		
	def test_mcts_getMove(self):
		move = self.mcts.get_move(self.gs)
		self.mcts.update_with_move(move)
		print ('final next move', move);

	def policy_network(self, state, limit = 8):
		nextMoveList = policy.eval_state(state, state.get_legal_moves())
		srtList = sorted(nextMoveList, key=lambda probDistribution: probDistribution[1], reverse=True);
		res = srtList[0:limit - 1]
		print res
		#if len(state.history) < 4:
		#    res = [((3,16),  0.011963408), ((3,3),  0.014572658)]
		#shuffle(res)
		return res

	def policy_network_random_noEyes(self, state):
		moves = state.get_legal_moves(include_eyes=False)
		# 'random' distribution over positions that is smallest
		# at (0,0) and largest at (18,18)
		probs = np.arange(361, dtype=np.float)
		probs = probs / probs.sum()
		#print zip(moves, probs)
		return zip(moves, probs)

	def policy_network_random_withEyes(self, state):
		moves = state.get_legal_moves(include_eyes=True)
		# 'random' distribution over positions that is smallest
		# at (0,0) and largest at (18,18)
		probs = np.arange(361, dtype=np.float)
		probs = probs / probs.sum()
		return zip(moves, probs)


	def policy_network_random(self, state):
		moves = state.get_legal_moves(include_eyes=False)
		actions = []
		for move in moves:
			actions.append((move, random.uniform(0, 1)))
		return actions

	def value_network_dummy(self, state):
		#金角银边草肚皮
		return 0.5


	def value_network_java(self, state):
		sgfId = str(uuid.uuid4())
		sgfPath = "d:\\tmp\\%s.value_network.sgf" % sgfId;
		util.gamestate_to_sgf(state,  sgfPath)
		t = subprocess.check_output(["cmd.exe", " /c D:\ps\club\Go\eval.bat %s" % sgfPath])
		m = re.search('B:(\d+);W:(\d+)', t)
		blackImpactScope = float(m.group(1));
		whiteImpactScope = float(m.group(2));
		value = blackImpactScope / (blackImpactScope + whiteImpactScope)
		if self.aiColor == WHITE:
			value = 1 - value
		value = value
		print (value, state.history, len(state.history), state.current_player)
		return value


	def value_network(self, state):
		value = VALUENET.eval_state(state)
		if self.aiColor == WHITE:
			value = 1 - value
		print (value, state.history, len(state.history), state.current_player)
		return value

	def rollout_policy_random(self, state):
		return self.policy_network_random(state)

	def rollout_policy_policy(self, state):
		return policy_network(state)

	def rollout_policy(self, state):
		nDepth = 3;
		#let you go first
		numOfCaptured = 0;
		numOfBeCaptured = 0;
		yourTurn = True
		#Assume AI always take WHITE
		if state.current_player == BLACK:
			yourTurn = False
		for i in range(0, nDepth - 1):
			nextMoveList = policy_network_random(state)
			state.do_move(nextMoveList[0][0])
			if yourTurn:
				numOfCaptured += len(state.last_remove_set)
			else:
				numOfBeCaptured += len(state.last_remove_set)

			yourTurn = not yourTurn
		return numOfCaptured / (numOfBeCaptured + 10)
		#return 1


if __name__ == '__main__':
	unittest.main()
