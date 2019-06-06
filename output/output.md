​		



# 단일 특성



## ASMInstructin - Ngram

정확도: 악성코드를 악성코드라고 예측하고, 정상파일을 정상파일로 탐지한 비율

| 모델이름                      | 1gram | 2gram | 3gram | 4gram |
| ----------------------------- | ----- | ----- | ----- | ----- |
| DecisionTreeClassifier        | 0.701 | 0.702 | 0.746 | 0.7   |
| RandomForestClassifier        | 0.701 | 0.703 | 0.792 | 0.7   |
| AdaBoostClassifier            | 0.701 | 0.703 | 0.74  | 0.7   |
| GradientBoostingClassifier    | 0.701 | 0.703 | 0.789 | 0.7   |
| MLPClassifier                 | 0.7   | 0.7   | 0.76  | 0.7   |
| KNeighborsClassifier          | 0.591 | 0.7   | 0.768 | 0.7   |
| QuadraticDiscriminantAnalysis | 0.42  | 0.307 | 0.573 | 0.308 |
| GaussianNB                    | 0.36  | 0.306 | 0.63  | 0.308 |



## ByteHistogram

| 모델이름                      | 정확도 |
| ----------------------------- | ------ |
| GradientBoostingClassifier    | 0.921  |
| RandomForestClassifier        | 0.913  |
| KNeighborsClassifier          | 0.86   |
| AdaBoostClassifier            | 0.849  |
| DecisionTreeClassifier        | 0.821  |
| MLPClassifier                 | 0.711  |
| GaussianNB                    | 0.588  |
| QuadraticDiscriminantAnalysis | 0.566  |



# Import

#1 사용한 Import 함수이름

```
GetProcAddress, GetModuleHandleA, GetLastError, ExitProcess, Sleep, WriteFile, MultiByteToWideChar, FreeLibrary, GetTickCount, GetCurrentProcess, RegCloseKey, ReadFile, SetFilePointer, GetCurrentThreadId, VirtualAlloc 
```



| 모델이름                      | 정확도 |
| ----------------------------- | ------ |
| KNeighborsClassifier          | 0.718  |
| DecisionTreeClassifier        | 0.718  |
| RandomForestClassifier        | 0.718  |
| GaussianNB                    | 0.718  |
| QuadraticDiscriminantAnalysis | 0.718  |
| GradientBoostingClassifier    | 0.718  |
| MLPClassifier                 | 0.717  |
| AdaBoostClassifier            | 0.717  |



#2 사용한 Import 함수이름

```
GetProcAddress, GetModuleHandleA, GetLastError, ExitProcess, Sleep, WriteFile, MultiByteToWideChar, FreeLibrary, GetTickCount, GetCurrentProcess, RegCloseKey, ReadFile, SetFilePointer, GetCurrentThreadId, VirtualAlloc, CreateFileA, GetCommandLineA, FindClose, WaitForSingleObject, GetStdHandle, GetFileSize, EnterCriticalSection, LeaveCriticalSection, VirtualFree, WideCharToMultiByte, RegQueryValueExA, DeleteCriticalSection, RegOpenKeyExA, DestroyWindow, GetCurrentProcessId, UnhandledExceptionFilter, lstrlenA, GetDC, CharNextA, GetVersion, MessageBoxA, LocalAlloc, RtlUnwind
```



| 모델이름                      | 정확도 |
| ----------------------------- | ------ |
| RandomForestClassifier        | 0.839  |
| GradientBoostingClassifier    | 0.837  |
| KNeighborsClassifier          | 0.819  |
| MLPClassifier                 | 0.796  |
| DecisionTreeClassifier        | 0.778  |
| AdaBoostClassifier            | 0.757  |
| GaussianNB                    | 0.644  |
| QuadraticDiscriminantAnalysis | 0.621  |



# Exports

| 모델이름                      | 정확도 |
| ----------------------------- | ------ |
| RandomForestClassifier        | 0.798  |
| GradientBoostingClassifier    | 0.798  |
| KNeighborsClassifier          | 0.792  |
| DecisionTreeClassifier        | 0.77   |
| MLPClassifier                 | 0.769  |
| QuadraticDiscriminantAnalysis | 0.746  |
| AdaBoostClassifier            | 0.743  |
| GaussianNB                    | 0.595  |



# SectionName

| 모델이름                      | 정확도 |
| ----------------------------- | ------ |
| KNeighborsClassifier          | 0.7    |
| DecisionTreeClassifier        | 0.7    |
| RandomForestClassifier        | 0.7    |
| MLPClassifier                 | 0.7    |
| AdaBoostClassifier            | 0.7    |
| GradientBoostingClassifier    | 0.7    |
| GaussianNB                    | 0.417  |
| QuadraticDiscriminantAnalysis | 0.336  |
