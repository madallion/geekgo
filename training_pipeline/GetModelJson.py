from AlphaGo.models.policy import CNNPolicy
arch = {'filters_per_layer': 128, 'layers': 12} # args to CNNPolicy.create_network()
feature_list = [
			"board",
			"ones",
			"turns_since",
			"liberties",
			"capture_size",
			"self_atari_size",
			"liberties_after",
			# "ladder_capture",
			# "ladder_escape",
			"sensibleness",
			"zeros"]
policy = CNNPolicy(feature_list, **arch)
policy.save_model('all_feat_model.json')

