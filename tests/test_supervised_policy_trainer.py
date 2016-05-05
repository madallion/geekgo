import os
from AlphaGo.training.supervised_policy_trainer import run_training
import unittest


class TestSupervisedPolicyTrainer(unittest.TestCase):
	def testTrain(self):
		model = 'D:\\ps\\club\\Go\\models\\all_feat_model.json'
		data = 'D:\ps\club\Go\\.tmp.testing.h5'
		output = 'tests/test_data/.tmp.training/'
		args = [model, data, output, '--epochs', '1', '--epoch-length', '20']
		run_training(args)

		#os.remove(os.path.join(output, 'metadata.json'))
		#os.remove(os.path.join(output, 'shuffle.npz'))
		#os.remove(os.path.join(output, 'weights.00000.hdf5'))
		#os.rmdir(output)

if __name__ == '__main__':
	unittest.main()
