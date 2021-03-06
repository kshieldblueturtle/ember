# -*- coding: utf-8 -*-
import os
import sys
import tqdm
import argparse
import numpy as np
import pandas as pd
import lightgbm as lgb
from collections import OrderedDict
import multiprocessing
import logging
from src import features, ember
from sklearn.externals import joblib 
import jsonlines
import csv

# 로거 설정
mylogger = logging.getLogger(__name__)
mylogger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(formatter)

# 파일 핸들러
fh = logging.FileHandler('predict_error.log', 'w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

mylogger.addHandler(fh)
mylogger.addHandler(sh)

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--modelpathdir", type=str, required=True, help="trained model path")
parser.add_argument("-d", "--datadir", type=str, help="Directory for predicting dataSets", required=True)
parser.add_argument("-o", "--output", type=str, help="output directory", required=True)
args = parser.parse_args()

if not os.path.exists(args.modelpathdir):
    parser.error("ember model {} does not exist".format(args.modelpathdir))
if not os.path.exists(args.datadir):
    parser.error("ember model {} does not exist".format(args.datadir))
if not os.path.exists(args.output):
    os.mkdir(args.output)

# 학습 모델
model = {}
feature_importance = {}

def file_iterator(dirpath):
    """
    디렉터리에 있는 파일을 탐색하는 제너레이터
    """
    for filename in os.listdir(dirpath):
        yield os.path.join(dirpath, filename)

def step1_loadmodel(modelDirPath):
    '''
    학습 모델 불러오기
    학습 중요도 불로오기
    '''
    for filename in os.listdir(modelDirPath):
        name, ext = os.path.splitext(filename)
        # 모델 불러오기
        if ext == '.pkl':
            model[name] = joblib.load(os.path.join(modelDirPath, filename)) 
      
    with jsonlines.open(os.path.join(modelDirPath, 'features_importance.jsonl')) as reader:
        for obj in reader:
            for key, value in obj.items():
                feature_importance[key] = value

def step2_predict(target):
    '''    
    디렉터리에 있는 샘플에 대해서
    특성 추출 + 특성 공학
    '''
    numberOfCPU =multiprocessing.cpu_count()
    pool = multiprocessing.Pool(numberOfCPU)
    end = len(next(os.walk(target))[2])
    lock = multiprocessing.Lock()
    
    with open(os.path.join(args.output, 'predict_result.csv'), 'w') as f:
        writer = csv.writer(f, lineterminator='\n')
        
        for x, filepath in tqdm.tqdm(pool.imap(ember.predict_preprocess , file_iterator(target)), total=end):
            X = pd.DataFrame([x])
            filename = filepath.split('\\')[-1]

            # key: 모델 이름, value: 모델 객체
            for key, value in model.items():
                if len(feature_importance.get(key)) != 0:
                    new_X = X[feature_importance.get(key)]
                    predict_score = value.predict(new_X)
                else:
                    predict_score = value.predict(X)

                lock.acquire()
                writer.writerow([filename, predict_score[0], key])
                lock.release()

def step3(target):
    '''
    파일 검사(단일 타겟)
    '''
    # target = r'C:\\Users\\sungwook\\Downloads\\EppManifest.dll'
    
    x, filepath = ember.predict_preprocess(target)
    X = pd.DataFrame([x])

    # key: 모델 이름, value: 모델 객체
    for key, value in model.items():
        if len(feature_importance.get(key)) != 0:
            pass
            new_X = X[feature_importance.get(key)]
            predict_score = value.predict(new_X)
        else:
            predict_score = value.predict(X)

        print('{}:{}'.format(key, predict_score[0]))

def main():
    step1_loadmodel(args.modelpathdir)
    if os.path.isdir(args.datadir):
        step2_predict(args.datadir) # 디렉터리 예측(멀티 프로세싱)
    else:
        step3(args.datadir) # 단일 타겟 예측

if __name__ == "__main__":
    main()