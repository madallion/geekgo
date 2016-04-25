
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

WHITE = -1
BLACK = +1
EMPTY = 0
PASS_MOVE = None


class Expert():

	def __init__(self, policy, state, aiColor = WHITE):
		self.s = GameState()
		self.policy = policy
		self.mcts = MCTS(self.s, self.value_network, self.policy_network, self.rollout_policy, n_search=4)
		self.aiColor = aiColor
	def mcts_getMove(self, state, lastAction):
		if lastAction[0] != -1:
			self.mcts.update_with_move(lastAction)		
		move = self.mcts.get_move(self.gs)
		self.mcts.update_with_move(move)
		return move

		## update the tree		
		#if lastAction[0] != -1:
		#	if lastAction not in self.mcts.treenode.children:
		#		self.mcts.treenode.expansion([(lastAction, 0.5)])
		#		self.mcts.treenode.updateU_value([(lastAction, 0.5)])
		#	self.mcts.state.do_move(lastAction)
		#	self.mcts.treenode = self.mcts.treenode.children[lastAction]

		#nextAction = self.mcts.getMove(3, 10)
		#self.mcts.state.do_move(nextAction)

		#if nextAction not in self.mcts.treenode.children:
		#	self.mcts.treenode.expansion([(nextAction, 0.5)])
		#	self.mcts.treenode.updateU_value([(nextAction, 0.5)])
		#self.mcts.treenode = self.mcts.treenode.children[nextAction] #drop previous root node

def policy_network(state):
    nextMoveList = policy.eval_state(state, state.get_legal_moves())
    srtList = sorted(nextMoveList, key=lambda probDistribution: probDistribution[1], reverse=True);
    res = srtList[0:10]
    shuffle(res)
    return res

def policy_network_random_noEyes(state):
	moves = state.get_legal_moves(include_eyes=False)
	# 'random' distribution over positions that is smallest
	# at (0,0) and largest at (18,18)
	probs = np.arange(361, dtype=np.float)
	probs = probs / probs.sum()
	return zip(moves, probs)

def policy_network_random_withEyes(state):
	moves = state.get_legal_moves(include_eyes=True)
	# 'random' distribution over positions that is smallest
	# at (0,0) and largest at (18,18)
	probs = np.arange(361, dtype=np.float)
	probs = probs / probs.sum()
	return zip(moves, probs)

def policy_network_random(state):
	moves = state.get_legal_moves()
	actions = []
	for move in moves:
		actions.append((move, random.uniform(0, 1)))
	return actions

def value_network(state):
	#TODO 金角银边草肚皮
	return 0.5

def rollout_policy_random(state):
	return policy_network_random(state)

def rollout_policy_score(state):
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
