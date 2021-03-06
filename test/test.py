import unittest
import pandas as pd
import os
import sys
import jsonlines
import tqdm
import lightgbm as lgb
import pefile
from collections import OrderedDict

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from src import features, ember

def ExtractLabel(filename, df):
    return df[df.hash==filename].values[0][1]

def sample_iterator(dirpath):
    '''
    디렉터리 탐색 제너레이터
    '''
    for filename in os.listdir(dirpath):
        yield filename

class TestArea(unittest.TestCase):
    def setUp(self):
        '''
        테스트 초기화
        '''
        self.dirpath = '/home/choi/Desktop/traintest'
        # self.dirpath = '/home/choi/Desktop/trainset/TrainSet'
        self.output = '/home/choi/Desktop/output'
        self.csv = '/home/choi/Desktop/TrainSet.csv'
        self.testdirpath = '/home/choi/Desktop/traintest'

    def test_extract_features(self):
        '''
        특성 추출 테스트
        '''        
        df = pd.read_csv(self.csv, names=['hash', 'y'])
        extractor = features.PEFeatureExtractor()

        # 파일 쓰기
        with jsonlines.open(os.path.join(self.output, "features.jsonl"), 'w') as f:
            for _file in tqdm.tqdm(os.listdir(self.dirpath)):
                path = os.path.join(self.dirpath, _file)
                try:
                    feature = extractor.raw_features(path)
                    
                    feature.update({"sha256": _file}) #hash
                    feature.update({"label" : ExtractLabel(_file, df)}) #label
                    f.write(feature)        
                except KeyboardInterrupt:
                    sys.exit()
                except Exception as e:
                    print('{} has error: {}'.format(_file, e))

    def test_train_model(self):
        '''
        모델 학습 테스트
        '''
        rows = 0
        with jsonlines.open(os.path.join(self.output, 'features.jsonl')) as reader:
            for obj in reader.iter(type=dict, skip_invalid=True):
                rows += 1

        # 벡터화
        ember.create_vectorized_features(self.output, rows)

        # Train and save model
        print("Training LightGBM model")
        lgbm_model = ember.train_model(self.output, rows)
        lgbm_model.save_model(os.path.join(self.output, "model.txt")) 

    def test_predict_sample_withModel(self):
        '''
        학습한 모델을 사용해서 샘플 예측 테스트
        '''
        model_path = os.path.join(self.output, "model.txt")
        lgbm_model = lgb.Booster(model_file=model_path)

        y_pred = []
        name = []
        err = 0
        end = len(next(os.walk(self.testdirpath))[2])

        for filename in tqdm.tqdm(sample_iterator(self.testdirpath), total=end):
            filepath = os.path.join(self.testdirpath, filename)
            name.append(filename)
            try:
                y_pred.append(ember.predict_sample(lgbm_model, filepath))
            except KeyboardInterrupt:
                sys.exit()
            except Exception as e:
                y_pred.append(0)
                print("{}: {} error is occuered".format(filename, e))
                err += 1
                    
        series = OrderedDict([('hash', name),('y_pred', y_pred)])
        r = pd.DataFrame.from_dict(series)
        r.to_csv(os.path.join(self.output, 'result.csv'), index=False, header=None)

    def test_fileinfo(self):
        '''
        version information없는 파일 확인 테스트
        '''
        # 정상 타겟
        target = '0a1023c0d17681b9154ac0f3c0a03865.vir'
        # 비정상 타겟
        # target = '0a037da609eb2d50e273afd3d9ec8e85.vir'
        path = os.path.join(self.dirpath , target)
        
        pe = pefile.PE(path)
        pe_dict = pe.dump_dict()
        print(pe_dict.keys())
        if pe_dict.get('Version Information') is None:
            print('No exist')
        else:
            print('exist')
    
    def test_extract_sectionname(self):
        '''
        섹션 이름 추출 테스트
        '''
        # 언패킹 타겟
        target = '0a1023c0d17681b9154ac0f3c0a03865.vir'       
        path = os.path.join(self.dirpath , target)

        section = features.SectionNameInfo()
        pe = pefile.PE(path)
        bytez = open(path, 'rb').read()

        # 호출
        section_names = section.raw_features(bytez, pe)
        for key, value in section_names.items():
            print(key, value)

        # 특성 개수(=dim)
        print('특성 개수: {}'.format(len(section_names)))

    def test_extract_resourcename(self):
        # 리소스 섹션이 없는 샘플
        target = '0c8eeca34a84dfc0aa3b13f8dba7bb82.vir'       
        
        # 리소스 섹션이 있는 샘플
        # target = '0a1023c0d17681b9154ac0f3c0a03865.vir'
        path = os.path.join(self.dirpath , target)

        pe = pefile.PE(path)
        bytez = open(path, 'rb').read()

        if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE') is False:
            print('no')
        else:
            print('yes')

    def test_extract_asminstruction(self):
        target = '0c8eeca34a84dfc0aa3b13f8dba7bb82.vir'       
        
        path = os.path.join(self.dirpath , target)        
        pe = pefile.PE(path)
        asm_extractor = features.AsmInstruction()
        
        r = asm_extractor.raw_features(path, pe)
        print(len(r))   

    def test_extract_imports(self):
        target = '0b43236155522d7689a1659e395a6814.vir'       
        
        path = os.path.join(self.dirpath , target)        
        pe = pefile.PE(path)

        imports_extractor = features.ImportsInfo()
        
        importFunctions = imports_extractor.raw_features(path, pe)

        for key, value in importFunctions.items():
            print(key, value)

    def test_extract_HeaderInfo(self):
        target = '0a52f2fb0318031bf2cd2429e71c54d0.vir'       
        
        path = os.path.join(self.dirpath , target)        
        pe = pefile.PE(path)

        fileinfo_extractor = features.DOSHEADER()
        r = fileinfo_extractor.raw_features(path, pe)
        print(len(r))

    def test_extract_DOS(self):
        target = '0a8d34227ff751975680bd8ad007a73c.vir'       
        
        path = os.path.join(self.dirpath , target)        
        pe = pefile.PE(path)

        fileinfo_extractor = features.DOSHEADER()
        r = fileinfo_extractor.raw_features(path, pe)
        print(r)

