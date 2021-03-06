import os
import pefile
import operator
from capstone import *
from capstone.x86 import *
import multiprocessing
import tqdm
import pandas as pd

'''
참고자료: 책->인공지능 보안을 배우다.
'''

gram = {}
gram_threshold = 4

def gen_list_n_gram(num, asm_list):
    for i in range(0, len(asm_list), num):
        yield asm_list[i:i + num]

def n_grams(num, asm_list):
    gen_list = gen_list_n_gram(num, asm_list)

    for lis in gen_list:
        lis = " ".join(lis)
        try:
            gram[lis] += 1
        except:
            gram[lis] = 1

def extract_asmInstruction(filepath):
    try:
        asm = []
        pe = pefile.PE(filepath)

        ep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        end = pe.OPTIONAL_HEADER.SizeOfCode
        ep_ava = ep + pe.OPTIONAL_HEADER.ImageBase

        for section in pe.sections:
            addr = section.VirtualAddress
            size = section.Misc_VirtualSize

            if ep > addr and ep < (addr + size):
                # print(section.Name)
                ep = addr
                end = size

        data = pe.get_memory_mapped_image()[ep:ep + end]
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        md.detail = False

        #디스어셈
        for insn in md.disasm(data, ep_ava):
            asm.append(insn.mnemonic)

        return asm
    except Exception as e:
        return False

def fileIterator(dirpath):
    for filepath in os.listdir(dirpath):
        yield os.path.join(dirpath, filepath)

def main():
    target = r'C:\Users\sungwook\Documents\Trainset\TrainSet'
    numberOfCPU  = multiprocessing.cpu_count() - 1
    pool = multiprocessing.Pool(numberOfCPU)

    for asm in tqdm.tqdm(pool.imap(extract_asmInstruction, fileIterator(target)), total=10000):
        if asm is False:
            continue
        n_grams(gram_threshold, asm)

    sorted_x = dict(sorted(gram.items(), key=operator.itemgetter(1), reverse=True)[:50])
    df = pd.DataFrame.from_dict(sorted_x.items())
    df.columns = ['ngram', 'count']
    df.to_csv('asm_ngram.csv', index=None)

    for key, value in sorted_x.items():
        print("'{}' : 0, ".format(key))


if __name__ == "__main__":
    main()

