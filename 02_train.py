# -*- coding: utf-8 -*-
import argparse
import os
from src import ember
import sys
import jsonlines
from tabulate import tabulate
from sklearn.externals import joblib
import operator

# argparse 설정
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--datadir", help="Features Directory", type=str)
parser.add_argument("-o", "--output", help="Output Directory", type=str)
parser.add_argument("-s", "--score", help="Output Directory", type=str)
args = parser.parse_args()

def remove_model(modelDirPath):
	'''
    기존에 있던 학습 모델 삭제
    '''
	for filename in os.listdir(modelDirPath):
		name, ext = os.path.splitext(filename)
		if ext == '.pkl':
			os.remove(os.path.join(modelDirPath, filename))

def save_model(train_result):
	'''
	모델과 특성 중요도 저장
	'''
	with jsonlines.open(os.path.join(args.output, 'features_importance.jsonl'), 'w') as f:
		for key, value in train_result.items():
			modelname = key
			modelObject =  value['model']
			featurs_names = value['feature_names']
			
			result = {}			
			result[modelname] = featurs_names
			#특성 중요도 저장
			f.write(result)

			# for key, value in model_dict.items():
			modelfilenameTosave = os.path.join(args.output, key) + '.pkl'
			joblib.dump(modelObject, modelfilenameTosave) 

def main():
	# jsonl파일의 행(row)개수 세기(학습할 샘플의 수)
	rows = 0
	with jsonlines.open(os.path.join(args.datadir, 'features.jsonl')) as reader:
		for obj in reader.iter(type=dict, skip_invalid=True):
			rows += 1
	
	# 기존에 있떤 모델 삭제
	remove_model(args.output)

	# 학습
	train_result =  ember.train_model(args.datadir, rows)

	# # 화면에 출력
	columns = ['model', '1st', '1. kfold', '2nd', '2. kfold', 'best score']
	scoreTable = []
	for key, value in train_result.items():
		scoreTable.append(value['score'])
	scoreTable.sort(key=operator.itemgetter(5), reverse=True)
	
	with open(os.path.join(args.output, args.score), 'w') as f:
		prettyScoreTable = tabulate(scoreTable, headers=columns)
		f.write(prettyScoreTable)		
		print()
		print('======================== 점수가 가장 높은 모델의 평가 점수 ========================')
		print(scoreTable[0])
		print()
		print('======================== 모든 모델의 평가 점수 ========================')
		print(prettyScoreTable)
		print()
		
	# # 학습 모델 저장
	save_model(train_result)

if __name__=='__main__':
	main()