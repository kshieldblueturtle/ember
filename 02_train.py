import argparse
import os
from src import ember
import sys
import jsonlines

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--datadir", help="Features Directory", type=str)
	parser.add_argument("-o", "--output", help="Output Directory", type=str)
	args = parser.parse_args()

	#Get total lines from feature.jsonl
	rows = 0
	with jsonlines.open(os.path.join(args.datadir, 'features.jsonl')) as reader:
		for obj in reader.iter(type=dict, skip_invalid=True):
			rows += 1

	ember.create_vectorized_features(args.datadir, rows)

	# Train and save model
	print("Training LightGBM model")
	lgbm_model = ember.train_model(args.datadir, rows)
	lgbm_model.save_model(os.path.join(args.output, "model.txt")) 

if __name__=='__main__':
	main()