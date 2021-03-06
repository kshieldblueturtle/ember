# -*- coding: utf-8 -*-
''' Extracts some basic features from PE files. Many of the features
implemented have been used in previously published works. For more information,
check out the following resources:
* Schultz, et al., 2001: http://128.59.14.66/sites/default/files/binaryeval-ieeesp01.pdf
* Kolter and Maloof, 2006: http://www.jmlr.org/papers/volume7/kolter06a/kolter06a.pdf
* Shafiq et al., 2009: https://www.researchgate.net/profile/Fauzan_Mirza/publication/242084613_A_Framework_for_Efficient_Mining_of_Structural_Information_to_Detect_Zero-Day_Malicious_Portable_Executables/links/0c96052e191668c3d5000000.pdf
* Raman, 2012: http://2012.infosecsouthwest.com/files/speaker_materials/ISSW2012_Selecting_Features_to_Classify_Malware.pdf
* Saxe and Berlin, 2015: https://arxiv.org/pdf/1508.03096.pdf

It may be useful to do feature selection to reduce this set of features to a meaningful set
for your modeling problem.
'''

import re
import pefile
import numpy as np
from sklearn.feature_extraction import FeatureHasher
import time
import pandas as pd
import logging
import collections
import math
import warnings
from capstone.x86 import *
from capstone import *
warnings.simplefilter(action='ignore', category=FutureWarning)
warnings.simplefilter(action='ignore', category=UserWarning)

# 로거 설정
mylogger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh = logging.StreamHandler()
sh.setFormatter(formatter)
mylogger.addHandler(sh)
mylogger.setLevel(logging.DEBUG)

def get_entropy(binarydata):
    '''
    바이너리의 엔트로피를 구하는 함수
    엔트로피 알고리즘: Shannon entropy
    소스코드: https://github.com/erocarrera/pefile/blob/master/pefile.py의 entropy_H 함수
    '''
    if not binarydata:
        return 0.0

    occurences = collections.Counter(bytearray(binarydata))
    entropy = 0.0

    for x in occurences.values():
        p_x = float(x) / len(binarydata)
        entropy -= p_x * math.log(p_x, 2)

    return entropy

class FeatureType(object):
    ''' Base class from which each feature type may inherit '''

    name = ''
    dim = 0

    def __repr__(self):
        return '{}({})'.format(self.name, self.dim)

    def raw_features(self, filepath, pe):
        ''' Generate a JSON-able representation of the file '''
        raise (NotImplemented)

    def process_raw_features(self, raw_obj):
        ''' Generate a feature vector from the raw features '''
        raise (NotImplemented)

    def feature_vector(self, filepath, pe):
        ''' Directly calculate the feature vector from the sample itself. This should only be implemented differently
        if there are significant speedups to be gained from combining the two functions. '''
        return self.process_raw_features(self.raw_features(filepath, pe))


class ByteHistogram(FeatureType):
    '''
    Byte 1-gram
    '''

    name = 'histogram'
    dim = 256

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        grams = {
            '1_gram': []
        }

        bytez = open(filepath, 'rb').read()
        counts = np.bincount(np.frombuffer(bytez, dtype=np.uint8), minlength=256)
        grams['1_gram'] = counts.tolist()
        
        return grams

    def process_raw_features(self, raw_obj):
        counts = np.array(raw_obj['1_gram'], dtype=np.float32)
        sum = counts.sum()
        normalized = counts / sum

        _dict = {}
        for idx in range(0, 0xFF):
            columns = '1-gram ' + str(idx)
            _dict[columns] = normalized[idx]
        
        return _dict


class SectionNameInfo(FeatureType):
    ''' 
    섹션 정보 추출
    '''

    name = 'section'
    dim = 13

    def __init__(self):
        super(FeatureType, self).__init__()


    def raw_features(self, filepath, pe):
        '''
        악성코드에서 자주 출현하는 섹션의 유/무
        :param self:
        :param pe:
        :return:
        '''

        malicious_sections = {
            '.ndata': 0,
            '.bss': 0,
            'data': 0,
            'code': 0,
            'bss': 0,
            'upx0': 0,
            'upx1': 0,
            'upx2': 0,
            '.itext': 0,
            '.sdata':0          
        }

        for section in pe.sections:
            section_name = section.Name.decode('ascii', 'ignore')
            section_name = section_name.split('\00')[0].lower()
            
            if section_name == '':
                section_name = ".None"

            # 섹션 이름이 있으면 딕셔너리 값을 1로 수정
            if section_name in malicious_sections:
                malicious_sections[section_name] = 1
                
        return malicious_sections

    def process_raw_features(self, raw_obj):
        return raw_obj

class AsmInstruction(FeatureType):
    '''
    '''
    name = 'AsmInstruction'
    dim = 40
    threshold = 3

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        # 빈도수가 높은 명령어
        # To do 직접 특성 공학으로 분석 해야 함 

        # 1gram
        # instruction_list = {
        #     'mov' : 0, 'push' : 0, 'add' : 0, 'int3' : 0, 'call' : 0, 'cmp' : 0, 'pop' : 0, 'lea' : 0, 'je' : 0, 'test' : 0, 'jmp' : 0, 'xor' : 0, 'jne' : 0, 'inc' : 0, 'ret' : 0, 'sub' : 0, 
        #     'dec' : 0, 'nop' : 0, 'and' : 0, 'movzx' : 0, 'or' : 0, 'jb' : 0, 'imul' : 0, 'jae' : 0, 'xchg' : 0, 'jbe' : 0, 'ja' : 0, 'shr' : 0, 'shl' : 0, 'fld' : 0, 'fstp' : 0, 'jl' : 0, 'jle' : 0, 
        #     'jns' : 0, 'js' : 0, 'sar' : 0, 'leave' : 0, 'sbb' : 0, 'jge' : 0, 'jg' : 0, 'outsd' : 0, 'popal' : 0, 'outsb' : 0, 'jo' : 0, 'arpl' : 0, 'insb' : 0, 'insd' : 0, 'jp' : 0, 'bound' : 0, 'aaa' : 0
        # }

        # 2gram
        # instruction_list = {
        #     'mov mov':0, 'int3 int3':0, 'push push':0, 'push call':0, 'add add':0, 'push mov':0, 'mov push':0, 'call mov':0, 'mov call':0, 'pop pop':0, 'test je':0, 'test je':0, 'mov cmp':0, 'lea push':0, 'cmp je':0, 'cmp jne':0,
        #     'lea mov':0, 'call push':0, 'je mov':0, 'pop ret':0, 'push lea':0, 'mov pop':0, 'mov jmp':0, 'add push':0, 'nop nop':0, 'mov test':0, 'inc add':0, 'add mov':0, 'call add':0, 'jmp mov':0, 'mov add':0,
        #     'dec add':0, 'jne mov':0, 'test jne':0, 'mov xor':0, 'je push':0, 'mov sub':0, 'call test':0, 'add inc':0, 'add dec':0, 'lea call':0, 'xor mov':0, 'pop mov':0, 'sub mov':0, 'call pop':0, 'ret push':0, 'add xor':0, 
        #     'je cmp':0, 'add cmp':0
        # }

        # 3gram
        instruction_list = {
            'int3 int3 int3':0, 'mov mov mov':0, 'push push push':0, 'add add add':0, 'push push call':0, 'mov call mov':0, 'mov mov call':0, 'push mov push':0, 'mov call':0, 'push call mov':0, 'mov push push':0, 'call mov mov':0, 'push push mov':0, 'nop nop nop':0, 'mov push mov':0, 'push mov call':0,
            'push call add':0, 'push call push':0, 'mov push call':0, 'add push add':0, 'push mov mov':0, 'mov mov push':0, 'pop pop pop':0, 'lea push push':0, 'add inc add':0, 'mov test je':0, 'test je mov':0, 'add dec add':0, 'mov pop ret':0, 'mov jmp mov':0, 'mov mov cmp':0,
            'lea mov mov':0, 'cmp jne mov':0, 'call push push':0, 'mov lea mov':0, 'mov cmp je':0, 'je mov mov':0, 'push call pop':0, 'pop pop ret':0, 'mov cmp jne':0, 'mov mov lea':0, 'cmp je mov':0, 'add mov mov':0, 'ret int3 int3':0, 'mov pop pop':0, 'mov mov pop':0, 'jmp mov mov':0, 
            'mov mov test':0, 'ret push mov':0
        }

        # 4gram
        # instruction_list = {
        #     'int3 int3 int3 int3' : 0, 'mov mov mov mov' : 0, 'add add add add' : 0, 'push push push push' : 0, 'push push push call' : 0, 'nop nop nop nop' : 0, 'mov mov mov call' : 0, 'mov call mov mov' : 0, 'mov mov call mov' : 0, 'push push call mov' : 0, 'call mov mov mov' : 0, 'mov push push push' : 0, 'push mov push push' : 0, 
        #     'push push call push' : 0, 'ret int3 int3 int3' : 0, 'push push call add' : 0, 'xchg xchg xchg xchg' : 0, 'push push push mov' : 0, 'push mov push mov' : 0, 'push mov call mov' : 0, 'int3 int3 int3 push' : 0, 'mov push mov push' : 0, 'mov test je mov' : 0, 'push push mov call' : 0, 'pop ret int3 int3' : 0, 'push call add mov' : 0, 
        #     'push call push push' : 0, 'int3 int3 push mov' : 0, 'push lea push push' : 0, 'push call mov mov' : 0, 'lea push push push' : 0, 'push push mov push' : 0, 'lea mov mov mov' : 0, 'push call push call' : 0, 'mov push push mov' : 0, 'lea push push call' : 0, 'push mov mov mov' : 0, 'mov mov test je' : 0, 'add add push add' : 0, 'add push add add' : 0, 
        #     'push push call test' : 0, 'test je mov mov' : 0, 'mov mov push push' : 0, 'mov push mov mov' : 0, 'mov mov mov cmp' : 0, 'mov lea mov mov' : 0, 'push mov push call' : 0, 'pop ret push mov' : 0, 'mov push push call' : 0, 'pop pop pop pop' : 0
        # }

        asm = []

        ep = pe.OPTIONAL_HEADER.AddressOfEntryPoint
        end = pe.OPTIONAL_HEADER.SizeOfCode
        ep_ava = ep + pe.OPTIONAL_HEADER.ImageBase

        for section in pe.sections:
            addr = section.VirtualAddress
            size = section.Misc_VirtualSize

            if ep > addr and ep < (addr + size):
                ep = addr
                end = size

        data = pe.get_memory_mapped_image()[ep:ep + end]
        md = Cs(CS_ARCH_X86, CS_MODE_32)
        md.detail = False

        # 디스어셈
        for insn in md.disasm(data, ep_ava):
            asm.append(insn.mnemonic)

        asm_ngram = self.n_grams(self.threshold, asm)

        for key, value in asm_ngram.items():
            if instruction_list.get(key) is not None:
                instruction_list[key] = 1

        return instruction_list

    def process_raw_features(self, raw_obj):
        return raw_obj

    def gen_list_n_gram(self, num, asm_list):
        for i in range(0, len(asm_list), num):
            yield asm_list[i:i + num]

    def n_grams(self, num, asm_list):
        gen_list = self.gen_list_n_gram(num, asm_list)
        gram = {}

        for lis in gen_list:
            lis = " ".join(lis)
            try:
                gram[lis] += 1
            except:
                gram[lis] = 1
        return gram

class ImportsInfo(FeatureType):
    '''
    Import 라이브러리 추출
    '''
    name = 'imports'
    dim = 15

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        imports = {
            'GetProcAddress': 0,
            'GetModuleHandleA': 0,
            'GetLastError': 0,
            'ExitProcess': 0,
            'Sleep': 0,
            'WriteFile': 0,
            'MultiByteToWideChar': 0,
            'FreeLibrary': 0,
            'GetTickCount': 0,
            'GetCurrentProcess': 0,
            'RegCloseKey': 0,
            'ReadFile': 0,
            'SetFilePointer': 0,
            'GetCurrentThreadId': 0,
            'VirtualAlloc': 0,
            'CreateFileA': 0,
            'GetCommandLineA': 0,
            'FindClose': 0,
            'WaitForSingleObject': 0,
            'GetStdHandle': 0,
            'GetFileSize': 0,
            'EnterCriticalSection': 0,
            'LeaveCriticalSection': 0,
            'VirtualFree': 0,
            'WideCharToMultiByte': 0,
            'RegQueryValueExA': 0,
            'DeleteCriticalSection': 0,
            'RegOpenKeyExA': 0,
            'DestroyWindow': 0,
            'GetCurrentProcessId': 0,
            'UnhandledExceptionFilter': 0,
            'lstrlenA': 0,
            'GetDC': 0,
            'CharNextA': 0,
            'GetVersion': 0,
            'MessageBoxA': 0,
            'LocalAlloc': 0,
            'RtlUnwind': 0,
        }

        if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
            for lib in pe.DIRECTORY_ENTRY_IMPORT:
                for imp in lib.imports:    
                    if imp.name != None:
                        name = imp.name.decode('ascii')
                        if imports.get(name) is not None:
                            imports[name] = 1

        return imports

    def process_raw_features(self, raw_obj):
        return raw_obj

class ExportsInfo(FeatureType):
    '''
    익스포트 함수(dll만 해당)
    예외) 익스포트가 없는 dll함수가 있다.
    '''

    name = 'exports'
    dim = 128

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        exports = {
            'DllCanUnloadNow': 0,
            'DllGetClassObject': 0,
            'DllRegisterServer': 0,
            'DllUnregisterServer': 0,
        }

        isdll = pe.is_dll()
        # dll인지 확인->dll이 아니라면 종료
        if isdll is None:
            return exports

        if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
            for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
                if exp.name != None:
                    name = exp.name.decode('ascii')

                    if exports.get(name) is not None:
                        exports[name] = 1
            
        return exports

    def process_raw_features(self, raw_obj):
        return raw_obj

class GeneralFileInfo(FeatureType):
    '''
    파일 버전 정보 추출
    특성 공학 수정 필요
    '''
    name = 'general'
    dim = 20

    def __init__(self):
        super(FeatureType, self).__init__()
 
    def raw_features(self, filepath, pe): 
        fileinfo_header = {
            'FileDescription': '.None',
            'FileVersion': '.None',
            'InternalName': '.None',
            'CompanyName': '.None'
        }

        try:
            FileDescription = pe.FileInfo[0][0].StringTable[0].entries[b'FileDescription'].decode('ascii')
            FileVersion = pe.FileInfo[0][0].StringTable[0].entries[b'FileVersion'].decode('ascii')
            InternalName = pe.FileInfo[0][0].StringTable[0].entries[b'InternalName'].decode('ascii')
            CompanyName = pe.FileInfo[0][0].StringTable[0].entries[b'InternalName'].decode('ascii')

            fileinfo_header['FileDescription'] = FileDescription
            fileinfo_header['FileVersion'] = FileVersion
            fileinfo_header['InternalName'] = InternalName
            fileinfo_header['CompanyName'] = CompanyName

            return fileinfo_header
        except:
            return fileinfo_header

    def process_raw_features(self, raw_obj):
        '''
        특성공학: 해싱
        '''
        for key, value in raw_obj.items():
            r = FeatureHasher(20, input_type='string').transform([value])[0].toarray()[0]
            _convert = r.astype(np.int32)

            # - 제거(양수로 변환)
            for idx, x in enumerate(_convert):
                if x < 0:
                    _convert[idx] = -x
            _convert = [str(num) for num in _convert]
            raw_obj[key] = ''.join(_convert)

        return raw_obj

class DOSHEADER(FeatureType):
    '''
    DOS 헤더 추출
    '''
    name = 'dosheader'    
    dim = 19

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        IMAGE_DOS_HEADER_data = {
            'e_magic': 0,
            'e_cblp': 0,
            'e_cp': 0,
            'e_crlc': 0,
            'e_cparhdr': 0,
            'e_minalloc': 0,
            'e_maxalloc': 0,
            'e_ss': 0,
            'e_sp': 0,
            'e_csum': 0,
            'e_ip': 0,
            'e_cs': 0,
            'e_lfarlc': 0,
            'e_ovno': 0,
            'e_res': 0,
            'e_oemid': 0,
            'e_oeminfo': 0,
            'e_res2': 0,
            'e_lfanew': 0
        }

        if hasattr(pe, 'DOS_HEADER'):
            IMAGE_DOS_HEADER_data['e_magic'] = pe.DOS_HEADER.e_magic
            IMAGE_DOS_HEADER_data['e_cblp'] = pe.DOS_HEADER.e_cblp
            IMAGE_DOS_HEADER_data['e_cp'] = pe.DOS_HEADER.e_cp
            IMAGE_DOS_HEADER_data['e_crlc'] = pe.DOS_HEADER.e_crlc
            IMAGE_DOS_HEADER_data['e_cparhdr'] = pe.DOS_HEADER.e_cparhdr
            IMAGE_DOS_HEADER_data['e_minalloc'] = pe.DOS_HEADER.e_minalloc
            IMAGE_DOS_HEADER_data['e_maxalloc'] = pe.DOS_HEADER.e_maxalloc
            IMAGE_DOS_HEADER_data['e_ss'] = pe.DOS_HEADER.e_ss
            IMAGE_DOS_HEADER_data['e_sp'] = pe.DOS_HEADER.e_sp
            IMAGE_DOS_HEADER_data['e_csum'] = pe.DOS_HEADER.e_csum
            IMAGE_DOS_HEADER_data['e_ip'] = pe.DOS_HEADER.e_ip
            IMAGE_DOS_HEADER_data['e_cs'] = pe.DOS_HEADER.e_cs
            IMAGE_DOS_HEADER_data['e_lfarlc'] = pe.DOS_HEADER.e_lfarlc
            IMAGE_DOS_HEADER_data['e_ovno'] = pe.DOS_HEADER.e_ovno
            IMAGE_DOS_HEADER_data['e_res'] = int.from_bytes(pe.DOS_HEADER.e_res, byteorder='little')
            IMAGE_DOS_HEADER_data['e_oemid'] = pe.DOS_HEADER.e_oemid
            IMAGE_DOS_HEADER_data['e_oeminfo'] = pe.DOS_HEADER.e_oeminfo
            IMAGE_DOS_HEADER_data['e_res2'] = int.from_bytes(pe.DOS_HEADER.e_res2, byteorder='little')
            IMAGE_DOS_HEADER_data['e_lfanew'] = pe.DOS_HEADER.e_lfanew

        return IMAGE_DOS_HEADER_data
    
    def process_raw_features(self, raw_obj):
        # e_res삭제
        del raw_obj['e_res']
        # e_res2 데이터 변경
        raw_obj['e_res2'] = raw_obj['e_res2'] // 10000000000000000000000000000000000000000000

        return raw_obj

class FILEHEADER(FeatureType):
    '''
    파일 헤더 추출
    '''
    name = 'fileheader'    
    dim = 6

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        FILE_HEADER_data = {
            'Machine': 0,
            'NumberOfSections': 0,
            'TimeDateStamp': 0,
            'PointerToSymbolTable': 0,
            'SizeOfOptionalHeader': 0,
            'Characteristics': 0
        }

        if hasattr(pe, 'FILE_HEADER'):
            FILE_HEADER_data['Machine'] = pe.FILE_HEADER.Machine
            FILE_HEADER_data['NumberOfSections'] = pe.FILE_HEADER.NumberOfSections
            FILE_HEADER_data['TimeDateStamp'] = pe.FILE_HEADER.TimeDateStamp
            FILE_HEADER_data['PointerToSymbolTable'] = pe.FILE_HEADER.PointerToSymbolTable
            FILE_HEADER_data['SizeOfOptionalHeader'] = pe.FILE_HEADER.SizeOfOptionalHeader
            FILE_HEADER_data['Characteristics'] = pe.FILE_HEADER.Characteristics
        
        return FILE_HEADER_data

    def process_raw_features(self, raw_obj):
        return raw_obj

class OPTIONALHEADDER(FeatureType):
    '''
    OPTIONAL 헤더 추출
    '''
    name = 'optionalheader'    
    dim = 29

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        OPTIONAL_HEADER_data = {
            'Magic': 0,
            'MajorLinkerVersion': 0,
            'MinorLinkerVersion': 0,
            'SizeOfCode': 0,
            'SizeOfInitializedData': 0,
            'SizeOfUninitializedData': 0,
            'AddressOfEntryPoint': 0,
            'BaseOfCode': 0,
            'ImageBase': 0,
            'SectionAlignment': 0,
            'FileAlignment': 0,
            'MajorOperatingSystemVersion': 0,
            'MinorOperatingSystemVersion': 0,
            'MajorImageVersion': 0,
            'MinorImageVersion': 0,
            'MajorSubsystemVersion': 0,
            'MinorSubsystemVersion': 0,
            'SizeOfImage': 0,
            'SizeOfHeaders': 0,
            'CheckSum': 0,
            'Subsystem': 0,
            'DllCharacteristics': 0,
            'SizeOfStackReserve': 0,
            'SizeOfStackCommit': 0,
            'SizeOfHeapReserve': 0,
            'SizeOfHeapCommit': 0,
            'LoaderFlags': 0,
            'NumberOfRvaAndSizes': 0,
        }

        if hasattr(pe, 'OPTIONAL_HEADER'):
            OPTIONAL_HEADER_data['Magic'] = pe.OPTIONAL_HEADER.Magic
            OPTIONAL_HEADER_data['MajorLinkerVersion'] = pe.OPTIONAL_HEADER.MajorLinkerVersion
            OPTIONAL_HEADER_data['MinorLinkerVersion'] = pe.OPTIONAL_HEADER.MinorLinkerVersion
            OPTIONAL_HEADER_data['SizeOfCode'] = pe.OPTIONAL_HEADER.SizeOfCode
            OPTIONAL_HEADER_data['SizeOfInitializedData'] = pe.OPTIONAL_HEADER.SizeOfInitializedData
            OPTIONAL_HEADER_data['SizeOfUninitializedData'] = pe.OPTIONAL_HEADER.SizeOfUninitializedData
            OPTIONAL_HEADER_data['AddressOfEntryPoint'] = pe.OPTIONAL_HEADER.AddressOfEntryPoint
            OPTIONAL_HEADER_data['BaseOfCode'] = pe.OPTIONAL_HEADER.BaseOfCode
            OPTIONAL_HEADER_data['ImageBase'] = pe.OPTIONAL_HEADER.ImageBase
            OPTIONAL_HEADER_data['SectionAlignment'] = pe.OPTIONAL_HEADER.SectionAlignment
            OPTIONAL_HEADER_data['FileAlignment'] = pe.OPTIONAL_HEADER.FileAlignment
            OPTIONAL_HEADER_data['MajorOperatingSystemVersion'] = pe.OPTIONAL_HEADER.MajorOperatingSystemVersion
            OPTIONAL_HEADER_data['MinorOperatingSystemVersion'] = pe.OPTIONAL_HEADER.MinorOperatingSystemVersion
            OPTIONAL_HEADER_data['MajorImageVersion'] = pe.OPTIONAL_HEADER.MajorImageVersion
            OPTIONAL_HEADER_data['MinorImageVersion'] = pe.OPTIONAL_HEADER.MinorImageVersion
            OPTIONAL_HEADER_data['MajorSubsystemVersion'] = pe.OPTIONAL_HEADER.MajorSubsystemVersion
            OPTIONAL_HEADER_data['MinorSubsystemVersion'] = pe.OPTIONAL_HEADER.MinorSubsystemVersion
            OPTIONAL_HEADER_data['SizeOfImage'] = pe.OPTIONAL_HEADER.SizeOfImage
            OPTIONAL_HEADER_data['SizeOfHeaders'] = pe.OPTIONAL_HEADER.SizeOfHeaders
            OPTIONAL_HEADER_data['CheckSum'] = pe.OPTIONAL_HEADER.CheckSum
            OPTIONAL_HEADER_data['Subsystem'] = pe.OPTIONAL_HEADER.Subsystem
            OPTIONAL_HEADER_data['DllCharacteristics'] = pe.OPTIONAL_HEADER.DllCharacteristics
            OPTIONAL_HEADER_data['SizeOfStackReserve'] = pe.OPTIONAL_HEADER.SizeOfStackReserve
            OPTIONAL_HEADER_data['SizeOfStackCommit'] = pe.OPTIONAL_HEADER.SizeOfStackCommit
            OPTIONAL_HEADER_data['SizeOfHeapReserve'] = pe.OPTIONAL_HEADER.SizeOfHeapReserve
            OPTIONAL_HEADER_data['SizeOfHeapCommit'] = pe.OPTIONAL_HEADER.SizeOfHeapCommit
            OPTIONAL_HEADER_data['LoaderFlags'] = pe.OPTIONAL_HEADER.LoaderFlags
            OPTIONAL_HEADER_data['NumberOfRvaAndSizes'] = pe.OPTIONAL_HEADER.NumberOfRvaAndSizes

        return OPTIONAL_HEADER_data
    
    def process_raw_features(self, raw_obj):
        return raw_obj

class ResourceName(FeatureType):
    '''
    리소스 이름 유/무
    참고자료: pescanner
    https://github.com/hiddenillusion/AnalyzePE/blob/master/pescanner.py
    '''
    name = 'resourceName'
    dim = 8

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        # test1
        maliciou_resource_name = {
            'RT_VERSION': 0,
            'RT_GROUP_ICON': 0,
            'RT_ICON': 0,
            'RT_MANIFEST': 0,
            'RT_STRING': 0,
            'RT_DIALOG': 0,
            'RT_RCDATA': 0,
            'RT_BITMAP': 0,
            'RT_GROUP_CURSOR': 0,
            'RT_CURSOR': 0,
        }
        
        if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE') is False:
            return maliciou_resource_name

        resource_name = []
        
        if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
            for resource_type in pe.DIRECTORY_ENTRY_RESOURCE.entries:
                if resource_type.name is not None:
                    name = "%s" % resource_type.name
                else:
                    name = "%s" % pefile.RESOURCE_TYPE.get(resource_type.struct.Id)
                if name == None:
                    name = str("%d" % resource_type.struct.Id)

                resource_name.append(name)

            for resourcename in resource_name:
                if maliciou_resource_name.get(resourcename) is not None:
                    maliciou_resource_name[resourcename] = 1

        return maliciou_resource_name

    def process_raw_features(self, raw_obj):
        return raw_obj

class TLSSection(FeatureType):
    '''
    TLS섹션 있는지 확인
    '''
    name = 'tls'
    dim = 1

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        tls_header = {
            'tls': 0
        }

        if hasattr(pe, 'DIRECTORY_ENTRY_TLS'):
            tls_header['tls'] = 1

        return tls_header

    def process_raw_features(self, raw_obj):
        return raw_obj

class StringExtractor(FeatureType):
    '''
    문자열 추출
    '''

    name = 'strings'
    dim = 1 + 1 + 1 + 96 + 1 + 1 + 1 + 1 + 1

    def __init__(self):
        super(FeatureType, self).__init__()
        # all consecutive runs of 0x20 - 0x7f that are 5+ characters
        self._allstrings = re.compile(b'[\x20-\x7f]{5,}')
        # occurances of the string 'C:\'.  Not actually extracting the path
        self._paths = re.compile(b'c:\\\\', re.IGNORECASE)
        # occurances of http:// or https://.  Not actually extracting the URLs
        self._urls = re.compile(b'https?://', re.IGNORECASE)
        # occurances of the string prefix HKEY_.  No actually extracting registry names
        self._registry = re.compile(b'HKEY_')
        # crude evidence of an MZ header (dropper?) somewhere in the byte stream
        self._mz = re.compile(b'MZ')

    def raw_features(self, filepath, pe):
        bytez = open(filepath, 'rb').read()        
        allstrings = self._allstrings.findall(bytez)
        if allstrings:
            # statistics about strings:
            string_lengths = [len(s) for s in allstrings]
            avlength = sum(string_lengths) / len(string_lengths)
            # map printable characters 0x20 - 0x7f to an int array consisting of 0-95, inclusive
            as_shifted_string = [b - ord(b'\x20') for b in b''.join(allstrings)]
            c = np.bincount(as_shifted_string, minlength=96)  # histogram count
            # distribution of characters in printable strings
            csum = c.sum()
            p = c.astype(np.float32) / csum
            wh = np.where(c)[0]
            H = np.sum(-p[wh] * np.log2(p[wh]))  # entropy
        else:
            avlength = 0
            c = np.zeros((96,), dtype=np.float32)
            H = 0
            csum = 0

        return {
            'numstrings': len(allstrings),
            'avlength': avlength,
            'printabledist': c.tolist(),  # store non-normalized histogram
            'printables': int(csum),
            'entropy': float(H),
            'paths': len(self._paths.findall(bytez)),
            'urls': len(self._urls.findall(bytez)),
            'registry': len(self._registry.findall(bytez)),
            'MZ': len(self._mz.findall(bytez))
        }

    def process_raw_features(self, raw_obj):
        hist_divisor = float(raw_obj['printables']) if raw_obj['printables'] > 0 else 1.0
        return np.hstack([
            raw_obj['numstrings'], raw_obj['avlength'], raw_obj['printables'],
            np.asarray(raw_obj['printabledist']) / hist_divisor, raw_obj['entropy'], raw_obj['paths'], raw_obj['urls'],
            raw_obj['registry'], raw_obj['MZ']
        ]).astype(np.float32)


class FileEntropy(FeatureType):
    '''
    파일 엔트로피
    '''
    name = 'fileEntropy'
    dim = 1

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        bytez = open(filepath, 'rb').read()
        return [get_entropy(bytez)]

    def process_raw_features(self, raw_obj):
        return list(raw_obj)

class PEFeatureExtractor(object):       
    '''
    특성 추출
    '''
    features = [
        # DOSHEADER(),
        OPTIONALHEADDER(),
        FILEHEADER(),
        ResourceName(),
        GeneralFileInfo(),
        TLSSection(),
        SectionNameInfo(),
        ImportsInfo(),
        ExportsInfo(),
        ByteHistogram(),
        AsmInstruction()
    ]

    dim = sum([fe.dim for fe in features])

    def raw_features(self, filepath):
        try:
            pe = pefile.PE(filepath)
        except pefile.PEFormatError as e:
            raise Exception('PEFormatError : {}'.format(e))
        except Exception as e:
            raise Exception('other Exception : {}'.format(e))
        
        features = {}
        features.update({fe.name: fe.raw_features(filepath, pe) for fe in self.features})

        return features

    def process_raw_features(self, raw_obj):
        feature_vectors = {}
        for fe in self.features:
            feature_vectors = dict(**feature_vectors, **fe.process_raw_features(raw_obj[fe.name]))

        # 확인 필요
        if raw_obj.get('label') != None:
            feature_vectors['label'] = raw_obj['label']

        return feature_vectors

    def feature_vector(self, filepath):
        return self.process_raw_features(self.raw_features(filepath))