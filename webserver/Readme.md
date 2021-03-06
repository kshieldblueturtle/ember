# 웹 서비스

Pyhon Flask 웹 프레임워크를 사용해서 웹 서비스를 구현했습니다. 소규모 프로젝트이기 때문에 Apache, Nginx등 웹 서버와 연동하지 않았습니다. 



# 기능

PE포맷 파일을 제출하면 해당 파일에 대해서 악성인지 정상파일인지 검사합니다. 프로젝트에 있는 학습 모델이 검사합니다. 



# 설치

1. 가상환경 활성화
2. 프로젝트 requirement.txt 설치

```
(env)$ pip install -r requirments.txt
```



# 프로젝트 구조

* static: 웹 페이지 자원(js, css, 이미지 등)

* templates/submit.html: 파일 제출 페이지

* templates/result.html: 머신러닝 모델 예측결과 페이지

* main.py: Flask 실행 소스코드

* *.pkl : 머신러닝 학습 모델



# 실행

Debug모드가 활성화 되어 있으므로 실행 에러가 그대로 페이지에 노출됩니다. 

```
(env)$ python main.py
```

![](../screenshot/flask실행.png)



localhost:8888에 접속하면 파일 제출페이지에 접속됩니다.

![](../screenshot/파일제출페이지.png)



PE포맷파일을 제출하면 해당 파일이 악성인지 정상인지 검사합니다. 검사가 끝나면 결과 페이지로 이동됩니다. 각 학습된 머신러닝 모델의 결과와 ""악성 개수/머신러닝 모델 개수""가 출력됩니다.

![](../screenshot/파일제출 완료.png)

