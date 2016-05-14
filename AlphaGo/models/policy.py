from keras.models import Sequential, Model
from keras.models import model_from_json
from keras.layers import convolutional, merge, Input
from keras.layers.core import Activation, Flatten
import keras.backend as K
from AlphaGo.preprocessing.preprocessing import Preprocess
from AlphaGo.util import flatten_idx
import numpy as np
import json


class CNNPolicy(object):
	"""uses a convolutional neural network to evaluate the state of the game
	and compute a probability distribution over the next action
	"""

	def __init__(self, feature_list, **kwargs):
		"""create a policy object that preprocesses according to feature_list and uses
		a neural network specified by keyword arguments (see create_network())
		"""
		self.preprocessor = Preprocess(feature_list)
		kwargs["input_dim"] = self.preprocessor.output_dim
		# Using self.__class__ rather than explicitly CNNPolicy
		# so that, introspectively, this works with sublcasses
		# just as well
		self.model = self.__class__.create_network(**kwargs)
		self.forward = self._model_forward()

	def _model_forward(self):
		"""Construct a function using the current keras backend that, when given a batch
		of inputs, simply processes them forward and returns the output

		The output has size (batch x 361) for 19x19 boards (i.e. the output is a batch
		of distributions over flattened boards. See AlphaGo.util#flatten_idx)

		This is as opposed to model.compile(), which takes a loss function
		and training method.

		c.f. https://github.com/fchollet/keras/issues/1426
		"""
		forward_function = K.function([self.model.input], [self.model.output])

		# the forward_function returns a list of tensors
		# the first [0] gets the front tensor.
		return lambda inpt: forward_function([inpt])[0]

	def _select_moves_and_normalize(self, nn_output, moves, size):
		"""helper function to normalize a distribution over the given list of moves
		and return a list of (move, prob) tuples
		"""
		if len(moves) == 0:
			return []
		move_indices = [flatten_idx(m, size) for m in moves]
		# get network activations at legal move locations
		distribution = nn_output[move_indices]
		distribution = distribution / distribution.sum()
		return zip(moves, distribution)

	def batch_eval_state(self, states, moves_lists=None):
		"""Given a list of states, evaluates them all at once to make best use of GPU
		batching capabilities.

		Analogous to [eval_state(s) for s in states]


		Returns: a parallel list of move distributions as in eval_state
		"""
		n_states = len(states)
		if n_states == 0:
			return []
		state_size = states[0].size
		if not all([st.size == state_size for st in states]):
			raise ValueError("all states must have the same size")
		# concatenate together all one-hot encoded states along the 'batch' dimension
		nn_input = np.concatenate([self.preprocessor.state_to_tensor(s) for s in states], axis=0)
		# pass all input through the network at once (backend makes use of batches if len(states) is large)
		network_output = self.forward(nn_input)
		# default move lists to all legal moves
		moves_lists = moves_lists or [st.get_legal_moves() for st in states]
		results = [None] * n_states
		for i in range(n_states):
			results[i] = self._select_moves_and_normalize(network_output[i], moves_lists[i], state_size)
		return results

	def eval_state(self, state, moves=None):
		"""Given a GameState object, returns a list of (action, probability) pairs
		according to the network outputs

		If a list of moves is specified, only those moves are kept in the distribution
		"""
		tensor = self.preprocessor.state_to_tensor(state)
		# run the tensor through the network
		network_output = self.forward(tensor)
		moves = moves or state.get_legal_moves()
		return self._select_moves_and_normalize(network_output[0], moves, state.size)

	@staticmethod
	def create_network(**kwargs):
		"""construct a convolutional neural network.

		Keword Arguments:
		- input_dim:         	depth of features to be processed by first layer (no default)
		- board:             	width of the go board to be processed (default 19)
		- filters_per_layer: 	number of filters used on every layer (default 128)
		- layers:            	number of convolutional steps (default 12)
		- filter_width_K:    	(where K is between 1 and <layers>) width of filter on
								layer K (default 3 except 1st layer which defaults to 5).
								Must be odd.
		"""
		defaults = {
			"board": 19,
			"filters_per_layer": 128,
			"layers": 12,
			"filter_width_1": 5
		}
		# copy defaults, but override with anything in kwargs
		params = defaults
		params.update(kwargs)

		# create the network:
		# a series of zero-paddings followed by convolutions
		# such that the output dimensions are also board x board
		network = Sequential()

		# create first layer
		network.add(convolutional.Convolution2D(
			input_shape=(params["input_dim"], params["board"], params["board"]),
			nb_filter=params["filters_per_layer"],
			nb_row=params["filter_width_1"],
			nb_col=params["filter_width_1"],
			init='uniform',
			activation='relu',
			border_mode='same'))

		# create all other layers
		for i in range(2, params["layers"] + 1):
			# use filter_width_K if it is there, otherwise use 3
			filter_key = "filter_width_%d" % i
			filter_width = params.get(filter_key, 3)
			network.add(convolutional.Convolution2D(
				nb_filter=params["filters_per_layer"],
				nb_row=filter_width,
				nb_col=filter_width,
				init='uniform',
				activation='relu',
				border_mode='same'))

		# the last layer maps each <filters_per_layer> featuer to a number
		network.add(convolutional.Convolution2D(
			nb_filter=1,
			nb_row=1,
			nb_col=1,
			init='uniform',
			border_mode='same'))
		# reshape output to be board x board
		network.add(Flatten())
		# softmax makes it into a probability distribution
		network.add(Activation('softmax'))

		return network

	@staticmethod
	def load_model(json_file):
		"""create a new CNNPolicy object from the architecture specified in json_file
		"""
		with open(json_file, 'r') as f:
			object_specs = json.load(f)

		# Create object; may be a subclass of CNNPolicy saved in specs['class']
		policy_class = object_specs.get('class', 'CNNPolicy')
		if policy_class == 'CNNPolicy':
			new_policy = CNNPolicy(object_specs['feature_list'])
		elif policy_class == 'ResnetPolicy':
			new_policy = ResnetPolicy(object_specs['feature_list'])

		new_policy.model = model_from_json(object_specs['keras_model'])
		if 'weights_file' in object_specs:
			new_policy.model.load_weights(object_specs['weights_file'])
		new_policy.forward = new_policy._model_forward()
		return new_policy

	def save_model(self, json_file, weights_file=None):
		"""write the network model and preprocessing features to the specified file

		If a weights_file (.hdf5 extension) is also specified, model weights are also
		saved to that file and will be reloaded automatically in a call to load_model
		"""
		# this looks odd because we are serializing a model with json as a string
		# then making that the value of an object which is then serialized as
		# json again.
		# It's not as crazy as it looks. A CNNPolicy has 2 moving parts - the
		# feature preprocessing and the neural net, each of which gets a top-level
		# entry in the saved file. Keras just happens to serialize models with JSON
		# as well. Note how this format makes load_model fairly clean as well.
		object_specs = {
			'class': self.__class__.__name__,
			'keras_model': self.model.to_json(),
			'feature_list': self.preprocessor.feature_list
		}
		if weights_file is not None:
			self.model.save_weights(weights_file)
			object_specs['weights_file'] = weights_file
		# use the json module to write object_specs to file
		with open(json_file, 'w') as f:
			json.dump(object_specs, f)


class ResnetPolicy(CNNPolicy):
	"""Residual network architecture as per He at al. 2015
	"""
	@staticmethod
	def create_network(**kwargs):
		"""construct a convolutional neural network with Resnet-style skip connections.
		Arguments are the same as with the default CNNPolicy network, except the default
		number of layers is 20 plus a new n_skip parameter

		Keword Arguments:
		- input_dim:         	depth of features to be processed by first layer (no default)
		- board:             	width of the go board to be processed (default 19)
		- filters_per_layer: 	number of filters used on every layer (default 128)
		- layers:            	number of convolutional steps (default 20)
		- filter_width_K:    	(where K is between 1 and <layers>) width of filter on
								layer K (default 3 except 1st layer which defaults to 5).
								Must be odd.
		- n_skip_K:             (where K is as in filter_width_K) number of convolutional
								layers to skip with the linear path starting at K. Only valid
								at K >= 1. (Each layer defaults to 1)

		Note that n_skip_1=s means that the next valid value of n_skip_* is 3

		A diagram may help explain (numbers indicate layer):

			1        2         3              4         5         6
		I--C -- R -- C -- R -- C -- M -- R -- C -- R -- C -- R -- C -- M  ...  M  -- R -- F -- O
			\______________________/ \________________________________/ \ ... /
				[n_skip_1 = 2]               [n_skip_3 = 3]

		I - input
		R - ReLU
		C - Conv2D
		F - Flatten
		O - output
		M - merge

		The input is always passed through a Conv2D layer, the output of which layer is counted as '1'.
		Each subsequent [R -- C] block is counted as one 'layer'. The 'merge' layer isn't counted; hence
		if n_skip_1 is 2, the next valid skip parameter is n_skip_3, which will start at the output
		of the merge
		"""
		defaults = {
			"board": 19,
			"filters_per_layer": 128,
			"layers": 20,
			"filter_width_1": 5
		}
		# copy defaults, but override with anything in kwargs
		params = defaults
		params.update(kwargs)

		# create the network using Keras' functional API,
		# since this isn't 'Sequential'
		model_input = Input(shape=(params["input_dim"], params["board"], params["board"]))

		# create first layer
		convolution_path = convolutional.Convolution2D(
			input_shape=(),
			nb_filter=params["filters_per_layer"],
			nb_row=params["filter_width_1"],
			nb_col=params["filter_width_1"],
			init='uniform',
			activation='linear',  # relu activations done inside resnet modules
			border_mode='same')(model_input)

		def add_resnet_unit(path, K, **params):
			"""Add a resnet unit to path starting at layer 'K',
			adding as many (ReLU + Conv2D) modules as specified by n_skip_K

			Returns new path and next layer index, i.e. K + n_skip_K, in a tuple
			"""
			# loosely based on https://github.com/keunwoochoi/residual_block_keras
			# (see also keras docs here: http://keras.io/getting-started/functional-api-guide/#all-models-are-callable-just-like-layers)

			block_input = path
			# use n_skip_K if it is there, default to 1
			skip_key = "n_skip_%d" % K
			n_skip = params.get(skip_key, 1)
			for i in range(n_skip):
				layer = K + i
				# add ReLU
				path = Activation('relu')(path)
				# use filter_width_K if it is there, otherwise use 3
				filter_key = "filter_width_%d" % layer
				filter_width = params.get(filter_key, 3)
				# add Conv2D
				path = convolutional.Convolution2D(
					nb_filter=params["filters_per_layer"],
					nb_row=filter_width,
					nb_col=filter_width,
					init='uniform',
					activation='linear',
					border_mode='same')(path)
			# Merge 'input layer' with the path
			path = merge([block_input, path], mode='sum')
			return path, K + n_skip

		# create all other layers
		layer = 1
		while layer < params['layers']:
			convolution_path, layer = add_resnet_unit(convolution_path, layer, **params)
		if layer > params['layers']:
			print "Due to skipping, ended with {} layers instead of {}".format(layer, params['layers'])

		# since each layer's activation was linear, need one more ReLu
		convolution_path = Activation('relu')(convolution_path)

		# the last layer maps each <filters_per_layer> featuer to a number
		convolution_path = convolutional.Convolution2D(
			nb_filter=1,
			nb_row=1,
			nb_col=1,
			init='uniform',
			border_mode='same')(convolution_path)
		# flatten output
		network_output = Flatten()(convolution_path)
		# softmax makes it into a probability distribution
		network_output = Activation('softmax')(network_output)

		return Model(input=[model_input], output=[network_output])
