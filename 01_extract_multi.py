# -*- coding: utf-8 -*-
"""
This python module refer to Ember Porject(https://github.com/endgameinc/ember.git)
"""
import os
import argparse
import sys
from src import features, ember
import tqdm
import jsonlines
import pandas as pd
import multiprocessing
import logging
import csv

# 로거 설정
mylogger = logging.getLogger(__name__)
mylogger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
sh.setFormatter(formatter)

# 파일 핸들러
fh = logging.FileHandler('features_error.log', 'w')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)

mylogger.addHandler(fh)
mylogger.addHandler(sh)

# argparse 설정
parser = argparse.ArgumentParser()
parser.add_argument("-d", "--dataset", help="Dataset path", required=True)
parser.add_argument("-o", "--output", help="output path", required=True)
parser.add_argument("-c", "--csv", help="dataset label", required=True)
args = parser.parse_args()

if not os.path.exists(args.dataset):
    parser.error("TrainSet {} does not exist".format(args.dataset))    
if not os.path.exists(args.csv):
    parser.error("TrainSet label {} does not exist".format(args.csv))
if not os.path.exists(args.output):        
    os.mkdir(args.output)

# 트레이닝 셋 라벨파일 읽기
data = pd.read_csv(args.csv, names=['hash', 'y'])

def ExtractLabel(filename):
    '''
    샘플의 라벨 추출
    리턴: 해당 샘플의 라벨
    '''
    return data[data.hash==filename].values[0][1]

def file_iterator():
    """
    디렉터리에 있는 파일을 탐색하는 제너레이터
    """
    for filename in os.listdir(args.dataset):
        yield filename

def extract_features(filename):
    """
    멀티 프로세싱으로 특성 추출
    """
    extractor = features.PEFeatureExtractor()
    fullpath = os.path.join(os.path.join(args.dataset, filename))
    try:
        feature = extractor.raw_features(fullpath)
        feature.update({"sha256": filename}) # sample name(hash)
        feature.update({"label" : ExtractLabel(filename)}) #label
    except KeyboardInterrupt:        
        sys.exit()
    except Exception as e:
        print('{}:{}'.format(filename, e))
        mylogger.debug("{}: {}".format(filename, e))
        return None

    return feature
       
def extract_unpack(args):
    """
    인자 전달
    """
    return extract_features(*args)

def extract_subset():
    """
    멀티 프로세싱
    """
    numberOfcpu = multiprocessing.cpu_count() - 1
    pool = multiprocessing.Pool(numberOfcpu)
    lock = multiprocessing.Lock()
    end = len(next(os.walk(args.dataset))[2])
    
    extractor_iterator = ((filename) for idx, filename in enumerate(file_iterator()))
   
    with jsonlines.open(os.path.join(args.output, "features.jsonl"), 'w') as f:
        for x in tqdm.tqdm(pool.imap_unordered(extract_features, extractor_iterator), total=end):
            if not x:
                continue
            lock.acquire()
            f.write(x)                
            lock.release()
            
    pool.close()
    pool.join()

def main():
    # 특성 추출
    extract_subset()
    ember.create_metadata(args.output)
    
if __name__=='__main__':
    main()