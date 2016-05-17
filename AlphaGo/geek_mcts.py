import numpy as np
import random
from AlphaGo import geek_util
import uuid
import subprocess
import re

WHITE = -1
BLACK = +1
EMPTY = 0
PASS_MOVE = None
import multiprocessing
from multiprocessing.pool import Pool

def value_network_java(state):
	sgfId = str(uuid.uuid4())
	sgfPath = "d:\\tmp\\%s.value_network.sgf" % sgfId;
	geek_util.gamestate_to_sgf(state,  sgfPath)
	t = subprocess.check_output(["cmd.exe", " /c D:\ps\club\Go\eval.bat %s" % sgfPath])
	m = re.search('B:(\d+);W:(\d+)', t)
	blackImpactScope = float(m.group(1));
	whiteImpactScope = float(m.group(2));
	value = blackImpactScope / (blackImpactScope + whiteImpactScope)
	
	#value = value 
	print (value, state.history[-5:-1])
	return value

def value_network(state):
	value = VALUENET.eval_state(state)
	print (value, state.history, len(state.history), state.current_player)
	return value	

def value_network_dummy(state):
	#金角银边草肚皮
	return 0.5

def policy_network_random_noEyes(state):
	moves = state.get_legal_moves(include_eyes=False)
	# 'random' distribution over positions that is smallest
	# at (0,0) and largest at (18,18)
	actions = []
	for move in moves:
		actions.append((move, random.uniform(0, 1)))
	return actions

def evaluate_rollout(state, rolloutPolicy = policy_network_random_noEyes, limit = 300):
		"""Use the rollout policy to play until the end of the game, get the winner (or 0 if tie)
		"""
		for i in xrange(limit):
			action_probs = rolloutPolicy(state)
			if len(action_probs) == 0:
				break
			max_action = max(action_probs, key=lambda (a, p): p)[0]
			state.do_move(max_action)
		else:
			# if no break from the loop
			print "WARNING: rollout reached move limit"
		#return state.get_winner()
		return state.get_winner_Score() / 100



def mcplayout(state, valueFunc = value_network_dummy, rolloutFunc = evaluate_rollout, aiColor = BLACK, lmbda = 0.5):
	# leaf evaluation
	v = valueFunc(state)
	z = rolloutFunc(state.copy(), policy_network_random_noEyes)
	# when ai is WHITE, z<0 means WHITE wins
	#	Color Score EvalValue
	#   +1	  +1		+1
	#	+1	  -1		-1
	#	-1     -1       +1
	#   -1     +1       -1
	if aiColor == WHITE:
		z = -z
		v = 1 - v

	leaf_value = (1 - lmbda) * v + lmbda * z  + v * z
	return 	leaf_value


class TreeNode(object):
	"""Tree Representation of MCTS that covers Selection, Expansion, Evaluation, and backUp (aka 'update()')
	"""
	def __init__(self, parent, prior_p, c_puct = 5, lmbda = 0.5):
		self.lmbda = lmbda
		self.parent = parent
		self.nVisits = 1
		self.P = prior_p
		self.Q_value =  1
		self.u_value =  1 #prior_p * c_puct * 10
		self.children = {}
#=======
#	def __init__(self, parent, prior_p):
#		self.parent = parent
#		self.nVisits = 0
#		self.Q_value = 0
#		self.u_value = prior_p
#		self.children = {}
#		self.P = prior_p
#>>>>>>> latest

	def expansion(self, actions):
		"""Expand subtree - a dictionary with a tuple of (x,y) position as keys, TreeNode object as values

		Keyword arguments:
		Output from policy function - a list of tuples of (x, y) position and prior probability

		Returns:
		None
		"""
		for action, prob in actions:
			if action not in self.children:
				self.children[action] = TreeNode(self, prob, lmbda=self.lmbda)
#=======
#				self.children[action] = TreeNode(self, prob)
#>>>>>>> latest

	def selection(self):
		"""Select among subtree to get the position that gives maximum action value Q plus bonus u(P)

		Keyword arguments:
		None.

		Returns:
		a tuple of (action, next_node)
		"""
		for (a, n) in self.children.iteritems():
			print (a, n.Q_value, n.u_value, n.nVisits)
		return max(self.children.iteritems(), key=lambda (a, n): n.toValue())

	def isLeaf(self):
		"""Check if leaf node (i.e. no nodes below this have been expanded)
		"""
		return self.children == {}

	def update(self, leaf_value, c_puct):
		"""Update node values from leaf evaluation

		Arguments:
		value of traversed subtree evaluation

		Returns:
		None
		"""
		# count visit
		self.nVisits += 1
		# update Q
		mean_V = self.Q_value * (self.nVisits - 1)
		self.Q_value = (mean_V + leaf_value) / self.nVisits
		# update u (note that u is not normalized to be a distribution)
		self.u_value = c_puct * self.P * np.sqrt(self.parent.nVisits) / (1 + self.nVisits)
		print ('u_value', self.parent.nVisits, self.nVisits, self.u_value)
	def toValue(self):
		"""Return action value Q plus bonus u(P)
		"""
		return self.Q_value + self.u_value


class MCTS(object):
	"""Monte Carlo tree search, takes an input of game state, value network function, policy network function,
	rollout policy function. get_move outputs an action after lookahead search is complete.

	The value function should take in a state and output a number in [-1, 1]
	The policy and rollout functions should take in a state and output a list of (action,prob) tuples where
		action is an (x,y) tuple

	lmbda and c_puct are hyperparameters. 0 <= lmbda <= 1 controls the relative weight of the value network and fast
	rollouts in determining the value of a leaf node. 0 < c_puct < inf controls how quickly exploration converges
	to the maximum-value policy
	"""

	def __init__(self, state, value_network, policy_network, rollout_policy, lmbda=0.5, c_puct=5, rollout_limit=500, playout_depth=20, n_search=10000, aiColor=BLACK):
		self.root = TreeNode(None, 1.0, lmbda=lmbda)
		self._value = value_network
		self._policy = policy_network
		self._rollout = rollout_policy
		self._lmbda = lmbda
		self._c_puct = c_puct
		self._rollout_limit = rollout_limit
		self._L = playout_depth
		self._n_search = n_search
		self.aiColor = aiColor
	
	def _DFS(self, nDepth, treenode, state):
		"""Monte Carlo tree search over a certain depth per simulation, at the end of simulation,
		the action values and visits of counts of traversed treenode are updated.

		Keyword arguments:
		Initial GameState object
		Initial TreeNode object
		Search Depth

		Returns:
		None
		"""

		visited = [None] * nDepth

		# Playout to nDepth moves using the full policy network
		for index in xrange(nDepth):
			action_probs = self._policy(state)
			# check for end of game
			if len(action_probs) == 0:
				break
			treenode.expansion(action_probs)
			action, treenode = treenode.selection()
			print action
			state.do_move(action)
			visited[index] = treenode

		# leaf evaluation
		v = self._value(state)
		z = self._evaluate_rollout(state.copy(), self._rollout_limit)
		# when ai is WHITE, z<0 means WHITE wins
		#	Color Score EvalValue
		#   +1	  +1		+1
		#	+1	  -1		-1
		#	-1     -1       +1
		#   -1     +1       -1
		if self.aiColor == WHITE:
			z = -z
		leaf_value = (1 - self._lmbda) * v + self._lmbda * z

		# update value and visit count of nodes in this traversal
		# Note: it is important that this happens from the root downward
		# so that 'parent' visit counts are correct
		for node in visited:
			node.update(leaf_value, self._c_puct)

	def _evaluate_rollout(self, state, limit):
		"""Use the rollout policy to play until the end of the game, get the winner (or 0 if tie)
		"""
		for i in xrange(limit):
			action_probs = self._rollout(state)
			if len(action_probs) == 0:
				break
			max_action = max(action_probs, key=lambda (a, p): p)[0]
			state.do_move(max_action)
		else:
			# if no break from the loop
			print "WARNING: rollout reached move limit"
		#return state.get_winner()
		return state.get_winner_Score() / 100

	def get_move(self, state):
		"""After running simulations for a certain number of times, when the search is complete, an action is selected
		from root state

		Keyword arguments:
		Number of Simulations

		Returns:
		action -- a tuple of (x, y)
		"""
		action_probs = self._policy(state)
		self.root.expansion(action_probs)

		for n in xrange(0, self._n_search):
			state_copy = state.copy()
			self._DFS(self._L, self.root, state_copy)

		# chosen action is the *most visited child*, not the highest-value
		# (note that they are the same as self._n_search gets large)
		return max(self.root.children.iteritems(), key=lambda (a, n): n.nVisits)[0]

		#instead , just chosen action with the highest-value
		#return max(self.root.children.iteritems(), key=lambda (a, n): n.toValue())[0]

	def update_with_move(self, last_move):
		"""step forward in the tree and discard everything that isn't still reachable
		"""
		if last_move in self.root.children:
			self.root = self.root.children[last_move]
			self.root.parent = None
			# siblings of root will be garbage-collected because they are no longer reachable
		else:
			self.root = TreeNode(None, 1.0, lmbda=self._lmbda)


class ParallelMCTS(MCTS):
	"""Monte Carlo tree search, takes an input of game state, value network function, policy network function,
	rollout policy function. get_move outputs an action after lookahead search is complete.

	The value function should take in a state and output a number in [-1, 1]
	The policy and rollout functions should take in a state and output a list of (action,prob) tuples where
		action is an (x,y) tuple

	lmbda and c_puct are hyperparameters. 0 <= lmbda <= 1 controls the relative weight of the value network and fast
	rollouts in determining the value of a leaf node. 0 < c_puct < inf controls how quickly exploration converges
	to the maximum-value policy
	"""

	def __init__(self, state, value_network, policy_network, rollout_policy, lmbda=0.5, c_puct=5, rollout_limit=500, playout_depth=20, n_search=10000, aiColor=BLACK):
		self.root = TreeNode(None, 1.0, lmbda=lmbda)
		self._value = value_network
		global VALUE_NETWORK
		VALUE_NETWORK = value_network
		self._policy = policy_network
		self._rollout = rollout_policy
		self._lmbda = lmbda
		self._c_puct = c_puct
		self._rollout_limit = rollout_limit
		self._L = playout_depth
		self._n_search = n_search
		self.aiColor = aiColor
	
	def _DFS(self, nDepth, treenode, state):
		"""Monte Carlo tree search over a certain depth per simulation, at the end of simulation,
		the action values and visits of counts of traversed treenode are updated.

		Keyword arguments:
		Initial GameState object
		Initial TreeNode object
		Search Depth

		Returns:
		None
		"""
		isDebug = False
		n_workers = multiprocessing.cpu_count() if not isDebug else 1  # set to 1 when debugging
		global worker_pool
		if worker_pool is None:
			worker_pool = Pool(processes=n_workers)
		outgoing = []  # positions waiting for a playout
		incoming = []  # positions that finished evaluation
		ongoing = []  # currently ongoing playout jobs
		visitedNodes = [None] * nDepth
		
		i = 0
		j = 0
		n = 100
		m = 30
		while i < n:
			stateCopy = state.copy();
			treenodeCopy = treeRoot;
			if not outgoing and not (isDebug and ongoing) and j < m:
				nodes = []
				# Playout to nDepth moves using the full policy network
				for index in xrange(nDepth):
						# Descend the tree so that we have something ready when a worker
						# stops being busy
						action_probs = self._policy(stateCopy)
						# check for end of game
						if len(action_probs) == 0:
							break
						treenodeCopy.expansion(action_probs)
						action, treenodeCopy = treenodeCopy.selection()
						print action
						if len(action) == 0:
							break
						stateCopy.do_move(action)
						visitedNodes[index] = treenodeCopy
						treenodeCopy.Q_value -= 10
				outgoing.append((visitedNodes, state))

			if len(ongoing) >= n_workers:
					# Too many playouts running? Wait a bit...
					ongoing[0][0].wait(0.01 / n_workers)
			elif len(outgoing) > 0:
				i += 1
				j += 1
				nodes, gs = outgoing.pop()
				atask = worker_pool.apply_async(mcplayout, (gs, value_network_dummy))
				#nodes are the treenodes in one path
				ongoing.append((atask, nodes))
			elif len(outgoing) == 0 and len(ongoing) > 0:
				ongoing[0][0].wait(100)
			else:
				i += 1

			# Anything to store in the tree?  (We do this step out-of-order
			# picking up data from the previous round so that we don't stall
			# ready workers while we update the tree.)
			while incoming:
				leaf_value, visitedNodes = incoming.pop()
				for node in visitedNodes:
					node.Q_value += 10
					node.update(leaf_value, self._c_puct)
		
			# Any playouts are finished yet?
			for job, nodes in ongoing:
				if not job.ready():
					continue
				# Yes! Queue them up for storing in the tree.
				leaf_value = job.get()
				incoming.append((leaf_value, nodes))
				ongoing.remove((job, nodes))

		# close process
		worker_pool.close()
		# update value and visit count of nodes in this traversal
		# Note: it is important that this happens from the root downward
		# so that 'parent' visit counts are correct

	def _evaluate_rollout(self, state, limit):
		"""Use the rollout policy to play until the end of the game, get the winner (or 0 if tie)
		"""
		for i in xrange(limit):
			action_probs = self._rollout(state)
			if len(action_probs) == 0:
				break
			max_action = max(action_probs, key=lambda (a, p): p)[0]
			state.do_move(max_action)
		else:
			# if no break from the loop
			print "WARNING: rollout reached move limit"
		#return state.get_winner()
		return state.get_winner_Score() / 100

	def get_move(self, state):
		"""After running simulations for a certain number of times, when the search is complete, an action is selected
		from root state

		Keyword arguments:
		Number of Simulations

		Returns:
		action -- a tuple of (x, y)
		"""
		action_probs = self._policy(state)
		self.root.expansion(action_probs)
		global worker_pool
		worker_pool = None
		global treeRoot
		treeRoot = self.root
		for n in xrange(0, self._n_search):
			state_copy = state.copy()
			self._DFS(self._L, self.root, state_copy)
		worker_pool = None
		# chosen action is the *most visited child*, not the highest-value
		# (note that they are the same as self._n_search gets large)
		return max(self.root.children.iteritems(), key=lambda (a, n): n.nVisits)[0]

		#instead , just chosen action with the highest-value
		#return max(self.root.children.iteritems(), key=lambda (a, n): n.toValue())[0]

	def update_with_move(self, last_move):
		"""step forward in the tree and discard everything that isn't still reachable
		"""
		if last_move in self.root.children:
			self.root = self.root.children[last_move]
			self.root.parent = None
			# siblings of root will be garbage-collected because they are no longer reachable
		else:
			self.root = TreeNode(None, 1.0, lmbda=self._lmbda)