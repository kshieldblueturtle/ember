# State Change
1. ember/features.py: change row variables -2018.10  
2. remove resource directory -2018.10  
3. change script files -2018.10  
4. add 01_extract.py, 02_train.py, 03_predict.py, 04_get_accuracy.py  -2018.10   
(this refer to ember/init.py, ember/features.py)
5. add utils directory  -2018.10 
6. add Test directory  -2018.10 
7. add output directory -2018.12   
8. add multiprocess job of extracting freature - 2019.01
  
  
# Reference
https://github.com/endgameinc/ember  

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
  
# Install
above python 3.5    
```
;Install virtualenv
$ virtualenv env -p python3
$ . ./env/bin/activate
```
  
```
;Install python modules
(env)$ pip install -r requirements.txt
```

# Prerequisite
* inputfile(csv including label) structure without column's names
![traindata_label](screenshot/traindata_label.png)

# how to Run
## Progress
1. 01_extract.py or 01_extract_multi.py 
2. 02_train.py
3. 03_predict.py [To revised]
4. 04_get_accuracy.py [To revised]

## Detail
1. extract features from trainsets
If you run, jsonl file is created.
```
(env)python 01_extract.py -d [TrainSet path] -c [TrainSet label path] -o [output path]
```
  
2. train.py
If you run, model.txt and .dat file are created. 
.dat file which is not printable is temporary file to be used training.
Currently, It is developed GradientBoosting from LightGBM
```
(env)python 02_train.py -d [jsonl path]
``` 

3. 03_predict.py [To revised]
  
4. 04_get_accuracy.py [To revised]

## To Do
1. Pipelien from scikit-learn.
2. GUI or web UI.
3. guide videos.

