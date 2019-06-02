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

def file_iterator(dirpath):
    """
    디렉터리에 있는 파일을 탐색하는 제너레이터
    """
    for filename in os.listdir(dirpath):
        yield os.path.join(dirpath, filename)

def step1_loadmodel(modelDirPath):
    '''
    학습 모델 불러오기
    '''
    for filename in os.listdir(modelDirPath):
        name, ext = os.path.splitext(filename)
        if ext == '.pkl':
            model[name] = joblib.load(os.path.join(modelDirPath, filename)) 

def step2_predict():
    '''
    디렉터리에 있는 샘플에 대해서
    특성 추출 + 특성 공학
    '''
    numberOfCPU =multiprocessing.cpu_count()
    pool = multiprocessing.Pool(numberOfCPU)
    end = len(next(os.walk(args.datadir))[2])

    mylogger.info("특성 추출 시작")
    for x in tqdm.tqdm(pool.imap(ember.predict_preprocess , file_iterator(args.datadir)), total=end):
        X = pd.DataFrame([x])
        
        for key, value in model.items():
            r = value.predict(X)

def main():
    step1_loadmodel(args.modelpathdir)
    step2_predict()

if __name__ == "__main__":
    main()