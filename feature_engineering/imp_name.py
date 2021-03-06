import pefile
import multiprocessing
import os
import tqdm
import csv
import pandas as pd

def dir_iterator(dirpath):
    for path in os.listdir(dirpath):
        yield os.path.join(dirpath, path)

def extract_section_name(filepath):
    '''
    참고자료: pescanner
    https://github.com/hiddenillusion/AnalyzePE/blob/master/pescanner.py
    '''
    try:
        names = []
        pe = pefile.PE(filepath)
            
        if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
            for lib in pe.DIRECTORY_ENTRY_IMPORT:
                for imp in lib.imports:                
                    if imp.name != None: # remove 'null'                    
                            names.append(imp.name.decode('ascii'))

        return names     
        
    except pefile.PEFormatError as e:
        print("PE추출 실패 {}".format(filepath))
        return False
    except UnicodeDecodeError as e:
        print("디코딩 실패 {}".format(filepath))
        return False

def main():
    target = '/home/choi/Desktop/trainset/TrainSet'
    # target = '/home/choi/Desktop/traintest'
    manager = multiprocessing.Manager()
    imp_count = manager.dict()

    # CPU 개수
    numberOfCPU = multiprocessing.cpu_count()
    print("CPU 개수 : {}".format(numberOfCPU))

    pool = multiprocessing.Pool(numberOfCPU)
    end = 10000
    for r in tqdm.tqdm(pool.imap(extract_section_name, dir_iterator(target)), total=end):
        if r == False:
            continue

        for section_name in r:
            if imp_count.get(section_name) == None:
                imp_count[section_name] = 1
            else:
                imp_count[section_name] += 1

    df = pd.DataFrame.from_dict(imp_count.items())
    df.columns = ['function_name', 'count']
    df.to_csv('imp_names.csv', index=None)

    # for key, value in imp_count.items():
    #     print(key, value)

if __name__ == '__main__':
    main()