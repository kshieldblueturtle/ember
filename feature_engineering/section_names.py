import pefile
import multiprocessing
import os
import tqdm
import csv
import pandas as pd

# def isSectionExecutable(section):
# 	characteristics = getattr(section, 'Characteristics')

#     if (characteristics & 0x00000020 > 0) or (characteristics & 0x20000000 > 0):
#         return True
#     return False

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
        
        for section in pe.sections:
            section_name = section.Name.decode('ascii')
            section_name = section_name.split('\00')[0].lower()
            
            if section_name == '':
                section_name = '.None'

            names.append(section_name)

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
    section_name_count = manager.dict()

    # CPU 개수
    numberOfCPU = multiprocessing.cpu_count()
    print("CPU 개수 : {}".format(numberOfCPU))

    pool = multiprocessing.Pool(numberOfCPU)
    end = 10000
    for r in tqdm.tqdm(pool.imap(extract_section_name, dir_iterator(target)), total=end):
        if r == False:
            continue

        for section_name in r:
            if section_name_count.get(section_name) == None:
                section_name_count[section_name] = 1
            else:
                section_name_count[section_name] += 1

    df = pd.DataFrame.from_dict(section_name_count.items())
    df.columns = ['section_name', 'count']
    df.to_csv('section_names.csv', index=None)
    # for key, value in section_name_count.items():
    #     print(key, value)

if __name__ == '__main__':
    main()