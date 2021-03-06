import pefile
import multiprocessing
import os
import tqdm

def dir_iterator(dirpath):
    for path in os.listdir(dirpath):
        yield os.path.join(dirpath, path)

def extract_resouce_name(filepath):
    '''
    참고자료: pescanner
    https://github.com/hiddenillusion/AnalyzePE/blob/master/pescanner.py
    '''
    try:
        names = []
        pe = pefile.PE(filepath)

        if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
            for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
                if resource_type.name is not None:
                    name = "%s" % resource_type.name
                else:
                    name = "%s" % pefile.RESOURCE_TYPE.get(resource_type.struct.Id)
                if name == None:
                  name = str("%d" % resource_type.struct.Id)
                  
            names.append(name)
            return names

        return False        
        
    except pefile.PEFormatError as e:
        print("PE추출 실패 {}".format(filepath))
        return False

def main():
    target = '/home/choi/Desktop/traintest'
    manager = multiprocessing.Manager()
    resource_name_count = manager.dict()

    # CPU 개수
    numberOfCPU = multiprocessing.cpu_count()
    print("CPU 개수 : {}".format(numberOfCPU))

    pool = multiprocessing.Pool(numberOfCPU)
    end = 100
    for r in tqdm.tqdm(pool.imap(extract_resouce_name, dir_iterator(target)), total=end):
        if r == False:
            continue

        for resource_name in r:
            if resource_name_count.get(resource_name) == None:
                resource_name_count[resource_name] = 1
            else:
                resource_name_count[resource_name] += 1

    for key, value in resource_name_count.items():
        print(key, value)

if __name__ == '__main__':
    main()