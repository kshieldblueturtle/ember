# 프로젝트

머신러닝으로 윈도우 32bit파일을 대상으로 정상/악성코드를 판단하는 프로젝트입니다.

 https://github.com/choisungwook/ember.git를 Fork하고 개발 흐름을 사용했습니다.



# State Change(소스 코드 변경 이력)

1. Fork https://github.com/choisungwook/ember.git
2. 프로그램 흐름의 뼈대는 유지하고 특성 추출 하는 부분을 제거
3. 특성 추출 라이브러리를 pefile로 변경
4. pefile을 사용해서 특성 추출 & 가공
5. 기존 학습 함수(train_model)삭제하고 새로운 학습 모델 구현



# 데이터 셋

정보보호 R&D 데이터 셋(<https://www.kisis.or.kr/kisis/subIndex/278.do>)



# 샘플 분석 중 발견한 것들
* objdump: 패킹 된 어떤 샘플은 objudmp로 디스 어셈블 실패 -> capstone 패키지를 사용해서 디스어셈블



# 프로젝트 구조

* ember: 특성 추출, 학습, 예측 소스코드 디렉터리
* test: 개발 중에 테스트 목적으로 만든 소스코드 디렉터리
* notebook: 주피터 노트북으로 테스트한 소스코드 디렉터리



# 설치

- 파이썬 3.5버전 이상
- 우분투 16이상
- 라이브러리, 파이썬 패키지 설치

```
$ sudo apt install python-pip3, python-dev
```

```
# 가상환경 설치(virtualenv, conda env, pyvenv 등 선택해서 사용)
# 이 예제는 virtualenv

$ virtualenv env -p python3
$ . ./env/bin/activate
```

```
# 파이썬 패키지 설치
(env)$ pip install -r requirements.txt
```



# 준비

csv파일에 각 파일 이름과 정상/악성인지 적습니다. 정상이면 0, 악성이면 1로 판단합니다.

![라벨](screenshot/준비_라벨파일.png)



# 실행 방법

## 특성 추출

멀티 프로세스로 PE포맷 바이너리 파일의 특성을 추출합니다. 프로세스의 개수는 실행하고 있는 CPU에 의존합니다. 예를 들어 i7-8700은 CPU가 6개이므로 6개를 사용합니다.

```bash
(env)$ python 01_extract_multi.py -d [데이터셋 경로] -c [데이터셋 라벨] -o [추출한 특성을 저장할 경로]
```



### 특성 추출 결과

jsonl, csv파일이 생성됩니다. csv파일은 사람 눈에 보기 좋게 만든 결과이고 jsonl파일은 특성 가공, 학습 과정에서 사용됩니다. 

![특성추출결과](screenshot/특성추출_결과.png) {:.alignleft}



## 학습

첫 번째 학습을 하고 특성 중요도가 높은 40%을 다시 선택해서 학습합니다. 모델에 따라서 특성 중요도가 없는 것이 있습니다. 이 모델은 특성 중요도 학습에 제외시킵니다.

```
(env)$ python 02_train.py -d [features.jonl경로] -o [학습 결과를 저장할 경로] -s [저장할 학습 테이블 이름]
```



### 학습결과

* 1st: 첫 번째 학습 결과

* 1.kfold: 첫 번째 학습의 K-fold

* 2nd: 학습 모델의 특성 중요도 40%선택 후 다시 학습한 결과

* 2.kfold: 다시 학습한 모델의 k-fold

![특성추출결과](screenshot/학습결과.png) {:.alignleft}



# 피처 엔지니어링

피처 엔지니어링 디렉터리 참고



# 테스트 코드

test디렉터리 참고



# 참고자료
* 오픈소스: https://github.com/endgameinc/ember  

* 논문 정보

  H. Anderson and P. Roth, "EMBER: An Open Dataset for Training Static PE Malware Machine Learning Models”, in ArXiv e-prints. Apr. 2018.  

```
@ARTICLE{2018arXiv180404637A,  
  author = {{Anderson}, H.~S. and {Roth}, P.},  
  title = "{EMBER: An Open Dataset for Training Static PE Malware Machine Learning Models}",  
  journal = {ArXiv e-prints},  
  archivePrefix = "arXiv",  
  eprint = {1804.04637},  
  primaryClass = "cs.CR",  
  keywords = {Computer Science - Cryptography and Security},  
  year = 2018,  
  month = apr,  
  adsurl = {http://adsabs.harvard.edu/abs/2018arXiv180404637A},  
}    
```

* 책: 인공지능 보안을 배우다