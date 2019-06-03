from flask import Flask
import pandas as pd
import os
import logging
import multiprocessing
import jsonlines
import tqdm
import sys

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from src import features, ember

# logger 설정
my_logger = logging.getLogger(__name__)
sh = logging.StreamHandler()
my_logger.addHandler(sh)
my_logger.setLevel(logging.DEBUG)


app = Flask(__name__)

# 테스트 경로
test_csv = '/home/choi/Desktop/TrainSet.csv'
test_dataset = '/home/choi/Desktop/traintest'
test_output = '/home/choi/Desktop/flask_output'

# 트레이닝 셋 라벨파일 읽기
data = pd.read_csv(test_csv, names=['hash', 'y'])

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
    for filename in os.listdir(test_dataset):
        yield filename

def extract_features(filename):
    """
    멀티 프로세싱으로 특성 추출
    """
    extractor = features.PEFeatureExtractor()
    fullpath = os.path.join(os.path.join(test_dataset, filename))
    try:
        feature = extractor.raw_features(fullpath)
        feature.update({"sha256": filename}) # sample name(hash)
        feature.update({"label" : ExtractLabel(filename)}) #label

    except KeyboardInterrupt:        
        sys.exit()
    except Exception as e:        
        my_logger.debug("{}: {} error is occuered".format(filename, e))
        return None

    return feature

@app.route('/predict', methods=['GET'])
def extract_subset():
    """
    멀티 프로세싱
    """
    numberOfcpu = multiprocessing.cpu_count()
    pool = multiprocessing.Pool(numberOfcpu)
    lock = multiprocessing.Lock()
    end = len(next(os.walk(test_dataset))[2])
    
    extractor_iterator = ((filename) for idx, filename in enumerate(file_iterator()))
    with jsonlines.open(os.path.join(test_output, "features.jsonl"), 'w') as f:
        for x in tqdm.tqdm(pool.imap_unordered(extract_features, extractor_iterator), total=end):
            if not x:
                continue
            lock.acquire()
            f.write(x)                
            lock.release()
            
    pool.close()
    pool.join()

    print('Done')
    return "Done"

if __name__=='__main__':
    app.run(debug=True)