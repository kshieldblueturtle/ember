# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
from werkzeug.utils import secure_filename
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from src import features, ember
import pandas as pd
from sklearn.externals import joblib 
import jsonlines
import collections
import pefile

app = Flask(__name__)
Bootstrap(app)

model = {}
feature_importance = {}

def loadmodel():
    '''
    학습 모델 불러오기
    학습 중요도 불로오기
    '''
    modelDirPath = os.path.abspath(os.path.dirname(__file__))
    for filename in os.listdir(modelDirPath):
        name, ext = os.path.splitext(filename)
        # 모델 불러오기
        if ext == '.pkl':
            model[name] = joblib.load(os.path.join(modelDirPath, filename)) 
      
    with jsonlines.open(os.path.join(modelDirPath, 'features_importance.jsonl')) as reader:
        for obj in reader:
            for key, value in obj.items():
                feature_importance[key] = value

def predcit_singfile(target):
    '''
    파일 검사(단일 타겟)
    '''
    x, filepath = ember.predict_preprocess(target)
    X = pd.DataFrame([x])
    result = collections.OrderedDict()
    score = 0

    # key: 모델 이름, value: 모델 객체
    for key, value in model.items():
        if len(feature_importance.get(key)) != 0:
            pass
            new_X = X[feature_importance.get(key)]
            predict_score = value.predict(new_X)
        else:
            predict_score = value.predict(X)

        if predict_score[0] == 1:
            score += 1

        result[key] = predict_score[0]

    # 1->악성, 0->정상
    for key, value in result.items():
        if value == 1:
            result[key] = "악성"
        elif value == 0:
            result[key] = "정상"

    result['악성코드확률'] = str(float(score)/len(model) * 100) + '%'

    return result

@app.route('/')
def my_route():
    return render_template('submit.html')
    
#파일 업로드 & 평가 처리
@app.route('/submit', methods=['POST'])
def submit_file():
    # save_dirpath = ''
    if request.method == "POST":
        f = request.files['filename']
        f.save(secure_filename(f.filename))
     
        try:
            pe = pefile.PE(f.filename)
            result = predcit_singfile(f.filename)
            return render_template('result.html', result=result)
        except:
            return "윈도우 파일이 아닙니다"

if __name__== '__main__':
    loadmodel()
    app.run(host='localhost', port=8888, debug=True)