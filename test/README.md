# 테스트 코드

개발 하면서 만들었던 테스트 코드 입니다. <br/>

python unittest를 사용했습니다.



## setup

```python
self.dirpath = 트레이닝 데이터셋 경로
self.output = 저장 경로
self.csv = 트레이닝 데이터셋 정답 파일
self.testdirpaht = 예측 데이터셋 
```

# 실행방법
```
1. 가상환경 실행
2. python -m unittest test.TestArea.[테스트 할 함수이름]
예) python -m unittest test.TestArea.test_extract_features
* 아직 subprocess로그 끄는 방법을 찾지 못함
```


## test_extract_features

특성 추출 테스트 소스코드 <br/>

features.jsonl파일 생성(경로: self.output, features.jsonl)



## test_train_model

모델 학습 테스트 소스코드 <br/>

* 추출한 특성으로 학습 
* 학습 모델은 파일로 생성(경로: self.output)



## test_sample

학습 모델을 사용해서 샘플에 대해 예측

* 결과: 정상:0, 악성:1
* 샘플의 결과는 csv파일로 저장(경로: self.output, result.csv)

