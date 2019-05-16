# 프로젝트

머신러닝으로 윈도우 32bit파일을 대상으로 정상/악성을 판단하는 프로젝트입니다.



# 데이터 셋

정보보호 R&D 데이터 셋

# 샘플 분석 중 발견한 것들
* objdump: 패킹 된 어떤 샘플은 objudmp로 디스 어셈블 실패

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
(env)$ pip3 install -r requirements.txt
```



# 실행 방법

* 올릴 예정



# State Change(소스 코드 변경 이력)

1. Fork https://github.com/choisungwook/ember.git
2. 프로그램 흐름의 뼈대는 유지하고 특성 추출 하는 부분을 제거
3. 특성 추출 라이브러리를 pefile로 변경



# 테스트 코드

test디렉터리 참고



# 참고자료
* https://github.com/endgameinc/ember  

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
<br />  
```
