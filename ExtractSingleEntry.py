from dataclasses import dataclass, fields, field
import numpy as np
from typing import List
import sys,os
sys.path.append(os.getcwd()+"/ThirdParty")
import gf
from ctypes import cdll, c_char_p, create_string_buffer
from Crypto.Cipher import AES
import binascii
import io
import fnmatch
import time,ast

#path = "E:\SteamLibrary\steamapps\common\Destiny2\packages" #Path to your packages folder.
path="E:\SteamLibrary\steamapps\common\Destiny2\packages"
custom_direc = os.getcwd()+"/out/" #Where you want the bin files to go
oodlepath = os.getcwd()+"/ThirdParty/oo2core_9_win64.dll" #Path to Oodle DLL in Destiny 2/bin/x64.dle DLL in Destiny 2/bin/x64.


def stripZeros(txt):
    if txt == "0000":
        return("0")
    elif txt == "00000000":
        return("0")
    elif txt == "00":
        return("0")
    else:
        temp=list(txt)
        count=0
        index=0
        ###print(temp)
        for char in temp:
            if char == "0":
                index+=1
                
            else:
                break
        ###print("".join(temp[index:]))
        return str("".join(temp[index:]))

def get_file_typename(file_type, file_subtype, ref_id, ref_pkg):
    if file_type == 8:
        return '8080xxxx Structure File'
    elif file_type == 33:
        return 'DirectX Bytecode Header'
    elif file_type == 41:
        return 'DirectX Bytecode Data'
    else:
        return 'Unknown'


def calculate_pkg_id(entry_a_data):
    ref_pkg_id = (entry_a_data >> 13) & 0x3FF
    ref_unk_id = entry_a_data >> 23

    ref_digits = ref_unk_id & 0x3
    if ref_digits == 1:
        return ref_pkg_id
    else:
        return ref_pkg_id | 0x100 << ref_digits


# All of these decoding functions use the information from formats.c on how to decode each entry
def decode_entry_a(entry_a_data):
    ref_id = entry_a_data & 0x1FFF
    # ref_pkg_id = (entry_a_data >> 13) & 0x3FF
    ref_pkg_id = calculate_pkg_id(entry_a_data)
    ref_unk_id = (entry_a_data >> 23) & 0x1FF

    return np.uint16(ref_id), np.uint16(ref_pkg_id), np.uint16(ref_unk_id)


def decode_entry_b(entry_b_data):
    file_subtype = (entry_b_data >> 6) & 0x7
    file_type = (entry_b_data >> 9) & 0x7F
    ###print(entry_b_data)
    return np.uint8(file_type), np.uint8(file_subtype)


def decode_entry_c(entry_c_data):
    starting_block = entry_c_data & 0x3FFF
    ###print(starting_block)
    starting_block_offset = ((entry_c_data >> 14) & 0x3FFF) << 4
    return starting_block, starting_block_offset


def decode_entry_d(entry_c_data, entry_d_data):
    file_size = (entry_d_data & 0x3FFFFFF) << 4 | (entry_c_data >> 28) & 0xF
    unknown = (entry_d_data >> 26) & 0x3F

    return np.uint32(file_size), np.uint8(unknown)


class OodleDecompressor:
    """
    Oodle decompression implementation.
    Requires Windows and the external Oodle library.
    """

    def __init__(self, library_path: str) -> None:
        """
        Initialize instance and try to load the library.
        """
        if not os.path.exists(library_path):
            raise Exception("Could not open Oodle DLL, make sure it is configured correctly.")

        try:
            self.handle = cdll.LoadLibrary(library_path)
        except OSError as e:
            raise Exception(
                "Could not load Oodle DLL, requires Windows and 64bit python to run."
            ) from e

    def decompress(self, payload: bytes) -> bytes:
        """
        Decompress the payload using the given size.
        """
        force_size = int('0x40000', 16)
        output = create_string_buffer(force_size)
        self.handle.OodleLZ_Decompress(
            c_char_p(payload), len(payload), output, force_size,
            0, 0, 0, None, None, None, None, None, None, 3)
        return output.raw


class PkgHeader:
    def __init__(self, pbin):
        self.PackageID = gf.get_int16(pbin, 0x10)
        self.PackageIDH = gf.fill_hex_with_zeros(hex(self.PackageID)[2:], 4)
        self.PatchID = gf.get_int16(pbin, 0x30)

        self.EntryTableOffset = gf.get_int32(pbin, 0x44)
        # self.EntryTableLength = get_int_hex(0x48, phex)
        self.EntryTableSize = gf.get_int32(pbin, 0x60)
        self.EntryTableLength = self.EntryTableSize * 0x16

        self.BlockTableSize = gf.get_int32(pbin, 0x68)
        self.BlockTableOffset = gf.get_int32(pbin, 0x6C)


@dataclass
class SPkgEntry:
    EntryA: np.uint32 = np.uint32(0)
    EntryB: np.uint32 = np.uint32(0)
    EntryC: np.uint32 = np.uint32(0)
    EntryD: np.uint32 = np.uint32(0)

    '''
     [             EntryD              ] [             EntryC              ] 
     GGGGGGFF FFFFFFFF FFFFFFFF FFFFFFFF FFFFEEEE EEEEEEEE EEDDDDDD DDDDDDDD

     [             EntryB              ] [             EntryA              ]
     00000000 00000000 TTTTTTTS SS000000 CCCCCCCC CBBBBBBB BBBAAAAA AAAAAAAA

     A:RefID: EntryA & 0x1FFF
     B:RefPackageID: (EntryA >> 13) & 0x3FF
     C:RefUnkID: (EntryA >> 23) & 0x1FF
     D:StartingBlock: EntryC & 0x3FFF
     E:StartingBlockOffset: ((EntryC >> 14) & 0x3FFF) << 4
     F:FileSize: (EntryD & 0x3FFFFFF) << 4 | (EntryC >> 28) & 0xF
     G:Unknown: (EntryD >> 26) & 0x3F

     Flags (Entry B)
     S:SubType: (EntryB >> 6) & 0x7
     T:Type:  (EntryB >> 9) & 0x7F
    '''


@dataclass
class SPkgEntryDecoded:
    ID: np.uint16 = np.uint16(0)
    FileName: str = ''
    FileType: str = ''
    RefID: np.uint16 = np.uint16(0)  # uint13
    RefPackageID: np.uint16 = np.uint16(0)  # uint9
    RefUnkID: np.uint16 = np.uint16(0)  # uint10
    Type: np.uint8 = np.uint8(0)  # uint7
    SubType: np.uint8 = np.uint8(0)  # uint3
    StartingBlock: np.uint16 = np.uint16(0)  # uint14
    StartingBlockOffset: np.uint32 = np.uint32(0)  # uint14
    FileSize: np.uint32 = np.uint32(0)  # uint30
    Unknown: np.uint8 = np.uint8(0)  # uint6
    EntryA: int = ''


@dataclass
class SPkgEntryTable:
    Entries: List[SPkgEntryDecoded] = field(default_factory=list)  # This list of of length [EntryTableSize]


@dataclass
class SPkgBlockTableEntry:
    ID: int = 0  # 0x0
    Offset: np.uint32 = np.uint32(0)  # 0x4
    Size: np.uint32 = np.uint32(0)  # 0x8
    PatchID: np.uint16 = np.uint16(0)  # 0xC
    Flags: np.uint16 = np.uint16(0)  # 0xE
    Hash: List[np.uint8] = field(default_factory=list)  # [0x14] = 20  # 0x22
    GCMTag: List[np.uint8] = field(default_factory=list)  # [0x10] = 16  # 0x32


@dataclass
class SPkgBlockTable:
    Entries: List[SPkgBlockTableEntry] = field(default_factory=list)  # This list of length [BlockTableSize]


class Package:
    BLOCK_SIZE = int('0x40000', 16)

    AES_KEY_0 = [
        "0xD6", "0x2A", "0xB2", "0xC1", "0x0C", "0xC0",
        "0x1B", "0xC5", "0x35", "0xDB", "0x7B",
        "0x86", "0x55", "0xC7", "0xDC", "0x3B",
    ]
    AES_KEY_1 = [
        "0x3A", "0x4A", "0x5D", "0x36", "0x73", "0xA6",
        "0x60", "0x58", "0x7E", "0x63", "0xE6",
        "0x76", "0xE4", "0x08", "0x92", "0xB5",
    ]
    AES_KEY_2 = [
        "0xA4", "0xDD", "0x6C", "0x58", "0x9D", "0x68",
        "0xA7", "0x56", "0xFE", "0x72", "0x3A", "0x31",
        "0x07","0x93","0x8B","0xD1",
    ]
   
    
    def __init__(self, package_directory,EntryToGet,ReturnData):
        self.package_directory = package_directory
        if '_en_' in self.package_directory:
            self.t_package_id = self.package_directory[-13:-9]
        else:
            self.t_package_id = self.package_directory[-10:-6]
        self.package_header = None
        self.entry_table = None
        self.block_table = None
        self.all_patch_ids = []
        self.max_pkg_bin = None
        self.nonce = None
        self.aes_key_0 = binascii.unhexlify(''.join([x[2:] for x in self.AES_KEY_0]))
        self.aes_key_1 = binascii.unhexlify(''.join([x[2:] for x in self.AES_KEY_1]))
        self.aes_key_2 = binascii.unhexlify(''.join([x[2:] for x in self.AES_KEY_2]))
        self.EntryToGet=EntryToGet
        self.ReturnData=ReturnData
        ##print(self.EntryToGet)


    def extract_package(self, custom_direc,Entry,Output, extract=True, largest_patch=True):
        self.get_all_patch_ids()
        self.Output=Output
        if largest_patch:
            self.set_largest_patch_directory()
        ##print(f"Extracting files for {self.package_directory}")

        self.max_pkg_bin = open(self.package_directory, 'rb').read()
        self.package_header = self.get_header()
        self.entry_table = self.get_entry_table()
        self.block_table = self.get_block_table()

        if self.ReturnData:
            self.process_blocks(custom_direc)

    def get_all_patch_ids(self):
        all_pkgs = [x for x in os.listdir(self.package_directory.split('/w64')[0]) if self.t_package_id in x]
        all_pkgs.sort()
        self.all_patch_ids = [int(x[-5]) for x in all_pkgs]

    def set_largest_patch_directory(self):
        if 'unp1' in self.package_directory:
            all_pkgs = [x for x in os.listdir(self.package_directory.split('/w64')[0]) if x[:-6] in self.package_directory]
        else:
            all_pkgs = [x for x in os.listdir(self.package_directory.split('/w64')[0]) if self.t_package_id in x]
        sorted_all_pkgs, _ = zip(*sorted(zip(all_pkgs, [int(x[-5]) for x in all_pkgs])))
        self.package_directory = self.package_directory.split('/w64')[0] + '/' + sorted_all_pkgs[-1]
        return

    def get_header(self):
        """
        Given a pkg directory, this gets the header data and uses SPkgHeader() struct to fill out the fields of that struct,
        making a header struct with all the correct data.
        :param pkg_dir:
        :return: the pkg header struct
        """
        header_length = int('0x16F', 16)
        # The header data is 0x16F bytes long, so we need to x2 as python reads each nibble not each byte
        header = self.max_pkg_bin[:header_length]
        pkg_header = PkgHeader(header)
        ###print(pkg_header)
        return pkg_header

    def get_entry_table(self):
        """
        After we've got the header data for each pkg we know where the entry table is. Using this information, we take each
        row of 16 bytes (128 bits) as an entry and separate the row into EntryA, B, C, D for decoding
        :param pkg_data: the hex data from pkg
        :param entry_table_size: how long this entry table is in the pkg data
        :param entry_table_offset: hex offset for where the entry table starts
        :return: the entry table made
        """

        entry_table = SPkgEntryTable()
        entries_to_decode = []
        entry_table_start = self.package_header.EntryTableOffset
        entry_table_data = self.max_pkg_bin[entry_table_start:entry_table_start+self.package_header.EntryTableLength]
       
        i=self.EntryToGet*16
        entry = SPkgEntry(gf.get_int32(entry_table_data, i),
                            gf.get_int32(entry_table_data, i+4),
                            gf.get_int32(entry_table_data, i+8),
                            gf.get_int32(entry_table_data, i+12))
        entries_to_decode.append(entry)
        entry_table.Entries = self.decode_entries(entries_to_decode)
        ###print(len(entries_to_decode))
        return entry_table

    def decode_entries(self, entries_to_decode):
        """
        Given the entry table (and hence EntryA, B, C, D) we can decode each of them into data about each (file? block?)
        using bitwise operators.
        :param entry_table: the entry table struct to decode
        :return: array of decoded entries as struct SPkgEntryDecoded()
        """
        ###print(entries_to_decode)
        entries = []
        count = 0
        ##print(self.EntryToGet)
        for entry in entries_to_decode:
           
            # ##print("\n\n")
            #useful=["0x808045eb","0x808045f0","0x808045f7","0x808097b8","0x80809345","0x80809ec5","0x8080986a","0x808090d5","0x80808e8b","0x80808c0d","0x808099f1","0x80805a09","0x80809fb8","0x80800065","0x80809b06","0x80800000","0x80808e8e","0x808045f0","0x80808ec7"]
            ref_id, ref_pkg_id, ref_unk_id = decode_entry_a(entry.EntryA)
            if self.ReturnData == False:
                global DataToWrite
                DataToWrite=hex(entry.EntryA)
                break
            
            ##print("ran")
            #if hex(entry.EntryA) in useful:
            file_type, file_subtype = decode_entry_b(entry.EntryB)
            starting_block, starting_block_offset = decode_entry_c(entry.EntryC)
            file_size, unknown = decode_entry_d(entry.EntryC, entry.EntryD)
            file_name = f"{self.package_header.PackageIDH}-{gf.fill_hex_with_zeros(hex(self.EntryToGet)[2:], 4)}"
            file_typename = get_file_typename(file_type, file_subtype, ref_id, ref_pkg_id)

            decoded_entry = SPkgEntryDecoded(np.uint16(self.EntryToGet), file_name, file_typename,
                                             ref_id, ref_pkg_id, ref_unk_id, file_type, file_subtype, starting_block,
                                             starting_block_offset, file_size, unknown, hex(entry.EntryA))
            entries.append(decoded_entry)
            ###print("Here")
            #if len(entries) > 50:
             #   ##print(entries)
              #  time.sleep(60)
            count += 1
            
            #(count)
        return entries

    def get_block_table(self):
        block_table = SPkgBlockTable()
        block_table_data = self.max_pkg_bin[self.package_header.BlockTableOffset:self.package_header.BlockTableOffset + self.package_header.BlockTableSize*48]
        reduced_bt_data = block_table_data
        for i in range(self.package_header.BlockTableSize):
            block_entry = SPkgBlockTableEntry(ID=i)
            for fd in fields(block_entry):
                if fd.type == np.uint32:
                    value = gf.get_int32(reduced_bt_data, 0)
                    setattr(block_entry, fd.name, value)
                    reduced_bt_data = reduced_bt_data[4:]
                elif fd.type == np.uint16:
                    value = gf.get_int16(reduced_bt_data, 0)
                    setattr(block_entry, fd.name, value)
                    reduced_bt_data = reduced_bt_data[2:]
                elif fd.type == List[np.uint8] and fd.name == 'Hash':
                    flipped = gf.get_flipped_bin(reduced_bt_data, 20)
                    value = [c for c in flipped]
                    setattr(block_entry, fd.name, value)
                    reduced_bt_data = reduced_bt_data[20:]
                elif fd.type == List[np.uint8] and fd.name == 'GCMTag':
                    flipped = gf.get_flipped_bin(reduced_bt_data, 16)
                    value = [c for c in flipped]
                    setattr(block_entry, fd.name, value)
                    reduced_bt_data = reduced_bt_data[16:]
            block_table.Entries.append(block_entry)
        return block_table

    def process_blocks(self, custom_direc):
        all_pkg_bin = []
        for i in self.all_patch_ids:
            bin_data = open(f'{self.package_directory[:-6]}_{i}.pkg', 'rb').read()
            all_pkg_bin.append(bin_data)

        self.set_nonce()
        ###print(all_pkg_bin)
        self.output_files(all_pkg_bin, custom_direc)

    def decrypt_block(self, block, block_bin):
        if block.Flags & 0x4:
            key = self.aes_key_1
        elif block.Flags & 0x8:
            key = self.aes_key_2
        else:
            key = self.aes_key_0
        cipher = AES.new(key, AES.MODE_GCM, nonce=self.nonce)
        plaintext = cipher.decrypt(block_bin)
        ###print(str(plaintext).split("\\x"))
        #time.sleep(10)
        return plaintext

    def set_nonce(self):
        nonce_seed = [
            0x84, 0xDF, 0x11, 0xC0,
            0xAC, 0xAB, 0xFA, 0x20,
            0x33, 0x11, 0x26, 0x99,
        ]

        nonce = nonce_seed
        package_id = self.package_header.PackageID
        #print(package_id)
        nonce[0] ^= (package_id >> 8) & 0xFF
        nonce[1] = 0xEA
        nonce[11] ^= package_id & 0xFF


        self.nonce = binascii.unhexlify(''.join([gf.fill_hex_with_zeros(hex(x)[2:], 2) for x in nonce]))
        ##print(self.nonce)

    def decompress_block(self, block_bin):
        decompressor = OodleDecompressor(oodlepath)
        decompressed = decompressor.decompress(block_bin)
        return decompressed

    def output_files(self, all_pkg_bin, custom_direc):
        for entry in self.entry_table.Entries[::-1]:
            ###print(entry)
            current_block_id = entry.StartingBlock
            block_offset = entry.StartingBlockOffset
            block_count = int(np.floor((block_offset + entry.FileSize - 1) / self.BLOCK_SIZE))
            ##print(str(block_offset)+" - "+str(block_count))
            last_block_id = current_block_id + block_count
            file_buffer = b''  # string of length entry.Size
            while current_block_id <= last_block_id:
                current_block = self.block_table.Entries[current_block_id]
                if current_block.PatchID not in self.all_patch_ids:
                    ##print(f"Missing PatchID {current_block.PatchID}")
                    return
                current_pkg_data = all_pkg_bin[self.all_patch_ids.index(current_block.PatchID)]
                current_block_bin = current_pkg_data[current_block.Offset:current_block.Offset + current_block.Size]
                # We only decrypt/decompress if need to
                if current_block.Flags & 0x2:
                    # ##print('Going to decrypt')
                    current_block_bin = self.decrypt_block(current_block, current_block_bin)
                if current_block.Flags & 0x1:
                    # ##print(f'Decompressing block {current_block.ID}')
                    current_block_bin = self.decompress_block(current_block_bin)
                if current_block_id == entry.StartingBlock:
                    file_buffer = current_block_bin[block_offset:]
                else:
                    file_buffer += current_block_bin
                ###print(file_buffer)
                current_block_id += 1
            fileFormat=""
            #print(entry.EntryA)
            #time.sleep(5)
            
            
            fileFormat=".bin"
            #fileFormat=".bin"
            #if entry.FileName.upper() == "03C3-16EC":
                ###print(entry.EntryA)
                ###print(f'{custom_direc}{self.package_directory.split("/w64")[-1][1:-6]}/{entry.FileName.upper()}'+fileFormat)
            if fileFormat == ".bin":
                #try:
                #    os.makedirs(custom_direc + self.package_directory.split('/w64')[-1][1:-6])
                #except FileExistsError:
                #    pass
                
                # ##print(entry.FileSize)
                global DataToWrite
                DataToWrite=file_buffer[:entry.FileSize]
                if self.Output == True:
                    file = io.FileIO(f'{custom_direc}/{entry.FileName.upper()}'+fileFormat, 'wb')
                    if entry.FileSize != 0:
                        writer = io.BufferedWriter(file, buffer_size=entry.FileSize)
                        writer.write(file_buffer[:entry.FileSize])
                        writer.flush()
                    else:
                        with open(f'{custom_direc}/{entry.FileName.upper()}'+fileFormat, 'wb') as f:
                            f.write(file_buffer[:entry.FileSize])
                    #print(str(entry.Type)+" : "+str(entry.SubType))
                
            ###print(f"Wrote to {entry.FileName} successfully")

def GetEntryA(path, custom_direc,package,entry):
    single_pkgs = dict()
    #entry="0bc8"
    entrytoget=ast.literal_eval("0x"+stripZeros(entry))
    single_pkgs[package[:-6]] = package
    ##print(single_pkgs)
    ###print(single_pkgs.items())
    for pkg, pkg_full in single_pkgs.items():
        pkg = Package(f'{path}/{pkg_full}',entrytoget,False)
        pkg.extract_package(custom_direc,entrytoget,False,extract=True)
    ##print(DataToWrite)
    return DataToWrite
def unpack_entry(path, custom_direc,package,entry):
    i=0
    
    ###print(all_packages)
    single_pkgs = dict()
    #entry="0bc8"
    entrytoget=ast.literal_eval("0x"+stripZeros(entry))
    single_pkgs[package[:-6]] = package
    ##print(single_pkgs)
    ###print(single_pkgs.items())   
    for pkg, pkg_full in single_pkgs.items():
        pkg = Package(f'{path}/{pkg_full}',entrytoget,True)
        pkg.extract_package(custom_direc,entrytoget,False,extract=True)
    Data=binascii.hexlify(DataToWrite).decode()
    return Data
def unpack_entry_ext(path, custom_direc,package,entry):
    i=0
    ##print(package)
    ##print(entry)
    ###print(all_packages)
    single_pkgs = dict()
    #entry="0bc8"
    entrytoget=ast.literal_eval("0x"+stripZeros(entry))
    single_pkgs[package[:-6]] = package
    ##print(single_pkgs)
    ###print(single_pkgs.items())
    for pkg, pkg_full in single_pkgs.items():
        pkg = Package(f'{path}/{pkg_full}',entrytoget,True)
        pkg.extract_package(custom_direc,entrytoget,True,extract=True)
    #Data=binascii.hexlify(DataToWrite).decode()
def GetTypes(path, custom_direc,package,entry):
    single_pkgs = dict()
    #entry="0bc8"
    entrytoget=ast.literal_eval("0x"+stripZeros(entry))
    single_pkgs[package[:-6]] = package
    ##print(single_pkgs)
    ###print(single_pkgs.items())
    for pkg, pkg_full in single_pkgs.items():
        pkg = Package(f'{path}/{pkg_full}',entrytoget,False)
        pkg.extract_package(custom_direc,entrytoget,False,extract=True)
    ##print(DataToWrite)
    return DataToWrite
#unpack_entry_ext(path,custom_direc,"w64_sr_globals_012d_4.pkg","0022")
