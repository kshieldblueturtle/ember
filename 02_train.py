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

	# jsonl파일의 행(row)개수 세기(학습할 샘플의 수)
	rows = 0
	with jsonlines.open(os.path.join(args.datadir, 'features.jsonl')) as reader:
		for obj in reader.iter(type=dict, skip_invalid=True):
			rows += 1

	# 벡터화
	ember.create_vectorized_features(args.datadir, rows)
	
	# 학습
	ember.train_model(args.datadir, rows)
	# print("Training LightGBM model")
	# lgbm_model = ember.train_model(args.datadir, rows)
	# lgbm_model.save_model(os.path.join(args.output, "model.txt")) 


if __name__=='__main__':
	main()