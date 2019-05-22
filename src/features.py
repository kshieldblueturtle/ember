#!/usr/bin/python
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
import hashlib
import numpy as np
from sklearn.feature_extraction import FeatureHasher
import time
import pandas as pd
from subprocess import PIPE, Popen
import logging

mylogger = logging.getLogger(__name__)
sh = logging.StreamHandler()
mylogger.addHandler(sh)
mylogger.setLevel(logging.DEBUG)

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


# class ByteHistogram(FeatureType):
#     ''' Byte histogram (count + non-normalized) over the entire binary file '''

#     name = 'histogram'
#     dim = 256

#     def __init__(self):
#         super(FeatureType, self).__init__()

#     def raw_features(self, bytez, lief_binary):
#         counts = np.bincount(np.frombuffer(bytez, dtype=np.uint8), minlength=256)
#         return counts.tolist()

#     def process_raw_features(self, raw_obj):
#         counts = np.array(raw_obj, dtype=np.float32)
#         sum = counts.sum()
#         normalized = counts / sum
#         return normalized


# class ByteEntropyHistogram(FeatureType):
#     ''' 2d byte/entropy histogram based loosely on (Saxe and Berlin, 2015).
#     This roughly approximates the joint probability of byte value and local entropy.
#     See Section 2.1.1 in https://arxiv.org/pdf/1508.03096.pdf for more info.
#     '''

#     name = 'byteentropy'
#     dim = 256

#     def __init__(self, step=1024, window=2048):
#         super(FeatureType, self).__init__()
#         self.window = window
#         self.step = step

#     def _entropy_bin_counts(self, block):
#         # coarse histogram, 16 bytes per bin
#         c = np.bincount(block >> 4, minlength=16)  # 16-bin histogram
#         p = c.astype(np.float32) / self.window
#         wh = np.where(c)[0]
#         H = np.sum(-p[wh] * np.log2(
#             p[wh])) * 2  # * x2 b.c. we reduced information by half: 256 bins (8 bits) to 16 bins (4 bits)

#         Hbin = int(H * 2)  # up to 16 bins (max entropy is 8 bits)
#         if Hbin == 16:  # handle entropy = 8.0 bits
#             Hbin = 15

#         return Hbin, c

#     def raw_features(self, bytez, lief_binary):
#         output = np.zeros((16, 16), dtype=np.int)
#         a = np.frombuffer(bytez, dtype=np.uint8)
#         if a.shape[0] < self.window:
#             Hbin, c = self._entropy_bin_counts(a)
#             output[Hbin, :] += c
#         else:
#             # strided trick from here: http://www.rigtorp.se/2011/01/01/rolling-statistics-numpy.html
#             shape = a.shape[:-1] + (a.shape[-1] - self.window + 1, self.window)
#             strides = a.strides + (a.strides[-1],)
#             blocks = np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)[::self.step, :]

#             # from the blocks, compute histogram
#             for block in blocks:
#                 Hbin, c = self._entropy_bin_counts(block)
#                 output[Hbin, :] += c

#         return output.flatten().tolist()

#     def process_raw_features(self, raw_obj):
#         counts = np.array(raw_obj, dtype=np.float32)
#         sum = counts.sum()
#         normalized = counts / sum
#         return normalized


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
                '.rsrc': 0,
                '.data': 0,
                '.bss': 0,
                '.crt': 0,
                '.rdata': 0,
                '.reloc': 0,
                '.idata': 0,
                '.data': 0,
                '.edata':0,
                '.sdata':0,
                '.ndata':0,
                '.itext':0,
                '.tls': 0,
                '.crt': 0,
                '.bss': 0,
                '.code': 0,
            }
        
        try:
            for section in pe.sections:
                section_name = section.Name.decode('utf-8')
                section_name = section_name.split('\00')[0].lower()
                
                # 섹션 이름이 있으면 딕셔너리 값을 1로 수정
                if section_name in malicious_sections:
                    malicious_sections[section_name] = 1
                    
            return malicious_sections

        except Exception as e:
            return malicious_sections

    def process_raw_features(self, raw_obj):
        features = [
            list(raw_obj.values())
        ]
        return np.hstack(features).astype(np.float32)

class AsmInstruction(FeatureType):
    '''
    1. objdump로 디스어셈블한 후 inustrction만 추출
    2. 정보보호 R&D 대회에서 사용된 어셈블리 언어의 빈도 수를 특성으로 사용
    '''
    name = 'AsmInstruction'
    dim = 55

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        # 빈도수가 높은 명령어
        # To do 직접 특성 공학으로 분석 해야 함 
        malicious_instruction_list = [
            'mov', 'lea', 'andl', 'je', 'jmp', 'add', 'sbb', 'sub', 'int3', 'shr', 'or', 'jb', 'dec', 'decl', 'incl', 'fxch',
            'fsubr', 'jp', 'fstp', 'not', 'pushf', 'xchg', 'adc', 'in', 'clc', '(bad)', 'lcall', 'aaa', 'fiaddl', 'outsl', 'xlat',
            'roll', 'les', 'outsb', 'aam', 'das', 'cld', 'notb', 'iret', 'fstps', 'ss', 'cmc', 'rorb', 'fnsave', 'flds', 'fiadd', 'jno', 
            'incb', 'cmpw', 'adcl', 'movswl', 'shrl', 'cupid', 'fimul', 'rorl'
        ]
        malicious_instruction_dict = {}
        for instruction in malicious_instruction_list:
            malicious_instruction_dict[instruction] = 0

        try:
            # 자식 프로세스로 objdump실행
            # 이후에 메모리 관련 오류가 발생할 가능성이 있음
            #params is "objdump -d {} | grep '[0-9a-z]\{6\}:' | cut -b 33-50 | cut -d ' ' -f 1 | sort | awk NF | uniq".format(target)
            p1 = Popen(['objdump', '-d', filepath], stdout=PIPE) #objdmp -d
            p2 = Popen(['grep', '[0-9a-z]\{6\}:'], stdin=p1.stdout, stdout=PIPE) # grep '[0-9a-z]\{6\}:'
            p3 = Popen(['cut', '-b', '33-50'], stdin=p2.stdout, stdout=PIPE) # cut -b 33-50
            p4 = Popen(['cut', '-d', ' ', '-f', '1'], stdin=p3.stdout, stdout=PIPE) # cut -d ' ' -f 1
            p5 = Popen(['sort'], stdin=p4.stdout, stdout=PIPE) # sort
            p6 = Popen(['awk', 'NF'], stdin=p5.stdout, stdout=PIPE)

            # objudmp 결과 가져오기
            stdout_value = p6.communicate()[0].decode('utf-8')
            asm_instruction_list = stdout_value.rstrip('\n').splitlines()

            asm_instruction_dict = {}
            for instruction in asm_instruction_list:
                if asm_instruction_dict.get(instruction):   
                    asm_instruction_dict[instruction] += 1
                else:
                    asm_instruction_dict[instruction] = 1

            # 빈도 수를 가져오고 리턴
            for key, value in asm_instruction_dict.items():
                if malicious_instruction_dict.get(key) is not None:
                    malicious_instruction_dict[key] += value

            return malicious_instruction_dict
            
        except OSError as e:
            # 패킹된 샘플에 대해서 에러 발생
            mylogger.debug('[Error] Asm Instruction is failed {}'.format(e.errno))
            mylogger.debug('[Error] Asm Instruction is failed {}'.format(e.filename))
            mylogger.debug('[Error] Asm Instruction is failed {}'.format(e.strerror))

            return malicious_instruction_dict

    def process_raw_features(self, raw_obj):
        features = [
            list(raw_obj.values())
        ]
        return np.hstack(features).astype(np.float32)

class ImportsInfo(FeatureType):
    '''
    Import 라이브러리 추출
    '''

    name = 'imports'
    dim = 1280

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        imports = {}
    
        if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                dll = entry.dll.decode('ascii')
                
                if imports.get(dll) is None:                    
                        imports[dll] = []
                        
                for imp in entry.imports:
                    try:
                        function = imp.name.decode('ascii')
                    except:
                        function = str(imp.name)
                    
                    imports[dll].extend([function])
        
            return imports

    def process_raw_features(self, raw_obj):
        try:
            # 라이브러리 이름을 집합으로 추출(중복 제거)
            libraries = list(set(l.lower() for l in raw_obj.keys()))
            # scikit 피쳐해싱(256개 차원)
            libraries_hashed = FeatureHasher(256, input_type='string').transform([libraries]).toarray()[0]

            # API함수 추출        
            functions = []
            for library, value in raw_obj.items():
                for function in value:
                    if function is not None:
                        functions.append(function)                    
            # API함수 피쳐해싱(1024차원)
            function_hashed = FeatureHasher(1024, input_type='string').transform([functions]).toarray()[0]
            featurs = np.hstack([libraries_hashed, function_hashed]).astype(np.float32)

            return featurs
        except Exception as e:
            mylogger.debug('[Error] ImportsInfo process_raw_features Error {}'.format(e))
            return None

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
        isdll = pe.is_dll()

        if isdll is None:
            return []

        # Clipping assumes there are diminishing returns on the discriminatory power of exports beyond
        #  the first 10000 characters, and this will help limit the dataset size
        try:
            functions =  [exp.name.decode('utf-8') for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols]
            
            return functions
        except:
            return []        

    def process_raw_features(self, raw_obj):
        pass
        # exports_hashed = FeatureHasher(128, input_type="string").transform([raw_obj]).toarray()[0]
        # return exports_hashed.astype(np.float32)


class GeneralFileInfo(FeatureType):
    '''
    파일 버전 정보 추출
    '''
    name = 'general'
    dim = 16

    def __init__(self):
        super(FeatureType, self).__init__()
 
    def raw_features(self, filepath, pe):        
        pe_dict = pe.dump_dict()
        
        if pe_dict.get('Version Information') is None:
            fileinfo_header = {        
                'VS_VERSIONINFO_Length': 0,
                'VS_VERSIONINFO_ValueLength': 0,
                'VS_VERSIONINFO_Type': 0,
                'VS_FIXEDFILEINFO_Signature': 0,
                'VS_FIXEDFILEINFO_StrucVersion': 0,
                'VS_FIXEDFILEINFO_FileVersionMS': 0,
                'VS_FIXEDFILEINFO_FileVersionLS': 0,
                'VS_FIXEDFILEINFO_ProductVersionMS': 0,
                'VS_FIXEDFILEINFO_ProductVersionLS': 0,
                'VS_FIXEDFILEINFO_FileFlagsMask': 0,
                'VS_FIXEDFILEINFO_FileFlags': 0,
                'VS_FIXEDFILEINFO_FileOS': 0,
                'VS_FIXEDFILEINFO_FileType': 0,
                'VS_FIXEDFILEINFO_FileSubtype': 0,
                'VS_FIXEDFILEINFO_FileDateMS': 0,  
                'VS_FIXEDFILEINFO_FileDateLS': 0        
            }
            return fileinfo_header
            
        fileinfo_header = {}
        pe_fileinfo_header = pe_dict['Version Information']

        for entry in pe_fileinfo_header[0]:
            title = ''
            for key, value in entry.items():
                if isinstance(value, str):
                    title = value
                    continue

                fileinfo_header[title + '_' + key] = value['Value']

        return fileinfo_header

    def process_raw_features(self, raw_obj):
        features = [
            list(raw_obj.values())
        ]
        return np.hstack(features).astype(np.float32)

class HeaderFileInfo(FeatureType):
    '''
    DOS Header, Optiona Header, File Header 추출
    '''

    name = 'header'
    dim = 56

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        raw_obj = {}

        pe_dict = pe.dump_dict()
        pe_dos_header = pe_dict['DOS_HEADER']
        
        # dos 헤더        
        dos_header = {}
        del pe_dos_header['Structure']

        for key, value in pe_dos_header.items():
            dos_header[key] = value['Value']

        dos_header['e_res'] = int.from_bytes(pe.DOS_HEADER.e_res, byteorder='little')
        dos_header['e_res2'] = int.from_bytes(pe.DOS_HEADER.e_res2, byteorder='little')
        
        # file 헤더
        file_header = {}
        
        pe_file_header = pe_dict['FILE_HEADER']
        del pe_file_header['Structure']

        for key, value in pe_file_header.items():
            file_header[key] = value['Value']

        file_header['TimeDateStamp'] = pe.FILE_HEADER.TimeDateStamp

        # optional 헤더
        optional_header = {}

        pe_optional_header = pe_dict['OPTIONAL_HEADER']
        del pe_optional_header['Structure']

        for key, value in pe_optional_header.items():
            optional_header[key] = value['Value']

        # 종합       
        raw_obj['dos_header'] = dos_header
        raw_obj['optional_header'] = optional_header
        raw_obj['file_header'] = file_header

        return raw_obj

    def process_raw_features(self, raw_obj):
        features = [
            list(raw_obj['dos_header'].values()) +
            list(raw_obj['optional_header'].values()) +
            list(raw_obj['file_header'].values())
        ]

        return np.hstack(features).astype(np.float32)

class ResourceName(FeatureType):
    '''
    리소스 이름 유/무
    '''
    name = 'resourceName'
    dim = 8

    def __init__(self):
        super(FeatureType, self).__init__()

    def raw_features(self, filepath, pe):
        maliciou_resource_name = {
            'RT_STRING': 0,
            'RT_DIALOG': 0,
            'RT_GROUP_ICON': 0,
            'RT_VERSION': 0,
            'RT_BITMAP': 0,
            'RT_RCDATA': 0,
            'RT_ICON': 0,
            'RT_GROUP_CURSOR': 0
        }
        
        if hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE') is False:
            return maliciou_resource_name

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
            
        for resourcename in resource_name:
            if maliciou_resource_name.get(resourcename) is not None:
                maliciou_resource_name[resourcename] = 1
                
        return maliciou_resource_name

    def process_raw_features(self, raw_obj):
        features = [
            list(raw_obj.values())
        ]

        return np.hstack(features).astype(np.float32)

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
        features = [
            list(raw_obj.values())
        ]

        return np.hstack(features).astype(np.float32)  

# class StringExtractor(FeatureType):
#     ''' Extracts strings from raw byte stream '''

#     name = 'strings'
#     dim = 1 + 1 + 1 + 96 + 1 + 1 + 1 + 1 + 1

#     def __init__(self):
#         super(FeatureType, self).__init__()
#         # all consecutive runs of 0x20 - 0x7f that are 5+ characters
#         self._allstrings = re.compile(b'[\x20-\x7f]{5,}')
#         # occurances of the string 'C:\'.  Not actually extracting the path
#         self._paths = re.compile(b'c:\\\\', re.IGNORECASE)
#         # occurances of http:// or https://.  Not actually extracting the URLs
#         self._urls = re.compile(b'https?://', re.IGNORECASE)
#         # occurances of the string prefix HKEY_.  No actually extracting registry names
#         self._registry = re.compile(b'HKEY_')
#         # crude evidence of an MZ header (dropper?) somewhere in the byte stream
#         self._mz = re.compile(b'MZ')

#     def raw_features(self, bytez, lief_binary):
#         allstrings = self._allstrings.findall(bytez)
#         if allstrings:
#             # statistics about strings:
#             string_lengths = [len(s) for s in allstrings]
#             avlength = sum(string_lengths) / len(string_lengths)
#             # map printable characters 0x20 - 0x7f to an int array consisting of 0-95, inclusive
#             as_shifted_string = [b - ord(b'\x20') for b in b''.join(allstrings)]
#             c = np.bincount(as_shifted_string, minlength=96)  # histogram count
#             # distribution of characters in printable strings
#             csum = c.sum()
#             p = c.astype(np.float32) / csum
#             wh = np.where(c)[0]
#             H = np.sum(-p[wh] * np.log2(p[wh]))  # entropy
#         else:
#             avlength = 0
#             c = np.zeros((96,), dtype=np.float32)
#             H = 0
#             csum = 0

#         return {
#             'numstrings': len(allstrings),
#             'avlength': avlength,
#             'printabledist': c.tolist(),  # store non-normalized histogram
#             'printables': int(csum),
#             'entropy': float(H),
#             'paths': len(self._paths.findall(bytez)),
#             'urls': len(self._urls.findall(bytez)),
#             'registry': len(self._registry.findall(bytez)),
#             'MZ': len(self._mz.findall(bytez))
#         }

#     def process_raw_features(self, raw_obj):
#         hist_divisor = float(raw_obj['printables']) if raw_obj['printables'] > 0 else 1.0
#         return np.hstack([
#             raw_obj['numstrings'], raw_obj['avlength'], raw_obj['printables'],
#             np.asarray(raw_obj['printabledist']) / hist_divisor, raw_obj['entropy'], raw_obj['paths'], raw_obj['urls'],
#             raw_obj['registry'], raw_obj['MZ']
#         ]).astype(np.float32)

class PEFeatureExtractor(object):    
    '''
    특성 추출
    '''
    features = [
        HeaderFileInfo(), SectionNameInfo(), GeneralFileInfo(), ResourceName(), TLSSection(), AsmInstruction(),
        #ImportsInfo() , ExportsInfo()
    ]
    #features = [ExportsInfo()]
    dim = sum([fe.dim for fe in features])

    def raw_features(self, filepath):
        try:
            pe = pefile.PE(filepath)
        except pefile.PEFormatError as excp:
            mylogger.debug('PEFormatError : {}'.format(excp))
            pe = None
        except Exception as e:  # everything else (KeyboardInterrupt, SystemExit, ValueError):
            mylogger.debug('other Exception: {}'.format(e))
            raise            
        
        features = {} #appeared
        features.update({fe.name: fe.raw_features(filepath, pe) for fe in self.features})

        return features

    def process_raw_features(self, raw_obj):
        feature_vectors = [fe.process_raw_features(raw_obj[fe.name]) for fe in self.features]
        return np.hstack(feature_vectors).astype(np.float32)

    def feature_vector(self, filepath):
        return self.process_raw_features(self.raw_features(filepath))