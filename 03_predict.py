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
# parser.add_argument("-m", "--modelpath", type=str, required=True, help="trained model path")
parser.add_argument("-d", "--datadir", type=str, help="Directory for predicting dataSets", required=True)
parser.add_argument("-o", "--output", type=str, help="output directory", required=True)
args = parser.parse_args()

# if not os.path.exists(args.modelpath):
#     parser.error("ember model {} does not exist".format(args.modelpath))
if not os.path.exists(args.datadir):
    parser.error("ember model {} does not exist".format(args.datadir))
if not os.path.exists(args.output):
    os.mkdir(args.output)

# model_path = os.path.join(args.modelpath, "model.txt")
# lgbm_model = lgb.Booster(model_file=model_path)

def file_iterator(dirpath):
    """
    디렉터리에 있는 파일을 탐색하는 제너레이터
    """
    for filename in os.listdir(dirpath):
        yield os.path.join(dirpath, filename)

def extract_features(filename):
    """
    멀티 프로세싱으로 특성 추출
    """
    extractor = features.PEFeatureExtractor()
    fullpath = os.path.join(os.path.join(args.dataset, filename))
    try:
        feature = extractor.raw_features(fullpath)
        feature.update({"sha256": filename}) # sample name(hash)
    except KeyboardInterrupt:
        sys.exit()
    except Exception as e:
        mylogger.debug("{}: {}".format(filename, e))
        return None

    return feature

def step1():
    '''
    디렉터리에 있는 샘플
    '''
    numberOfCPU =multiprocessing.cpu_count()
    pool = multiprocessing.Pool(numberOfCPU)
    end = len( next(os.walk(args.datadir))[2])
    mylogger.info("특성 추출 시작")
    for x in  tqdm.tqdm(pool.imap(ember.predict_preprocess , file_iterator(args.datadir)), total=end):
        print(x)

def main():
    step1()

if __name__ == "__main__":
    main()