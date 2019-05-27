# -*- coding: utf-8 -*-

import os
import json
import tqdm
import numpy as np
import pandas as pd
import lightgbm as lgb
import multiprocessing
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.model_selection import train_test_split
from .features import PEFeatureExtractor
from sklearn.metrics import accuracy_score
import tqdm
import warnings
import sys
import timeit
warnings.simplefilter(action='ignore', category=FutureWarning)

import logging
# logger 설정
my_logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
my_logger.addHandler(sh)
my_logger.setLevel(logging.DEBUG)

numberoftrainsetfile = 1
numberoftrainsets = 1

def raw_feature_iterator(file_paths):
    """
    Yield raw feature strings from the inputed file paths
    """
    for path in file_paths:
        with open(path, "r") as fin:
            for line in fin:
                yield line


def vectorize(irow, raw_features_string, X_path, y_path, nrows):
    """
    Vectorize a single sample of raw features and write to a large numpy file
    """
    extractor = PEFeatureExtractor()
    raw_features = json.loads(raw_features_string)
    feature_vector = extractor.process_raw_features(raw_features)

    y = np.memmap(y_path, dtype=np.float32, mode="r+", shape=nrows)
    y[irow] = raw_features["label"]

    X = np.memmap(X_path, dtype=np.float32, mode="r+", shape=(nrows, extractor.dim))
    X[irow] = feature_vector


def vectorize_unpack(args):
    """
    Pass through function for unpacking vectorize arguments
    """
    return vectorize(*args)


def vectorize_subset(X_path, y_path, raw_feature_paths, nrows):
    """
    Vectorize a subset of data and write it to disk
    """
    # Create space on disk to write features to
    extractor = PEFeatureExtractor()
    X = np.memmap(X_path, dtype=np.float32, mode="w+", shape=(nrows, extractor.dim))
    y = np.memmap(y_path, dtype=np.float32, mode="w+", shape=nrows)
    del X, y

    # Distribute the vectorization work
    pool = multiprocessing.Pool()
    argument_iterator = ((irow, raw_features_string, X_path, y_path, nrows)
                         for irow, raw_features_string in enumerate(raw_feature_iterator(raw_feature_paths)))
    for _ in tqdm.tqdm(pool.imap_unordered(vectorize_unpack, argument_iterator), total=nrows):
        pass


def create_vectorized_features(data_dir, rows):
    print("Vectorizing Dataset set")
    X_path = os.path.join(data_dir, "X.dat")
    y_path = os.path.join(data_dir, "y.dat")
    raw_feature_paths = [os.path.join(data_dir, "features.jsonl")]
    vectorize_subset(X_path, y_path, raw_feature_paths, rows)

def read_vectorized_features(data_dir, rows):
    ndim = PEFeatureExtractor.dim

    X_path = os.path.join(data_dir, "X.dat")
    y_path = os.path.join(data_dir, "y.dat")
    X = np.memmap(X_path, dtype=np.float32, mode="r", shape=(rows, ndim))
    y = np.memmap(y_path, dtype=np.float32, mode="r", shape=rows)

    return X, y

def read_metadata_record(raw_features_string):
    """
    Decode a raw features stringa and return the metadata fields
    """
    full_metadata = json.loads(raw_features_string)
    return {"sha256": full_metadata["sha256"], "appeared": full_metadata["appeared"], "label": full_metadata["label"]}


def create_metadata(data_dir):
    """
    Write metadata to a csv file and return its dataframe
    """
    pool = multiprocessing.Pool()
    raw_feature_paths = [os.path.join(data_dir, "features.jsonl")]
    records = list(pool.imap(read_metadata_record, raw_feature_iterator(raw_feature_paths)))
    records = [dict(record, **{"subset": "train"}) for record in records]

    metadf = pd.DataFrame(records)[["sha256", "appeared", "subset", "label"]]
    metadf.to_csv(os.path.join(data_dir, "metadata.csv"))
    print("\n[Done] create_metadata\n")
    
    return metadf

def read_metadata(data_dir):
    """
    Read an already created metadata file and return its dataframe
    """
    return pd.read_csv(os.path.join(data_dir, "metadata.csv"), index_col=0)

def get_predictAccuracy(prediction, y_train):
    '''
    교차검증 정확도 리턴
    '''
    return accuracy_score(prediction, y_train)

def _train(model, X_train, X_test, y_train, y_test):
    '''
    학습
    '''
    model = model.fit(X_train, y_train)
    
    # 교차 검증 테스트
    prediction = model.predict(X_test)
    my_logger.info("{} 교차 검증 결과 : {}".format(model.__class__.__name__, get_predictAccuracy(prediction, y_test)))

def train_model(data_dir, rows):
    """
    학습 준비 및 학습하는 함수 호출
    """
    # 벡터화
    X, y = read_vectorized_features(data_dir, rows)

    # 모델
    models = [
        KNeighborsClassifier(3),
        #SVC(kernel="linear", C=0.025), 
        #SVC(gamma=2, C=1),
        #GaussianProcessClassifier(1.0 * RBF(1.0)),
        DecisionTreeClassifier(max_depth=5),
        RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
        MLPClassifier(alpha=1, max_iter=1000),
        AdaBoostClassifier(),
        GaussianNB(),
        QuadraticDiscriminantAnalysis() 
    ]

    # 교차 검증을 위한 데이터셋 나누기
    X_train, X_test, y_train, y_test = train_test_split(X, y)

    try:
        training_start = timeit.default_timer()
        for model in models:        
            # 실행시간 코드:
            # #https://juliahwang.kr/algorism/python/2017/09/12/%ED%8C%8C%EC%9D%B4%EC%8D%AC%EC%BD%94%EB%93%9C%EC%8B%A4%ED%96%89%EC%8B%9C%EA%B0%84%EC%B8%A1%EC%A0%95%ED%95%98%EA%B8%B0.html
            start = timeit.default_timer()
            _train(model, X_train, X_test, y_train, y_test)
            end = timeit.default_timer()            
            my_logger.info('[학습 소요]: %0.2f' % (end - start))
        training_end = timeit.default_timer()
        my_logger.info('[총 학습 소요]: %0.2f' % (training_end - training_start))

    except KeyboardInterrupt: # 키보드 인터럽트 처리
	    sys.exit(-1)

    #train
    #lgbm_dataset = lgb.Dataset(X, y)
    #lgbm_model = lgb.train({"application": "binary"}, lgbm_dataset)

    #return lgbm_model

def predict_sample(lgbm_model, file_data):
    """
    Predict a PE file with an LightGBM model
    """
    extractor = PEFeatureExtractor()
    features = np.array(extractor.feature_vector(file_data), dtype=np.float32)
    return lgbm_model.predict([features])[0]