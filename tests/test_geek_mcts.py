﻿
from AlphaGo.go import GameState
from AlphaGo.mcts import MCTS
from AlphaGo.mcts import TreeNode
import random
import unittest

import os
import argparse
import json
import cPickle as pickle
#import six.moves.cPickle as pickle
import random
import numpy as np
from AlphaGo.models.policy import CNNPolicy

from random import shuffle
from AlphaGo import util

train_folder = 'D:\\ps\\club\\Go'
metapath = os.path.join(train_folder, 'all_feat_model.json')
weights_file='D:\ps\club\Go\models\weights.1sepoch0413.hdf5';

with open(metapath) as metafile:
    metadata = json.load(metafile)
arch = {'filters_per_layer': 128, 'layers': 12} # args to CNNPolicy.create_network()
policy = CNNPolicy(feature_list=metadata['feature_list'], **arch);
policy.model.load_weights(weights_file);
#policy.model.compile(loss='categorical_crossentropy', optimizer='sgd')

class TestMCTS(unittest.TestCase):

	def setUp(self):
		gs = GameState(size=19)
		gs.do_move((3, 3))  # B
		gs.do_move((15, 3))  # W
		gs.do_move((15, 15))  # B
		gs.do_move((3, 15))  # W
		gs.do_move((16, 15))
		gs.do_move((16, 16))
		gs.do_move((9, 9))
		gs.do_move((14, 15))
		gs.do_move((10, 10))
		self.s = gs
		util.gamestate_to_sgf(gs, "d:\\tmp\\tmp.gs")
		print "state saved to sgf"

		self.mcts = MCTS(self.s, value_network, policy_network, rollout_policy)
		self.treenode = TreeNode()

	#def test_treenode_selection(self):
	#	actions = self.mcts.priorProb(self.s)
	#	self.treenode.expansion(actions)
	#	self.treenode.updateU_value(actions)
	#	selectednode, selectedaction = self.treenode.selection()
	#	self.assertEqual(max(actions, key=lambda x: x[1])[1], selectednode.toValue(), 'incorrect node selected')
	#	self.assertEqual(max(actions, key=lambda x: x[1])[0], selectedaction, 'incorrect action selected')

	#def test_mcts_DFS(self):
	#	treenode = self.mcts.DFS(3, self.treenode, self.s)
	#	self.assertEqual(1, treenode.nVisits, 'incorrect visit count')

	def test_mcts_getMove(self):
		action = self.mcts.getMove(3, 1000)
		self.assertIsNotNone(action, 'no output action')
		print ('final next move', action);


def policy_network(state):
    nextMoveList = policy.eval_state(state, state.get_legal_moves())
    srtList = sorted(nextMoveList, key=lambda probDistribution: probDistribution[1], reverse=True);
    res = srtList[0:10]
    shuffle(res)
    return res

def policy_network_random(state):
	s = GameState()
	moves = s.get_legal_moves()
	actions = []
	for move in moves:
		actions.append((move, random.uniform(0, 1)))
	return actions

def value_network(state):
	return 0.5

def rollout_policy_dummy(state):
	return 1

def rollout_policy(state):
	nDepth = 3;
	#let you go first
	numOfCaptured = 0;
	numOfBeCaptured = 0;
	yourTurn = True
	for i in range(0, nDepth - 1):
		nextMoveList = policy_network(state)
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
