# -*- coding: utf-8 -*-
import os
import json
import tqdm
import math
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
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier, GradientBoostingClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from .features import PEFeatureExtractor
from sklearn.metrics import accuracy_score
import tqdm
import warnings
import sys
import timeit
import operator
import csv
from tabulate import tabulate
warnings.simplefilter(action='ignore', category=FutureWarning)

import logging
# logger 설정
my_logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(formatter)
my_logger.addHandler(sh)
my_logger.setLevel(logging.DEBUG)

def raw_feature_iterator(file_paths):
    """
    Yield raw feature strings from the inputed file paths
    """
    for path in file_paths:
        with open(path, "r") as fin:
            for line in fin:
                yield line

def read_metadata_record(raw_features_string):
    """
    json을 읽어서 dict 리턴
    """
    full_metadata = json.loads(raw_features_string)
    
    meatadata = {}
    for rootkey, rootvalue in full_metadata.items():
        if isinstance(rootvalue, dict):
            for subkey, subvalue in rootvalue.items():
                meatadata[subkey] = subvalue
        else:
            meatadata[rootkey] = rootvalue 

    return meatadata

def create_metadata(data_dir):
    """
    json을 csv로 변환
    """
    pool = multiprocessing.Pool()
    raw_feature_paths = [os.path.join(data_dir, "features.jsonl")]
    records = list(pool.imap(read_metadata_record, raw_feature_iterator(raw_feature_paths)))
    
    metadf = pd.DataFrame(records)
    metadf.to_csv(os.path.join(data_dir, "features.csv"), index=False)
    
    return metadf

def preprocess_features(data_dir):
    """
    json을 csv로 변환
    """
    pool = multiprocessing.Pool()
    raw_feature_paths = [os.path.join(data_dir, "features.jsonl")]
    records = list(pool.imap(read_features_record, raw_feature_iterator(raw_feature_paths)))

    metadf = pd.DataFrame(records)
    return metadf

def read_features_record(raw_features_string):
    """
    특성 공학
    """
    extractor = PEFeatureExtractor()
    raw_features = json.loads(raw_features_string)
    
    # 특성 공학
    feature_vector = extractor.process_raw_features(raw_features)
    
    return feature_vector

def read_metadata(data_dir):
    """
    csv 불러오기
    """
    return pd.read_csv(os.path.join(data_dir, "metadata.csv"), index_col=0)

def _importance(model, X, y, mode):
    '''
    모델에서 중요하게 생각하는 상위 특성을 선택해서 다시 학습
    '''
    k_fold_threshold = 3
    best_score = 0.0
    result = []
    columns1 = model.__class__.__name__
    best_model = None # 가장 성능이 높은 모델을 저장하는 변수, 리턴 값

    print()
    my_logger.info("특성 중요도 실험 시작-- 실험모델 {}".format(model.__class__.__name__))
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=23)
    
    model_before = model.fit(X_train, y_train)
    columns2 = model_before.score(X_test, y_test)
    best_score = columns2
    best_model = model_before # 모델 비교 1
    my_logger.info("특징 랭킹 선택 전 : {:.3f}".format(columns2))

    columns3 = cross_val_score(model_before, X, y, cv=k_fold_threshold).mean()
    my_logger.info("특징 랭킹 선택 전 K-fold : {:.4f}".format(columns3))
    if columns3 > best_score:
        best_score = columns3

    importance = getattr(model_before, "feature_importances_", None)
    # 특성 중요도를 추출하는 함수가 없으면 종료
    if importance is None:
        columns4 = '0.0'
        columns5 = '0.0'
        top = 0
        top_feature_name = []

    else:
        importance_tag = dict(zip(X.columns, importance))
        # 정렬
        sorted_importance = dict(sorted(importance_tag.items(), key=operator.itemgetter(1), reverse=True))

        # 특성 중요도 전부 출력 mode가 1일대
        if mode == 1:
            for key, value in sorted_importance.items():
                print('{}: {}'.format(key, value))

        # 상위 특성 선택
        # print('특성 개수: {}'.format(len(sorted_importance)))

        top = int(math.ceil(len(sorted_importance) * 0.3))
        top_feature_name = list(sorted_importance.keys())[:top]
        # X_train, X_test, y_train, y_test = train_test_split(X[top4_feature_name], y, test_size=0.3, random_state=42)
        
        new_train_X = X_train[top_feature_name]
        new_test_X = X_test[top_feature_name]
        after_model = model.fit(new_train_X, y_train)
        columns4 = after_model.score(new_test_X, y_test)
        if columns4 > best_score:
            best_score = columns4
            best_model = after_model
        my_logger.info("특징 랭킹 선택 후 : {:.4f}".format(columns4))

        # k-fold
        new_X = X[top_feature_name]
        columns5 = cross_val_score(after_model, new_X, y, cv=k_fold_threshold).mean()
        my_logger.info("특징 랭킹 선택 후 K-fold : {:.4f}".format(columns5))
        if columns5 > best_score:
            best_score = columns5
            best_model = after_model
    
    columns6 = best_score
    result.append(columns1)
    result.append(round(np.float(columns2), 3))
    result.append(round(np.float(columns3), 3))
    result.append(round(np.float(columns4), 3))
    result.append(round(np.float(columns5), 3))
    result.append(round(np.float(columns6), 3))
    
    socre_information = {
        'score': result, 
        'model': best_model,
        'numberOffeatures': top,
        'feature_names': top_feature_name
    }

    return socre_information

def train_model(data_dir, rows):
    """
    학습 준비 및 학습하는 함수 호출
    row: 특성 추출한 샘플의 수
    """
    # 특성 공학
    df = preprocess_features(data_dir)
    X = df.drop(['label'], axis=1)
    y = df['label']

    # 모델
    models = [
        KNeighborsClassifier(3),
        # SVC(kernel="linear", C=0.025), 
        # SVC(gamma=2, C=1),
        # GaussianProcessClassifier(1.0 * RBF(1.0)),
        DecisionTreeClassifier(max_depth=5),
        RandomForestClassifier(n_estimators=50, random_state=0, 
                         oob_score = True,
                         max_depth = 16, 
                         max_features = 'sqrt'),
        MLPClassifier(alpha=1, max_iter=1000),
        AdaBoostClassifier(),
        GaussianNB(),
        QuadraticDiscriminantAnalysis(),
        GradientBoostingClassifier(learning_rate=0.15, max_depth=16, max_features='sqrt', n_estimators=70)
    ]

    testmodels = [
        KNeighborsClassifier(3),
        GradientBoostingClassifier()
    ]
    
    # 모델 학습 & 평가
    result = {}
    for idx, model in enumerate(models):
        score = _importance(model, X, y, 0)
        result[model.__class__.__name__] = score

    return result

def predict_preprocess(filepath):
    extractor = PEFeatureExtractor()
    feature_vector = extractor.feature_vector(filepath)

    return feature_vector, filepath

'''
테스트용 모델 교차 검증 함수 -> 테스트용
'''

# def cross_val(models, X, y):
#     '''
#     cross_val을 사용한 일반 k-fold
#     현재 사용하지 않음 -> 테스트용
#     '''
#     # 교차 검증을 위한 데이터셋 나누기
#     X_train, X_test, y_train, y_test = cross_val_score(X, y)

#     try:
#         training_start = timeit.default_timer()
#         for model in models:        
#             # 실행시간코드:
#             # #https://juliahwang.kr/algorism/python/2017/09/12/%ED%8C%8C%EC%9D%B4%EC%8D%AC%EC%BD%94%EB%93%9C%EC%8B%A4%ED%96%89%EC%8B%9C%EA%B0%84%EC%B8%A1%EC%A0%95%ED%95%98%EA%B8%B0.html
#             start = timeit.default_timer()
#             _train(model, X_train, X_test, y_train, y_test)
#             end = timeit.default_timer()            
#             my_logger.info('[학습 소요]: %0.2f' % (end - start))
#         training_end = timeit.default_timer()
#         my_logger.info('[총 학습 소요]: %0.2f' % (training_end - training_start))

#     except KeyboardInterrupt: # 키보드 인터럽트 처리
# 	    sys.exit(-1)

# def skfold(models, X, y):
#     '''
#     계층적 K-fold
#     현재 사용하지 않음->테스트용
#     '''
#     skfold = StratifiedKFold(n_splits=5, shuffle=True)
#     training_start = timeit.default_timer()

#     for model in models:
#         my_logger.info("모델 {}의 StratifiedKfold 검증 결과".format(model.__class__.__name__))

#         for idx, (train_indx, test_index) in enumerate(skfold.split(X, y)):
#             X_train, X_test = X[train_indx], X[test_index]
#             y_train, y_test = y[train_indx], y[test_index]

#             # 훈련 
#             start = timeit.default_timer()
#             r = model.fit(X_train, y_train)
#             end = timeit.default_timer() 
#             my_logger.info("훈련 소요 %.2f" % (end - start))
#             score = r.predict(X_test)
            
#             # 교차 검증 결과
#             _accuracy_score = accuracy_score(score, y_test)
#             my_logger.info("{}회 결과 {}".format(idx+1, _accuracy_score))
#             my_logger.info("========================================")
#         my_logger.info('')

#     training_end = timeit.default_timer()
#     my_logger.info("========================================")
#     my_logger.info("========================================")
#     my_logger.info("총 훈련 시간 : %.2f" %(training_end - training_start))
#     my_logger.info("========================================")
#     my_logger.info("========================================")

# def _SelectFromModel(models, X, y):
#     """
#     sklearn SelectFromModel
#     현재 사용하지 않음->테스트용
#     """
#     X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
#     my_logger.debug("type: {}".format(type(X_train)))
    
#     for model in models:
#         my_logger.info("{}모델 SelectFromModel 측정 시장".format(model.__class__.__name__))
#         r = model.fit(X_train, y_train)
#         my_logger.info("전: {:.3f}".format(r.score(X_test, y_test)))

#         # SelectFromModel 선택
#         model_reduced = SelectFromModel(r, prefit=True)
#         X_train_new = model_reduced.transform(X_train)
#         X_test_new = model_reduced.transform(X_test)

#         # selectFromModel로 자동선택한 특성으로 학습
#         new_model = model.fit(X_train_new, y_train)
#         my_logger.info("후: {:.3f}".format(r.score(X_test_new, y_test)))
#         my_logger.info('')