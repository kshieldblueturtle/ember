import pefile
import multiprocessing
import os
import tqdm
import csv
import pandas as pd

def dir_iterator(dirpath):
    for path in os.listdir(dirpath):
        yield os.path.join(dirpath, path)

def extract_export(filepath):
    '''
    참고자료: https://github.com/guelfoweb/peframe/blob/d29e6ea00ebb8bfbfdc40a7ba0c983ca9afc55ba/modules/directories.py
    '''    
    names = []
    try:
        pe = pefile.PE(filepath)

        for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
            name = exp.name.decode('ascii')
            names.append(name)
    except:
        return False

    return names

def main():
    target = '/home/choi/Desktop/trainset/TrainSet'
    # target = '/home/choi/Desktop/traintest'
    manager = multiprocessing.Manager()
    count = manager.dict()

    # CPU 개수
    numberOfCPU = multiprocessing.cpu_count()
    print("CPU 개수 : {}".format(numberOfCPU))

    pool = multiprocessing.Pool(numberOfCPU)
    end = 10000
    for r in tqdm.tqdm(pool.imap(extract_export, dir_iterator(target)), total=end):
        if r == False:
            continue

        for function_name in r:
            if count.get(function_name) == None:
                count[function_name] = 1
            else:
                count[function_name] += 1

    df = pd.DataFrame.from_dict(count.items())
    df.columns = ['function_name', 'count']
    df.to_csv('export_names.csv', index=None)

    # for key, value in count.items():
    #     print(key, value)

if __name__ == '__main__':
    main()