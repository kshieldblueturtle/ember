import pefile
import os
from tqdm import tqdm
import pandas as pd
import multiprocessing

def file_iterator(dir_path):
    for path in os.listdir(dir_path):
        yield os.path.join(dir_path, path)

def extract_resource_name(pe):
    if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE') is False:
        return False
    
    resource_name = []
        
    for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if resource_type.name is not None:
            name = resource_type.name
        else:
            name = pefile.RESOURCE_TYPE.get(resource_type.struct.Id)        

        if name:
            resource_name.append(name)
        else:
            resource_name.append(resource_type.struct.Id)
            
    return resource_name

def main():
    # dir_path = '/home/choi/Desktop/traintest/'
    dir_path = '/home/choi/Desktop/trainset/TrainSet'
    end = 10000

    resource_count = {}
    files = os.listdir(dir_path)
    for path in tqdm(file_iterator(dir_path), total=end):

        try:
            pe = pefile.PE(path)

            resource_names = extract_resource_name(pe)

            if not resource_names:
                continue

            for resource_name in resource_names:
                if resource_count.get(resource_name) == None:
                    resource_count[resource_name] = 1
                else:
                    resource_count[resource_name] += 1
        except Exception as e:
            print('{}: {}'.format(path, e))

    df = pd.DataFrame.from_dict(resource_count.items())
    df.columns = ['resource name', 'count']
    df.to_csv('resource_names.csv', index=None)

    # # 출력
    # for key, value in resource_count.items():
    #     print(key, value)

if __name__=='__main__':
    main()