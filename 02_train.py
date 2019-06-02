import argparse
import os
from src import ember
import sys
import jsonlines
from tabulate import tabulate
from sklearn.externals import joblib

def remove_model(modelDirPath):
	'''
    기존에 있던 학습 모델 삭제
    '''
	for filename in os.listdir(modelDirPath):
		name, ext = os.path.splitext(filename)
		if ext == '.pkl':
			os.remove(os.path.join(modelDirPath, filename))

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("-d", "--datadir", help="Features Directory", type=str)
	parser.add_argument("-o", "--output", help="Output Directory", type=str)
	parser.add_argument("-s", "--score", help="Output Directory", type=str)
	args = parser.parse_args()

	# jsonl파일의 행(row)개수 세기(학습할 샘플의 수)
	rows = 0
	with jsonlines.open(os.path.join(args.datadir, 'features.jsonl')) as reader:
		for obj in reader.iter(type=dict, skip_invalid=True):
			rows += 1
	
	# 기존에 있떤 모델 삭제
	remove_model(args.output)

	# 학습
	scoreTable, model_dict =  ember.train_model(args.datadir, rows)

	# 화면에 출력
	columns = ['model', '1st', '1. kfold', '2nd', '2. kfold', 'best score']

	with open(os.path.join(args.output, args.score), 'w') as f:
		prettyScoreTable = tabulate(scoreTable, headers=columns)
		f.write(prettyScoreTable)		
		print()
		print('======================== 점수가 가장 높은 모델 ========================')
		print(scoreTable[0])
		print()
		print(prettyScoreTable)
		print()
	
	# 학습 모델 저장
	for key, value in model_dict.items():
		filename = os.path.join(args.output, key) + '.pkl'
		joblib.dump(value, filename) 

if __name__=='__main__':
	main()