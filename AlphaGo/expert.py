
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
		self.mcts = MCTS(self.s, self.value_network, self.policy_network, self.rollout_policy)
		self.treenode = TreeNode()
		self.aiColor = aiColor
	def mcts_getMove(self, state, lastAction):
		
		## update the tree		
		if lastAction[0] != -1:
			if lastAction not in self.mcts.treenode.children:
				self.mcts.treenode.expansion([(lastAction, 0.5)])
				self.mcts.treenode.updateU_value([(lastAction, 0.5)])
			self.mcts.state.do_move(lastAction)
			self.mcts.treenode = self.mcts.treenode.children[lastAction]

		nextAction = self.mcts.getMove(3, 10)
		self.mcts.state.do_move(nextAction)

		if nextAction not in self.mcts.treenode.children:
			self.mcts.treenode.expansion([(nextAction, 0.5)])
			self.mcts.treenode.updateU_value([(nextAction, 0.5)])
		self.mcts.treenode = self.mcts.treenode.children[nextAction] #drop previous root node

		return nextAction

	def policy_network(self, state):
		nextMoveList = self.policy.eval_state(state, state.get_legal_moves())
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

	def value_network(self, state):
	    return 0.5

	def rollout_policy_dummy(state):
	    return 1

	def rollout_policy(self, state):
		nDepth = 3;
		#let you go first
		numOfCaptured = 0;
		numOfBeCaptured = 0;
		aiTurn = False
		#Assume AI always take WHITE
		if state.current_player == self.aiColor:
			aiTurn = True
		for i in range(0, nDepth - 1):
			nextMoveList = policy_network_random(state)
			state.do_move(nextMoveList[0][0])
			if aiTurn:
				numOfCaptured += len(state.last_remove_set)
			else:
				numOfBeCaptured += len(state.last_remove_set)
			aiTurn = not aiTurn

		return numOfCaptured / (numOfBeCaptured + 10)

