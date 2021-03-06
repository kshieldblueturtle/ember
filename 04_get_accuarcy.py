# -*- coding: utf-8 -*-
from sklearn.metrics import confusion_matrix, accuracy_score
import pandas as pd
import numpy as np
import argparse
import tqdm
import os
import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--csv', type=str, required=True, help='csv file(test result)')
parser.add_argument('-o', '--output', type=str, required=True, help='csv file(test result)')
parser.add_argument('-l', '--label', type=str, required=True, help='csv file(testdataset label)')
args = parser.parse_args()

clssifieies = []

def split_predict(df):
    '''
    예측결과 파일에서 알고리즘별로 분리 후
    파일로 저장
    '''
    groups = df.groupby(df['classifier'])
    x = dict(list(groups))

    for key, value in x.items():
        savepath = os.path.join(args.output, key)
        new_df = value.drop(['classifier'], axis=1)
        new_df.to_csv(savepath + '.csv', index=None)
        clssifieies.append(key)

def predict(src_df, dst_df):
    '''
    src_df: 예측
    dst_df: 정답지
    '''
    answer = dst_df.y.tolist()
    predict = []
    end = len(dst_df)
    cnt = 0

    # 정렬
    for idx, row in tqdm.tqdm(dst_df.iterrows(), total=end):
        _name = row['filename']
        r = src_df[src_df.filename==_name].values[0][1]
        predict.append(int(r))

    accuracy = accuracy_score(predict, answer)
    print("accuracy : %.2f%%" % (np.round(accuracy, decimals=4)*100))
        
    #get and print matrix
    tn, fp, fn, tp = confusion_matrix(predict, answer).ravel()
    mt = np.array([[tp, fp],[fn, tn]])

    print(mt)
    print("오탐 : %.2f%%" % ( round(fp / float(fp + tn), 4) * 100))
    print("미탐 : %.2f%%" % ( round(fn / float(fn + tp), 4) * 100))

def main():
    df = pd.read_csv(args.csv, names=['filename', 'pred_y', 'classifier'])
    label_df = pd.read_csv(args.label, names=['filename', 'y'])

    # 예측 파일에서 모델 결과 분리
    split_predict(df)

    # 모델 예측 평가
    for classifier in clssifieies:
        try:
            print('===================== {} 평가 시작 ========================'.format(classifier))
            filename = os.path.join(args.output, classifier) + '.csv'
            classifier_df = pd.read_csv(filename, names=['filename', 'pred_y'])
            predict(classifier_df, label_df)
            print()
        except:
            print("파일 경로 또는 파일이 열려 있는지 확인하세요")

if __name__=='__main__':
    main()