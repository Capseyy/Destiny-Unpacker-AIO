from dataclasses import dataclass, fields, field
import os, sys, shutil
sys.path.append(os.getcwd()+"/ThirdParty")
import numpy as np
from typing import List
import gf, subprocess
import tkinter.messagebox
from ctypes import cdll, c_char_p, create_string_buffer , c_uint32
from Crypto.Cipher import AES
import binascii
import io
import fnmatch
import time,ast,struct
import FbxCommon
from ast import literal_eval
from tkinter import *
from tkinter import ttk
import fbx, ExtractSingleEntry
from fbx import *
from fbx import FbxManager
from functools import partial
global custom_direc,useful ,path,Hash64Data
path = "E:\SteamLibrary\steamapps\common\Destiny2\packages" #Path to your packages folder.
#path="C:\Program Files (x86)\Steam\steamapps\common\Destiny2\packages"
#path="D:/oldd2/packages"
custom_direc = os.getcwd()+"/out" #Where you want the bin files to go
oodlepath = os.getcwd()+"/ThirdParty/oo2core_9_win64.dll" #Path to Oodle DLL in Destiny 2/bin/x64.dle DLL in Destiny 2/bin/x64.
useful=[]

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
        #print(temp)
        for char in temp:
            if char == "0":
                index+=1
                
            else:
                break
        #print("".join(temp[index:]))
        return str("".join(temp[index:]))
def ReadHash64():
    file=open(os.getcwd()+"/cache/h64.txt","r")
    data=file.read()
    Hash64Data=data.split("\n")
    return Hash64Data
            
def hex_to_little_endian(hex_string):
    little_endian_hex = bytearray.fromhex(hex_string)[::-1]
    return little_endian_hex
def hex_to_big_endian(hex_string):
    return bytearray.fromhex(hex_string)

def Package_ID(Hash):
    ID = (Hash >> 13) & 0xFFF

    if (ID & 0x800) > 0 and (ID & 0x400) > 0:
        return ID & 0xBFF
    elif (ID & 0x400) == 0:
        return (ID & 0x3FF) | 0x400
    elif (ID & 0x200) == 0:
        return ID & 0x1FF
    elif (ID & 0x400) > 0:
        return ID & 0x3FF
    else:
        raise Exception("Unknown package encoding configuration.")
def Entry_ID(Hash):
    return Hash & 0x1FFF
def Hex_String(Num):
    Hex_Digits = "0123456789abcdef"
    return ''.join([
        Hex_Digits[(Num & 0xF000) >> 12],
        Hex_Digits[(Num & 0xF00) >> 8],
        Hex_Digits[(Num & 0xF0) >> 4],
        Hex_Digits[Num & 0xF]
    ])

class File:
    def __init__(self,Name,FileType,StrData,ActName):
        self.Name=Name
        self.FileType=FileType
        #self.Tags=[]
        self.Data=[]
        self.StrData=StrData
        self.Hashes=[]
        self.Strings=[]
        self.ReadFile()
        #self.FindTags()
        #self.ReadFile64()
        self.FindHashes()
        self.ActName=ActName
        self.QueHashes=[]
        self.Banks=[]
        output=open(os.getcwd()+"/cache/directive.txt","a")
        output.write("Activity File: \n")
        output.write(self.Name+"\n")
        output.close()
    def GetDialogue(self):
        Lines=[self.Raw[i:i+32] for i in range(0, len(self.Raw), 32)]
        count=0
        print("finding dial")
        found=False
        for Line in Lines:
            Hashes=[Line[i:i+8] for i in range(0, len(Line), 8)]
            for Hash in Hashes:
                if Hash.lower() == "b7978080":
                    Hash64=Lines[count+1][16:]
                    found=True
            count+=1
        if found == True:
            print(Hash64)
            flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash64))).decode('utf-8')
            HashToFind="0x"+flipped
            print(HashToFind)
            Dat64=ReadHash64()
            found=False
            for Hash in Dat64:
                temp=Hash.split(": ")
                if HashToFind == temp[0]:
                    DiaTable=temp[1]
                    print("FOUND DIALOGUE")
                    found=True
                    break
            if found == True:
                dec = ast.literal_eval(DiaTable)
                PkgID=Hex_String(Package_ID(dec))
                EntryID=Hex_String(Entry_ID(dec))
                DirName=PkgID+"-"+EntryID
                output=open(os.getcwd()+"/cache/directive.txt","a")
                output.write("Dialogue Table \n")
                #output.write(DirName+".tab \n")
                output.write(DirName+".tab \n")
                    
                print("try")
                with open(custom_direc+"/audio/"+DirName+".tab", 'rb') as f:
                    s = binascii.hexlify(bytes(f.read())).decode()
                    Data=[s[i:i+8] for i in range(0, len(s), 8)]
                    count=0
                    lines=[]
                    for Hash in Data:
                        #print(Hash)
                       
                        flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8')
                        #print(flipped)
                        dec = ast.literal_eval("0x"+flipped)
                        #print(dec)
                        #for Dat in StrData:
                            #if Dat[0] == str(dec):
                                #output.write(Dat[0]+" : "+Dat[1]+"\n")
                        ans=binary_search(self.StrData,int(dec))
                        #print(ans)
                        if str(ans) != "-1":
                            #print("written")
                            output.write(str(self.StrData[ans][1])+" : "+self.StrData[ans][2]+"\n")
                    f.close()
                output.write("\n\n\n")
                        
                count+=1
                output.close()
        print("done dia")        
                
                    
    def ReadFile(self):
        File=open(custom_direc+"/"+self.Name,"rb")
        Data=binascii.hexlify(bytes(File.read())).decode()
        self.Raw=Data
        self.Data=[Data[i:i+8] for i in range(0, len(Data), 8)]
        File.close()
    def ReadFile64(self):
        File=open(custom_direc+"/"+self.Name,"rb")
        Data=binascii.hexlify(bytes(File.read())).decode()
        temp=[Data[i:i+16] for i in range(0, len(Data), 16)]
        File.close()
        for Hash in temp:
            flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8')
            dec = "0x"+flipped
            Found=False
            #print(dec)
            for Line in Hash64Data:
                Lines=Line.split(": ")
                #print(Lines)
                if Lines[0] == str(dec):
                    Found=True
                    AudioFile=Lines[1]
                    #print(str(AudioFile)+"    64")
                    new=literal_eval(AudioFile)
                    PkgID=Hex_String(Package_ID(new))
                    EntryID=Hex_String(Entry_ID(new))
                    DirName=PkgID.upper()+"-"+EntryID.upper()+".bin"
                    print(DirName)

    def FindTags(self):
        Count=0
        for Hash in self.Data:
            Hash=[Hash[i:i+4] for i in range(0, len(Hash), 4)]
            try:
                Except=Hash[1]
            except IndexError:
                break
            else:
                if Hash[1] == "8080":
                    self.Tags.append(["".join(Hash),Count])
        
            Count+=4
    def FindHashes(self):
        Count=0
        Hashes=[]
        print("FindingHashes")
        #print(self.Name)
        for Hash in self.Data:
            Dir=False
            Mus=False
            Flip=binascii.hexlify(hex_to_little_endian(Hash)).decode()
            #print(Flip)
            Data=[Flip[i:i+2] for i in range(0, len(Flip), 2)]
            #print(Data)
            if (Data[0] == "80") and (Data[1] != "80"):
                Hashes.append("".join(Data))
                Hash="".join(Data)
                hash2="0x"+Hash
                new=literal_eval(hash2)
                PkgID=Hex_String(Package_ID(new))
                EntryID=Hex_String(Entry_ID(new))
                DirName=PkgID.upper()+"-"+EntryID.upper()+".directive"
                MusName=PkgID.upper()+"-"+EntryID.upper()+".mus"
                for File in os.listdir(custom_direc):
                    if File.lower() == DirName.lower():
                        Dir=True
                    if File.lower() == MusName.lower():
                        Mus=True
                if Dir == True and Mus == True:
                    break
            if (Data[0] == "81"):
                Hashes.append("".join(Data))
                Hash="".join(Data)
                hash2="0x"+Hash
                new=literal_eval(hash2)
                PkgID=Hex_String(Package_ID(new))
                EntryID=Hex_String(Entry_ID(new))
                DirName=PkgID.upper()+"-"+EntryID.upper()+".directive"
                MusName=PkgID.upper()+"-"+EntryID.upper()+".mus"
                for File in os.listdir(custom_direc):
                    if File.lower() == DirName.lower():
                        Dir=True
                    if File.lower() == MusName.lower():
                        Mus=True
                if Dir == True and Mus == True:
                    break
        print("Done Getting Hashes")
        self.Hashes=Hashes
    def PullStrings(self):
        #Get String Container
        file=open(os.getcwd()+"/cache/ActivityHashes.txt","r")
        Data=file.read().split("\n")
        for Act in Data:
            temp=Act.split(" : ")
            try:
                temp[1]
            except IndexError:
                continue
            if temp[1] == self.ActName:
                StringContainer=temp[3]
                break
        
        for Line in Hash64Data:
            Lines=Line.split(": ")
            #print(Lines)
            if Lines[0] == str("0x"+StringContainer):
                Found=True
                AudioFile=Lines[1]
                new=literal_eval(AudioFile)
                PkgID=Hex_String(Package_ID(new))
                EntryID=Hex_String(Entry_ID(new))
                DirName=PkgID.upper()+"-"+EntryID.upper()
        if StringContainer == "0000000000000000":
            DirName=""
        print(DirName)
        output=open(os.getcwd()+"/cache/directive.txt","a")
        output.write("\nMusic Script + Loadzones : \n")
        if self.ActName != []:
            output.write(self.ActName+"\n")
        for Hash in self.Data:
            if "0000" not in Hash:
                dat=StringHash(Hash,self.StrData,DirName)
                if dat != False:
                    if [dat,Hash] not in self.Strings:
                        self.Strings.append([dat,Hash])
                        output.write(dat+"\n")

        output.close()
        #print(self.Strings)
    def GetName(self):
        count=0
        output=open(os.getcwd()+"/cache/directive.txt","a")
        output.write("\n"+self.ActName+"\n")
        output.close()
    def GetMusAndDir(self):
        #getdir
        FoundDir=False
        FoundMus=False
        self.AudioFound=False
        print(self.Hashes)
        for Hash in self.Hashes:
            hash2="0x"+Hash
            new=literal_eval(hash2)
            PkgID=Hex_String(Package_ID(new))
            EntryID=Hex_String(Entry_ID(new))
            DirName=PkgID.upper()+"-"+EntryID.upper()+".directive"
            MusName=PkgID.upper()+"-"+EntryID.upper()+".mus"
            print(MusName)
            for File in os.listdir(custom_direc):
                if File == DirName:
                    self.StrDirectory=DirName
                    FoundDir=True
                elif File == MusName:
                    self.MusDirectory=MusName
                    FoundMus=True
                if FoundDir == True and FoundMus == True:
                    break
    
        if FoundDir == True:
            self.PrintDirect()
        if FoundMus == True:
            self.PrintMus()
        if self.AudioFound == True:
            self.BnkSearch()
        #BNKExplorer
        output=open(os.getcwd()+"/cache/directive.txt","a")
        output.write("\n\n\n\n")
        output.close()
            
    def BnkSearch(self):
        flipped=binascii.hexlify(bytes(hex_to_little_endian(self.AudioDir))).decode('utf-8')
        dec = "0x"+flipped
        print(str(dec))
        Found=False
        print("finding music BNK")
        for Line in Hash64Data:
            Lines=Line.split(": ")
            #print(Lines)
            if Lines[0] == str(dec).lower():
                Found=True
                AudioFile=Lines[1]
                break
        if Found == True:
            new=literal_eval(AudioFile)
            PkgID=Hex_String(Package_ID(new))
            EntryID=Hex_String(Entry_ID(new))
            AudioDrive=PkgID.upper()+"-"+EntryID.upper()+".aud"
            print(AudioDrive)
            for File in os.listdir(custom_direc+"/audio"):
                if File == AudioDrive:
                    print("AudioFileExists !!!")
                    newFile=open(custom_direc+"/audio/"+AudioDrive,"rb")
                    newFile.seek(0x18)
                    BankName=binascii.hexlify(bytes(newFile.read(4))).decode()
                    newFile.close()
                    flipped=binascii.hexlify(bytes(hex_to_little_endian(BankName))).decode('utf-8')
                    new="0x"+flipped
                    new=literal_eval(new)
                    PkgID=Hex_String(Package_ID(new))
                    EntryID=Hex_String(Entry_ID(new))
                    AudioDrive1=PkgID.upper()+"-"+EntryID.upper()+".aud2"
                    for File1 in os.listdir(custom_direc+"/audio"):
                        if File1 == AudioDrive1:
                            print("AudioFileExists2 !!!")
                            newFile=open(custom_direc+"/audio/"+AudioDrive1,"rb")
                            BankName=binascii.hexlify(bytes(newFile.read())).decode()
                            flipped=binascii.hexlify(bytes(hex_to_little_endian(BankName))).decode('utf-8')
                            new="0x"+flipped
                            print(new)
                            new=literal_eval(new)
                            PkgID=Hex_String(Package_ID(new))
                            EntryID=Hex_String(Entry_ID(new))
                            AudioDrive2=PkgID.upper()+"-"+EntryID.upper()+".bnk"
                            output=open(os.getcwd()+"/cache/directive.txt","a")
                            output.write("\nSoundBank: \n")
                            output.write(AudioDrive2)
                            output.close()
                            break
                                
                    break
        
            

    def PrintDirect(self):
        Direct=open(custom_direc+"/"+self.StrDirectory,"rb")
        Data=binascii.hexlify(bytes(Direct.read())).decode()
        Direct.close()
        output=open(os.getcwd()+"/cache/directive.txt","a")
        output.write("\nDIRECTIVE: \n")
        self.Direct=[Data[i:i+8] for i in range(0, len(Data), 8)]
        for Hash in self.Direct:
            if "0000" not in Hash:
                dat=StringHash(Hash,self.StrData,"")
                if dat != False:
                    if [dat,Hash] not in self.Strings:
                        self.Strings.append([dat,Hash])
                        output.write(dat+"\n")
        output.close()
    def PrintMus(self):
        count=0
        file=open(custom_direc+"/"+self.MusDirectory,"rb")
        Data=binascii.hexlify(bytes(file.read())).decode()
        count=0
        Lines=[Data[i:i+32] for i in range(0, len(Data), 32)]
        for Line in Lines:
            Hashes=[Line[i:i+8] for i in range(0, len(Line), 8)]
            if "e8bf8080" in Line:
                Type = "e8bf8080"
                flipped=binascii.hexlify(bytes(hex_to_little_endian(Hashes[0]))).decode('utf-8')
                Len=ast.literal_eval("0x"+stripZeros(flipped))
                StartingOffset=(count+1)*16
                break
            elif "fa458080" in Line:
                Type = "fa458080"
                flipped=binascii.hexlify(bytes(hex_to_little_endian(Hashes[0]))).decode('utf-8')
                Len=ast.literal_eval("0x"+stripZeros(flipped))
                StartingOffset=(count+1)*16
                break
            elif "fb458080" in Line:
                Type = "fa458080"
                flipped=binascii.hexlify(bytes(hex_to_little_endian(Hashes[0]))).decode('utf-8')
                Len=ast.literal_eval("0x"+stripZeros(flipped))
                StartingOffset=(count+1)*16
                break
            count+=1
                
        Dev=open(os.getcwd()+"/cache/directive.txt","a")
        Dev.write("\n\n\nMusic Cue List\n")
        file.seek(0xA0)
        #StartingOffset=176
        count=0
        Pointers=[]
        HashCache=[]
        test=[]
        if Type == "e8bf8080":
            print("New Type")
            file.seek(StartingOffset)
            for i in range(Len):
                #file.seek(StartingOffset)
                Data=binascii.hexlify(bytes(file.read(48))).decode() #0 unk 1 00000000 2 RelativePointer(in hex) 3 00000000 4 StrCheck 5 StrCheck 6 Hash 7 00000000 unk----
                Hashes=[Data[i:i+8] for i in range(0, len(Data), 8)]
                #print(Hashes)
                MusHash=binascii.hexlify(bytes(hex_to_little_endian(Hashes[6]))).decode('utf-8')
                HashCache.append(str(ast.literal_eval("0x"+MusHash)))
                #print(Hashes[2])
                if Hashes[2] == "00000000": #end of file
                    Pointers.append(0)
                    test.append(0)
                   
                else:
                    Pointer=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Hashes[2]))).decode('utf-8'))
                    temp=ast.literal_eval("0x"+Pointer)
                    test.append(temp)
                    Pos=StartingOffset+(48*i)+temp+8
                    Pointers.append(Pos)
                #print(Pos)
                #print(test[i])
                count+=1
        else:
            file.seek(StartingOffset)
            for i in range(Len):
                
                Data=binascii.hexlify(bytes(file.read(32))).decode() #0 unk 1 00000000 2 RelativePointer(in hex) 3 00000000 4 StrCheck 5 01? 6 Hash 7 00000000
                Hashes=[Data[i:i+8] for i in range(0, len(Data), 8)]
                
                print(Hashes)
                MusHash=binascii.hexlify(bytes(hex_to_little_endian(Hashes[6]))).decode('utf-8')
                HashCache.append(str(ast.literal_eval("0x"+MusHash)))
                #print(Hashes[2])
                if Hashes[2] == "00000000": #end of file
                    Pointers.append(0)
                    test.append(0)
                   
                else:
                    Pointer=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Hashes[2]))).decode('utf-8'))
                    temp=ast.literal_eval("0x"+Pointer)
                    test.append(temp)
                    Pos=StartingOffset+(32*i)+temp+8
                    Pointers.append(Pos)
                #print(Pos)
                #print(test[i])
                count+=1
            #print(count)
        count=0
        for Pointer in Pointers:
            #Hash=binascii.hexlify(bytes(hex_to_little_endian(HashCache[count]))).decode('utf-8')
            Hash=HashCache[count]
            #print(str(Pointers[count+1]) +" - "+str(Pointer))
            
            try:
                Difference=int(Pointers[count+1])-int(Pointer)
            except IndexError:
                file.seek(Pointer)
                try:
                    Event=file.read().decode()
                except UnicodeDecodeError:
                    continue
                else:
                    Dev.write(str(Hash)+": "+str(Event)+" \n")
                
                break
            else:
                if str(Pointers[count+1]) == "0":
                    count+=1
                    continue
                file.seek(Pointer)
                try:
                    Event=file.read(Difference).decode()
                except ValueError:
                    print("L")
                else:
                    Dev.write(str(Hash)+": "+str(Event)+" \n")
            #print(Event)
           
            count+=1
        Dev.close()
        count=0
        Direct=open(custom_direc+"/"+self.MusDirectory,"rb")
        Data=binascii.hexlify(bytes(Direct.read())).decode()
        Direct.close()
        self.Mus=[Data[i:i+32] for i in range(0, len(Data), 32)]
        for Hash in self.Mus:
            split=[Hash[i:i+8] for i in range(0, len(Hash), 8)]
            if "f5458080" in split:
                print("MusicDrive Found")
                Line=self.Mus[count+2]
                temp=[Line[i:i+8] for i in range(0, len(Line), 8)]
                self.AudioDir=temp[0]+temp[1]
                self.AudioFound=True                            
            if split[0].upper() == "C59D1C81":
                if split[2] !="00000000":
                    self.QueHashes.append(split[2])
                    print("QueHash found")
            count+=1
        #output.close()
                
    
        
   

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
    #print(entry_b_data)
    return np.uint8(file_type), np.uint8(file_subtype)


def decode_entry_c(entry_c_data):
    starting_block = entry_c_data & 0x3FFF
    #print(starting_block)
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

    def __init__(self, package_directory,useful):
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
        self.useful=useful
        self.aes_key_0 = binascii.unhexlify(''.join([x[2:] for x in self.AES_KEY_0]))
        self.aes_key_1 = binascii.unhexlify(''.join([x[2:] for x in self.AES_KEY_1]))

    def extract_package(self, custom_direc, extract=True, largest_patch=True):
        self.get_all_patch_ids()
        if largest_patch:
            self.set_largest_patch_directory()
        print(f"Extracting files for {self.package_directory}")

        self.max_pkg_bin = open(self.package_directory, 'rb').read()
        self.package_header = self.get_header()
        self.entry_table = self.get_entry_table()
        self.block_table = self.get_block_table()

        if extract:
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
        #print(pkg_header)
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
        #print(entry_table_start)
        entry_table_data = self.max_pkg_bin[entry_table_start:entry_table_start+self.package_header.EntryTableLength]
        #table=open("entrytable.bin","wb")
        #table.write(entry_table_data)
        #time.sleep(60)
        #print(self.package_header.EntryTableSize)
        #for i in range(0, self.package_header.EntryTableSize * 16, 16):
        #    print(entry_table_data,)
        for i in range(0, self.package_header.EntryTableSize * 16, 16):
            entry = SPkgEntry(gf.get_int32(entry_table_data, i),
                              gf.get_int32(entry_table_data, i+4),
                              gf.get_int32(entry_table_data, i+8),
                              gf.get_int32(entry_table_data, i+12))
            #print(entry)
            entries_to_decode.append(entry)
        #print(len(entries_to_decode))
        #time.sleep(10)
        entry_table.Entries = self.decode_entries(entries_to_decode)
        return entry_table

    def decode_entries(self, entries_to_decode):
        """
        Given the entry table (and hence EntryA, B, C, D) we can decode each of them into data about each (file? block?)
        using bitwise operators.
        :param entry_table: the entry table struct to decode
        :return: array of decoded entries as struct SPkgEntryDecoded()
        """
        #print(entries_to_decode)
        entries = []
        count = 0
        for entry in entries_to_decode:
            # print("\n\n")
            ref_id, ref_pkg_id, ref_unk_id = decode_entry_a(entry.EntryA)
            if (hex(entry.EntryA) in self.useful) or "All" in self.useful or (self.useful == ["Cube"]) or (self.useful == ["Norm"]) or ("Map" in self.useful):
                file_type, file_subtype = decode_entry_b(entry.EntryB)
                if "Map" in self.useful:
                    #print("check")
                    if (file_type == 40) or (file_type == 32)or(file_type == 16)or(file_type == 8):
                        u=1
                    else:
                        count+=1
                        continue
                if "Scripts" in self.useful:
                    if file_type != 8 and file_type != 16:
                        count+=1
                        continue
                starting_block, starting_block_offset = decode_entry_c(entry.EntryC)
                file_size, unknown = decode_entry_d(entry.EntryC, entry.EntryD)
                file_name = f"{self.package_header.PackageIDH}-{gf.fill_hex_with_zeros(hex(count)[2:], 4)}"
                file_typename = get_file_typename(file_type, file_subtype, ref_id, ref_pkg_id)

                decoded_entry = SPkgEntryDecoded(np.uint16(count), file_name, file_typename,
                                                 ref_id, ref_pkg_id, ref_unk_id, file_type, file_subtype, starting_block,
                                                 starting_block_offset, file_size, unknown, hex(entry.EntryA))
                entries.append(decoded_entry)
                #print("Here")
                #if len(entries) > 50:
                 #   print(entries)
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
        #print(all_pkg_bin)
        self.output_files(all_pkg_bin, custom_direc)

    def decrypt_block(self, block, block_bin):
        if block.Flags & 0x4:
            key = self.aes_key_1
        else:
            key = self.aes_key_0
        cipher = AES.new(key, AES.MODE_GCM, nonce=self.nonce)
        plaintext = cipher.decrypt(block_bin)
        #print(str(plaintext).split("\\x"))
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

        nonce[0] ^= (package_id >> 8) & 0xFF
        nonce[1] = 0xEA
        nonce[11] ^= package_id & 0xFF


        self.nonce = binascii.unhexlify(''.join([gf.fill_hex_with_zeros(hex(x)[2:], 2) for x in nonce]))

    def decompress_block(self, block_bin):
        decompressor = OodleDecompressor(oodlepath)
        decompressed = decompressor.decompress(block_bin)
        return decompressed

    def output_files(self, all_pkg_bin, custom_direc):

        
        for entry in self.entry_table.Entries[::-1]:
            #print(entry)
            current_block_id = entry.StartingBlock
            block_offset = entry.StartingBlockOffset
            block_count = int(np.floor((block_offset + entry.FileSize - 1) / self.BLOCK_SIZE))
            #print(str(block_offset)+" - "+str(block_count))
            last_block_id = current_block_id + block_count
            file_buffer = b''  # string of length entry.Size
            while current_block_id <= last_block_id:
                current_block = self.block_table.Entries[current_block_id]
                if current_block.PatchID not in self.all_patch_ids:
                    print(f"Missing PatchID {current_block.PatchID}")
                    return
                current_pkg_data = all_pkg_bin[self.all_patch_ids.index(current_block.PatchID)]
                current_block_bin = current_pkg_data[current_block.Offset:current_block.Offset + current_block.Size]
                # We only decrypt/decompress if need to
                if current_block.Flags & 0x2:
                    # print('Going to decrypt')
                    current_block_bin = self.decrypt_block(current_block, current_block_bin)
                if current_block.Flags & 0x1:
                    # print(f'Decompressing block {current_block.ID}')
                    current_block_bin = self.decompress_block(current_block_bin)
                if current_block_id == entry.StartingBlock:
                    file_buffer = current_block_bin[block_offset:]
                else:
                    file_buffer += current_block_bin
                #print(file_buffer)
                current_block_id += 1
            fileFormat=""
            #print(entry.EntryA)
            #time.sleep(5)
            
            if entry.EntryA == "0x808045eb":
                fileFormat=".mus"
            elif entry.EntryA == "0x80808ec7": #directive table
                fileFormat=".directive"
            elif entry.EntryA == "0x80808e8e":
                fileFormat=".act"
            elif entry.EntryA == "0x80809738":  #["0x80809738","0x80808363","0x808097b8"]
                fileFormat=".aud"
            elif entry.EntryA == "0x80808363":
                fileFormat=".aud2"
            elif entry.EntryA == "0x80808e8b":
                fileFormat=".act"
            elif entry.EntryA == "0x808090d5":
                fileFormat=".amb"
            elif entry.EntryA == "0x808097b8":
                fileFormat=".tab"
            elif entry.EntryA == "0x808099f1":
                fileFormat=".str"
            elif entry.EntryA == "0x808099ef":
                fileFormat=".ref"
            
            else:
                fileFormat=".bin"
            if self.useful == ["All","Scripts"]:
                fileFormat=".bin"
            if self.useful==["Cube"]:
                if entry.Type == 32:
                    if entry.SubType == 2:
                        fileFormat=".cube"
                    #elif entry.SubType == 1:
                        #fileFormat=".norm"
                elif entry.Type == 48:
                    if entry.SubType == 2:
                        fileFormat=".cdat"
            if self.useful == ["Norm"]:
                if entry.Type == 40:
                    if entry.SubType == 1:
                        fileFormat=".ndat"
                if entry.Type == 32:
                    if entry.SubType == 1:
                        refFile.write(entry.FileName.upper()+" : "+entry.EntryA+"\n")
                        fileFormat=".norm"
            if "Map" in self.useful:
                if entry.EntryA == "0x808093ad":  #0x28 leads to modelocclusionbounds                         #LHash->Dt->
                    fileFormat=".load"
                elif entry.EntryA == "0x80806d44":
                    fileFormat=".model"
                elif entry.EntryA == "0x80806c81":
                    fileFormat=".terrain"
                elif entry.EntryA == "0x80809ed2":
                    fileFormat=".dyntable"
                elif entry.EntryA == "0x80806d30":  #modelData0x80809ed2
                    fileFormat=".sub"
                elif entry.EntryA == "0x80808707":   #contains all data to make map  points to .dt 's
                    fileFormat=".Lhash"
                elif entry.EntryA == "0x80809883":   #A map data table, containing data entries  85988080 table for Entities and Statics 0x90 per  DynStaMapPointers
                    fileFormat=".dt"
                elif entry.EntryA == "0x8080891e":   #1 per load  Name at 0x18
                    fileFormat=".top"
                elif entry.EntryA == "0x80808701":
                    fileFormat=".mref"
                elif entry.EntryA == "0x808093b1":
                    fileFormat=".occlu"
                elif entry.EntryA == "0x80806a0d":  #points to .Load
                    fileFormat=".test"
                elif entry.EntryA == "0x80808e8e":  #0x28 leads to modelocclusionbounds                         #LHash->Dt->
                    fileFormat=".act"
                elif entry.EntryA == "0x80806daa":
                    fileFormat = ".mat"
                else:
                    fileFormat=".bin"
                if entry.Type == 40:
                    if entry.SubType == 4:
                        fileFormat=".vert"
                        #refs.write(entry.FileName+" : "+entry.EntryA+"\n")
                    if entry.SubType == 6:
                        fileFormat=".index"
                        #refs.write(entry.FileName+" : "+entry.EntryA+"\n")
                if entry.Type == 32:
                    if entry.SubType == 4:
                        fileFormat=".vheader"
                        #refs.write(entry.FileName+" : "+entry.EntryA+"\n")
                    if entry.SubType == 6:
                        fileFormat=".iheader"
                        #refs.write(entry.FileName+" : "+entry.EntryA+"\n")
            if "0x80800000" in self.useful:
                if entry.EntryA == "0x80800000":
                    fileFormat=".script"
            if "ActName" in self.useful:
                fileFormat=".bin"
                if entry.EntryA == "0x80808e8e":  #0x28 leads to modelocclusionbounds                         #LHash->Dt->
                    fileFormat=".act"
                elif entry.EntryA == "0x80808e8b":  #0x28 leads to modelocclusionbounds                         #LHash->Dt->
                    fileFormat=".dest"
            if (fileFormat != ".bin") or ("All" in self.useful):
                #try:
                #    os.makedirs(custom_direc + self.package_directory.split('/w64')[-1][1:-6])
                #except FileExistsError:
                #    pass
                file = io.FileIO(f'{custom_direc}/{entry.FileName.upper()}'+fileFormat, 'wb')
                # print(entry.FileSize)
                if entry.FileSize != 0:
                    writer = io.BufferedWriter(file, buffer_size=entry.FileSize)
                    writer.write(file_buffer[:entry.FileSize])
                    writer.flush()
                else:
                    with open(f'{custom_direc}/{entry.FileName.upper()}'+fileFormat, 'wb') as f:
                        f.write(file_buffer[:entry.FileSize])

            #print(f"Wrote to {entry.FileName} successfully")
        
def check_input(event):
    global lst, combo_box
    value = event.widget.get()

    if value == '':
        combo_box['values'] = lst
    else:
        data = []
        for item in lst:
            if value.lower() in item.lower():
                data.append(item)

        combo_box['values'] = data



def unpack_all(path, custom_direc, useful,filelist):
    all_packages = filelist
    i=0
    for thing in range(len(all_packages)):
        #print(i)
        if "video" in all_packages[i].split("_"):
            all_packages.remove(all_packages[i]) #videos break???
        else:
            i+=1
    #print(all_packages)
    single_pkgs = dict()
    for pkg in all_packages:
        single_pkgs[pkg[:-6]] = pkg
    #print(single_pkgs.items())
    for pkg, pkg_full in single_pkgs.items():
        if "audio" in pkg.split("_"):
            pkg = Package(f'{path}/{pkg_full}',useful)
            if useful == ["0x808099ef","0x808099f1"]:
                pkg.extract_package(extract=True, custom_direc=custom_direc)
            else:
                pkg.extract_package(extract=True, custom_direc=custom_direc+"/audio")
        elif "dialog" in pkg.split("_"):
            pkg = Package(f'{path}/{pkg_full}',useful)
            if useful == ["0x808099ef","0x808099f1"]:
                pkg.extract_package(extract=True, custom_direc=custom_direc)
            else:
                pkg.extract_package(extract=True, custom_direc=custom_direc+"/audio")
        else:
            pkg = Package(f'{path}/{pkg_full}',useful)
            pkg.extract_package(extract=True, custom_direc=custom_direc)
    print("done")
def setD2Location(loc,top):
    path=loc.get()
    MainWindow(top)

def DataView(top,name):
    for widget in top.winfo_children():
        widget.destroy()
    bg = PhotoImage(file = os.getcwd()+"/ThirdParty/destiny.png")
    label1 = Label(top, image = bg)
    
    Back = Button(top, text="Back", height=1, width=15,command=partial(ActivityMenu,top))
    Back.place(x=10, y=10)
    Output = Button(top, text="Export Data", height=1, width=15,command=partial(OutputAct, name))
    Output.place(x=1050, y=430)
    file = open(os.getcwd()+"/cache/directive.txt","r").read()
    T = Text(top, height = 500, width = 110)
    T.insert(END,file)
    T.pack()
    label1.place(x=0,y=0)
    top.mainloop()
def OutputAct(name):
    file = open(os.getcwd()+"/cache/directive.txt","r").read()
    file2 = open(os.getcwd()+"/Activity/"+name+".txt","w")
    file2.write(file)
    file2.close()
    
def CutsceneView(top):
    global lst, combo_box
    lst=[]
    for widget in top.winfo_children():
        widget.destroy()
    for File in os.listdir(path):
        temp=File.split("_")
        if "video" in temp:
            new="_".join(temp[:(len(temp)-1)])
            if new not in lst:
                lst.append(new)
    bg = PhotoImage(file = os.getcwd()+"/ThirdParty/destiny.png")
    label1 = Label(top, image = bg)
    label1.pack()
    useful=[]
    combo_box = ttk.Combobox(top,height=20, width=30)
    combo_box['values'] = lst
    combo_box.bind('<KeyRelease>', check_input)
    combo_box.place(x=500, y=125)
    Activity = Button(top, text="Extract Cutscene (will take a while)", height=1, width=30,command=partial(CutsceneRip,combo_box))
    Activity.place(x=500, y=175)
    Back = Button(top, text="Back", height=1, width=15,command=partial(MainWindow,top))
    Back.place(x=10, y=10)
    filelist = []
    top.mainloop()
    
def CutsceneRip(box):
    global path
    currentPath=os.getcwd()
    os.chdir(currentPath+"/ThirdParty")
    pkg=box.get()
    pkgID=pkg.split("_")[len(pkg.split("_"))-1]
    print(pkgID)
    pkgPath=path
    cmd='d2.exe '+str(pkgID)+' "'+pkgPath+'"'
    print(cmd)
    temp=currentPath.split("\\")
    newPath="/".join(temp)
    ans=subprocess.call(cmd, shell=True)
    path = newPath+"/Cutscenes/"+str(pkgID)
    # Check whether the specified path exists or not
    isExist = os.path.exists(path)
    if not isExist:

       # Create a new directory because it does not exist
       os.makedirs(path)
       print("The new directory is created!")
    for File in os.listdir(currentPath+"/ThirdParty/output/"+str(pkgID)):
        shutil.move(newPath+"/ThirdParty/output/"+str(pkgID)+"/"+File,newPath+"/Cutscenes/"+str(pkgID)+"/"+File)
    os.chdir(currentPath+"/ThirdParty")
    for file in os.listdir(currentPath+"/Cutscenes/"+pkgID+"/"):
        path2file=(newPath+"/Cutscenes/"+pkgID+"/"+file)
        binFile=open(path2file,"rb")
        data=str(binFile.read(3))
        binFile.close()
        print(data)
        if data.split("'")[1] == "CRI":
            print("USM Found")
            #converting to usm
            base = os.path.splitext(path2file)[0]
            print(base)
            isExist = os.path.exists(base+".usm")
            if isExist == True:
                print("USM already exists")
                os.remove(path2file)
            else:
                os.rename(path2file, base + ".usm")
        else:
            os.remove(path2file)
    #input()
    directory=os.listdir(currentPath+"/Cutscenes/"+pkgID+"/")
    for file in directory:
        path2file=(currentPath+"/Cutscenes/"+pkgID+"/"+file)    
        cmd=("UsmToolkit.exe extract "+path2file)
        #print(cmd)
        ans=subprocess.call(cmd, shell=True)
        #print("TOOLKIT USED")
        count=0
        for subfile in os.listdir(currentPath+"/Cutscenes/"+pkgID+"/"):
            if subfile.split(".")[1] == "adx":
                print(subfile)
                count+=1
                
                if count > 2:
                    os.remove(currentPath+"/Cutscenes/"+pkgID+"/"+subfile)
                else:
                    cmd="vgmstream -o "+currentPath+"/Cutscenes/"+pkgID+"/"+subfile.split(".")[0]+".wav "+currentPath+"/Cutscenes/"+pkgID+"/"+subfile
                    print(cmd)
                    ans=subprocess.call(cmd, shell=True)
        
       
         #Combine backing and audio
        

        
        tracks=[]
        for subfile in os.listdir(currentPath+"/Cutscenes/"+pkgID+"/"):
            if subfile.split(".")[1] == "wav":
                
                #convert to mp3
                cmd="ffmpeg -i "+currentPath+"/Cutscenes/"+pkgID+"/"+subfile+" -vn -ar 44100 -ac 2 -b:a 192k "+currentPath+"/Cutscenes/"+pkgID+"/"+subfile.split(".")[0]+".mp3"
                print(cmd)
                ans=subprocess.call(cmd, shell=True,cwd=currentPath+"/ThirdParty")
                tracks.append(subfile.split(".")[0]+".mp3")
                    
                    
            elif subfile.split(".")[1] == "m2v":
                m2vFile=subfile
        #first combine
        if len(tracks) != 2:
            print("Files were not deleted or found placeholder cutscene")
            for subfile in os.listdir(currentPath+"/Cutscenes/"+pkgID+"/"):
                if subfile.split(".")[1] == "mp3":
                    os.remove(currentPath+"/Cutscenes/"+pkgID+"/"+subfile)
                elif subfile.split(".")[1] == "m2v":
                    os.remove(currentPath+"/Cutscenes/"+pkgID+"/"+subfile)
                elif subfile.split(".")[1] == "wav":
                    os.remove(currentPath+"/Cutscenes/"+pkgID+"/"+subfile)
            
        else:
            cmd="ffmpeg -i "+currentPath+"/Cutscenes/"+pkgID+"/"+m2vFile+" -i "+currentPath+"/Cutscenes/"+pkgID+"/"+tracks[0]+" -c copy "+currentPath+"/Cutscenes/"+pkgID+"/tempoutput.mp4"
            print(cmd)
            ans=subprocess.call(cmd, shell=True,cwd=currentPath+"/ThirdParty")
            "ffmpeg -i video.mkv -i audio.mp3 -map 0 -map 1:a -c:v copy -shortest output.mkv"
            cmd='ffmpeg -i '+currentPath+'/Cutscenes/'+pkgID+'/tempoutput.mp4 -i '+currentPath+'/Cutscenes/'+pkgID+'/'+tracks[1]+' -filter_complex "[0:a][1:a]amerge=inputs=2[a]" -map 0:v -map "[a]" -c:v copy -ac 2 -shortest '+currentPath+"/Cutscenes/"+pkgID+"/"+m2vFile.split(".")[0]+".mp4"
            ans=subprocess.call(cmd, shell=True,cwd=currentPath+"/ThirdParty")
            #cleanup
            for subfile in os.listdir(currentPath+"/Cutscenes/"+pkgID+"/"):
                if subfile.split(".")[1] == "mp3":
                    os.remove(currentPath+"/Cutscenes/"+pkgID+"/"+subfile)
                elif subfile.split(".")[1] == "m2v":
                    os.remove(currentPath+"/Cutscenes/"+pkgID+"/"+subfile)
                elif subfile.split(".")[1] == "wav":
                    os.remove(currentPath+"/Cutscenes/"+pkgID+"/"+subfile)
                elif subfile.split(".")[1] == "adx":
                    os.remove(currentPath+"/Cutscenes/"+pkgID+"/"+subfile)
            os.remove(currentPath+"/Cutscenes/"+pkgID+"/tempoutput.mp4")
            os.remove(path2file)
        #input()
    os.chdir(currentPath)
    Popup()
def GenerateActivityNames():
    filelist=[]
    
    ActNames=[]
    useful=["ActName","0x80808e8e","0x80808e8b"]
    for file in os.listdir(path)[::-1]:
        if fnmatch.fnmatch(file,'w64*'):   #CHANGE HERE
            if "sandbox" not in file.split("_"):
                if "audio" not in file.split("_"):
                    filelist.append(file)
    unpack_all(path,custom_direc,useful,filelist)
    for File in os.listdir(os.getcwd()+"/out"):
        if File == "audio":
            continue
        if File.split(".")[1] == "dest":
            FileName=File.split(".")[0]
            CurrentOffset=0
            Pointers=[]
            #print(File)
            file=open(custom_direc+"/"+File,"rb")
            #file.seek(0xA0)
            ActivityFound=False
            while ActivityFound == False:
                Data=binascii.hexlify(bytes(file.read(16))).decode()
                DataSplit=[Data[i:i+8] for i in range(0, len(Data), 8)]
                if "2e898080" in DataSplit:
                    ActivityFound=True
                    Len=DataSplit[0][:4]
                    flipped=binascii.hexlify(bytes(hex_to_little_endian(Len))).decode('utf-8')
                    Len=ast.literal_eval("0x"+stripZeros(flipped))
                CurrentOffset+=16
            StartingOffset=CurrentOffset
            #CurrentOffset=176
            #print(Len)
            for i in range(Len):
                Data=binascii.hexlify(bytes(file.read(24))).decode()
                #ActivityData.append(Data)
                
                Data2=[Data[i:i+4] for i in range(0, len(Data), 4)]
                #print(Data)
                Pointer=Data2[8]
                flipped=binascii.hexlify(bytes(hex_to_little_endian(Pointer))).decode('utf-8')
                Len=ast.literal_eval("0x"+stripZeros(flipped))
                Pointers.append([int(Len)+CurrentOffset+16,Data[16:32]])
                CurrentOffset+=24

                
            
            StrFound=False
            while StrFound == False:
                Data=binascii.hexlify(bytes(file.read(4))).decode()
                if Data == "65008080":
                    StrFound=True
                CurrentOffset+=4
            CurrentOffset+=8
            file.seek(CurrentOffset)
            Strings=file.read().decode()
            #print(Strings)
            FilesNames=[]
            count=0  
            for Pointer in Pointers:
                name=""
                #print(Pointer)
                Start=Pointer[0]-CurrentOffset
                #print(Start)
                try:
                    Pointers[count+1][0]
                except IndexError:
                    name=Strings[Start:]
                else:
                    Start2=Pointers[count+1][0] - CurrentOffset
                    name=Strings[int(Start):int(Start2)]
                fixed=name.split("\x00")[0]
                if "ambient" not in fixed.split("_"):
                    FilesNames.append(Pointer[1]+" : "+fixed)
                count+=1
                #print(name)
            #print(FilesNames)
            file.close()
            file=open(custom_direc+"/"+File,"rb")
            file.seek(0x18)
            Data=binascii.hexlify(bytes(file.read(8))).decode()
            Hash=binascii.hexlify(bytes(hex_to_little_endian(Data))).decode('utf-8')
            for FileName in FilesNames:
                ActNames.append([FileName,Hash])
    theFile=open(os.getcwd()+"/cache/ActivityHashes.txt","w")
    stuff=[]
    for File in os.listdir(os.getcwd()+"/out"):
        if File == "audio":
            continue
        if File.split(".")[1] == "act":
            file=open(os.getcwd()+"/out/"+File,"rb")
            Data=binascii.hexlify(file.read()).decode('utf-8')
            DataSplit=[Data[i:i+16] for i in range(0, len(Data), 16)]
            for Act in ActNames:
                if Act[0].split(" : ")[0] in Data:
                    pkgId= File.split("-")[0]
                    for file in os.listdir(path):
                        temp=file.split("_")
                        if pkgId.lower() in file.split("_"):
                            PackageName="_".join(temp[:len(temp)-2])
                            stuffToAdd=Act[0]+" : "+PackageName+" : "+Act[1]
                            if stuffToAdd not in stuff:
                                stuff.append(stuffToAdd)
    for Thing in stuff:
        theFile.write(str(Thing)+"\n")
    theFile.close()
                    
    for file in os.listdir(os.getcwd()+"/out"):
        if file != "audio":
            os.remove(os.getcwd()+"/out/"+file)        
def ActivityRipper(entry):
    print("Starting ACT")
    package=""
    ActId=""
    ActName=entry.get()
    File2=open(os.getcwd()+"/cache/ActivityHashes.txt","r")
    data=File2.read()
    File2.close()
    Activities=data.split("\n")
    if ActName != "All":
        for Act in Activities:
            temp=Act.split(" : ")
            if entry.get() in temp:
                package=temp[2]
                ActId=temp[0]
                print("found")
                break
    output=open(os.getcwd()+"/cache/directive.txt","w")   #Comment out to not clear on reset
    filelist=[]
    filelist2=[]
    num=len(os.listdir(custom_direc+"/audio"))
    if entry.get() != "All":
        for file in os.listdir(path)[::-1]:
            if fnmatch.fnmatch(file,package+"*"):       #Customize this to what pkgs you need from. Can wildcard with * for all packages, or all of a certain type.
                filelist.append(file)
            if int(num) < 10:
                if fnmatch.fnmatch(file,'w64_sr_audio*'):
                    filelist2.append(file)
                if fnmatch.fnmatch(file,'w64_sr_dia*'):
                    filelist2.append(file)
    else:
        for file in os.listdir(path)[::-1]:
            if int(num) < 10:
                if fnmatch.fnmatch(file,'w64_sr_audio*'):
                    filelist2.append(file)
                if fnmatch.fnmatch(file,'w64_sr_dia*'):
                    filelist2.append(file)
            if "audio"  in file.split("_"):
                continue
            elif "dialog" in file.split("_"):
                continue
            else:
                if fnmatch.fnmatch(file,"w64*"):       #Customize this to what pkgs you need from. Can wildcard with * for all packages, or all of a certain type.
                    filelist.append(file)
    useful=["0x808045eb","0x80808e8e","0x80808ec7","0x80808e8b","0x80809650","0x80809738","0x80808363","0x808090d5","0x808097b8"]
    print("run unpack")
    unpack_all(path,custom_direc,useful,filelist)
    print(filelist2)
    useful=["0x80809738","0x80808363","0x808097b8"]
    if int(num) < 10:
        unpack_all(path,custom_direc,useful,filelist2)
    Files=[]
    print("Starting Process")
    file2=open(os.getcwd()+"/cache/output.txt","r")
    data=file2.read()
    file2.close()
    StrData=data.split("\n")
    #print(StrData)
    #file.close()
    newStrData=[]
    for String in StrData:
        try:
            String.split(" // ")[1]
        except IndexError:
            continue
        try:
            int(String.split(" // ")[1])
        except ValueError:
            continue
            
        try:
            newStrData.append([(String.split(" // ")[0]),int(String.split(" // ")[1]),String.split(" // ")[2]])
        except IndexError:
            #print(String)
            continue
        
        #print(newStrData)
    newStrData.sort(key=lambda x: x[1])
    StrData=newStrData
    for FileName in os.listdir(custom_direc):
        if FileName != "audio":
            if FileName.split(".")[1] == "act":
                ActFile=open(os.getcwd()+"/out/"+FileName,"rb")
                Data=binascii.hexlify(ActFile.read()).decode('utf-8')
                ActFile.close()
                DataSplit=[Data[i:i+16] for i in range(0, len(Data), 16)]
                if ActName == "All":
                    print("Extracting")
                    file=File(FileName,FileName.split(".")[1],StrData,ActName)
                    Files.append(file)
                    print(FileName)
                    file.FindHashes()
                    print("Got HAshes")
                    file.GetName()
                    print("GotName")
                    file.PullStrings()
                    print("Got Strings")
                    file.GetMusAndDir()
                    print("Get Mus and Dir")
                    file.GetDialogue()
                else:
                    if ActId in DataSplit:
                        print("Extracting")
                        file=File(FileName,FileName.split(".")[1],StrData,ActName)
                        Files.append(file)
                        print(FileName)
                        file.FindHashes()
                        print("Got HAshes")
                        file.GetName()
                        print("GotName")
                        file.PullStrings()
                        print("Got Strings")
                        file.GetMusAndDir()
                        print("Get Mus and Dir")
                        file.GetDialogue()
    print("done")
    #for file in os.listdir(custom_direc):
    #    if file != "audio":
    #        os.remove(custom_direc+"/"+file)
    Popup()
    DataView(top,entry.get())
def binary_search_single(arr, x):
    low = 0
    high = len(arr) - 1
    mid = 0
 
    while low <= high:
 
        mid = (high + low) // 2
        if int(arr[mid]) < x:
            low = mid + 1
 
        # If x is smaller, ignore right half
        elif int(arr[mid]) > x:
            high = mid - 1
 
        # means x is present at mid
        else:
            return mid
    # If we reach here, then the element was not present
    return -1        
def binary_search2(arr, x):
    low = 0
    high = len(arr) - 1
    mid = 0
 
    while low <= high:
 
        mid = (high + low) // 2
        if int(arr[mid][0]) < x:
            low = mid + 1
 
        # If x is smaller, ignore right half
        elif int(arr[mid][0]) > x:
            high = mid - 1
 
        # means x is present at mid
        else:
            return mid
    # If we reach here, then the element was not present
    return -1    
def binary_search(arr, x):
    low = 0
    high = len(arr) - 1
    mid = 0
 
    while low <= high:
 
        mid = (high + low) // 2
        if int(arr[mid][1]) < x:
            low = mid + 1
 
        # If x is smaller, ignore right half
        elif int(arr[mid][1]) > x:
            high = mid - 1
 
        # means x is present at mid
        else:
            return mid
    # If we reach here, then the element was not present
    return -1
def StringHash(Hash,StrData,Ref):
    #print(Ref)
    flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8')
    #print(flipped)
    dec = ast.literal_eval("0x"+flipped)
    Found=False
    ans=binary_search(StrData,int(dec))
    #print(ans)
    if str(ans) != "-1":
        Found=True
    if Found == True:
        if Ref != "":
            while True:
                try:
                    StrData[ans][0]
                except IndexError:
                    ans=ans-1
                    break
                if StrData[ans][0] != Ref:
                    #print(StrData[ans]
                    ans=ans+1
                else:
                    break
        return StrData[ans][2]
    else:
        return False
            
def ActivityMenu(top):
    global lst, combo_box
    lst=["All"]
    file=open(os.getcwd()+"/cache/ActivityHashes.txt","r")
    data=file.read()
    file.close()
    ActDat=data.split("\n")
    ActDat.remove("")
    for Act in ActDat:
        #print(Act)
        things=Act.split(" : ")
        lst.append(things[1])
    for widget in top.winfo_children():
        widget.destroy()
    lst.sort(reverse=False)
    bg = PhotoImage(file = os.getcwd()+"/ThirdParty/destiny.png")
    label1 = Label(top, image = bg)
    label1.pack()
    #print(lst)
    useful=[]
    combo_box = ttk.Combobox(top,height=20, width=50)
    combo_box['values'] = lst
    combo_box.bind('<KeyRelease>', check_input)
    combo_box.place(x=500, y=125)
    Activity = Button(top, text="Extract Activity Data", height=1, width=15,command=partial(ActivityRipper,combo_box))
    Activity.place(x=500, y=175)
    Back = Button(top, text="Back", height=1, width=15,command=partial(MainWindow,top))
    Back.place(x=10, y=10)
    filelist = []
    top.mainloop()
    


def Strings(ans):
    RefFile=open(os.getcwd()+"/cache/refFile.txt","w")
    useful=[]
    filelist = []
    for file in os.listdir(path)[::-1]:
        if fnmatch.fnmatch(file,'w64*'):
            if ans == "y":
                filelist.append(file)
 
    useful=["0x808099ef","0x808099f1"]
    unpack_all(path,custom_direc,useful,filelist)
    strPath=custom_direc
    print("Outputting...")
    output=open(os.getcwd()+"/cache/output.txt","w")
    output.close()
    allRefs=[]
    Files=os.listdir(strPath)
    #print(Files)
    for File in  Files:
        #print(File)
        if File != "audio":
            if File.split(".")[1] == "ref":
                allRefs.append(File)
    for Ref in allRefs:
        #print(Ref)
        file=open((strPath+"/"+Ref),"rb")
        FileName=Ref.split(".")[0]
        length=len(binascii.hexlify(bytes(file.read())))
        file.close()
        RefHeader=[]
        RefLocations=[]
        RefUnknown=[] #B89F8080
        RefHashes=[]
        file=open((strPath+"/"+Ref),"rb")
        iterations=(length//8)
        for i in range(6):
            RefHeader.append(binascii.hexlify(bytes(file.read(4))).decode('utf-8'))
        count=0
        for i in range(iterations-6):
            data=binascii.hexlify(bytes(file.read(4)))
            #print(data.decode('utf-8'))
            if data.decode() == "b89f8080":
                count += 1
                break
            RefLocations.append(data.decode('utf-8'))
            count += 1
        for i in range(4):
            data=binascii.hexlify(bytes(file.read(4)))
            RefUnknown.append(data.decode('utf-8'))
        for i in range((iterations-6)-(count)-4):
            data=binascii.hexlify(bytes(file.read(4)))
            RefHashes.append(data.decode('utf-8'))
        #print(RefHeader)
        #print(RefLocations)
        #print(RefUnknown)
        #print(RefHashes)
        
        file.close()
        #output=open("outputold.txt","a")
        stringBnk=[]
        for i in range(len(RefHashes)):
            RefHashes[i]=binascii.hexlify(bytes(hex_to_little_endian(RefHashes[i]))).decode('utf-8')
            #print(int(flippedHash,16))
            
            #print(flippedLoc)
            #BnkLoc=flippedLoc.split("80a0")[1]
            #print(data)
            #print(BnkLoc)
            
        #print(stringBnk)
        flippedLoc=binascii.hexlify(bytes(hex_to_little_endian(RefLocations[0]))).decode('utf-8')
        Hash1=int("0x"+flippedLoc,base=16)
        #BnkLoc=flippedLoc.split("80a0")[1]
        #stringBnk.append(Ref.split("-")[0]+"-"+BnkLoc+".str")
        BnkHeader=[]
        BnkLengths=[]
        BnkStrings=[]
        BnkGap=[]
        #print(Hash)
        
        #RefHashes=[]
        #print(stringBnk[0])
        # Example usage
        #print(int(Hash))
        pkg = Hex_String(Package_ID(int(Hash1)))
        #print(result)
        ent = Hex_String(Entry_ID(int(Hash1)))
        Bank=pkg+"-"+ent+".str"
        #print(Bank)
        try:
            Bnk=open(strPath+"/"+Bank,"rb")
        except FileNotFoundError:
            continue
        #print(Bank)
        #################
        data=binascii.hexlify(bytes(Bnk.read())).decode("utf-8")
        Data=[data[i:i+32] for i in range(0, len(data), 32)]
        count=0
        Blocks=False
        for Line in Data:
            temp=[Line[i:i+8] for i in range(0, len(Line), 8)]
            if "f5998080" in temp:
                count+=1
              
                BlockLengthsOffset=(16*count)
                flipped=binascii.hexlify(bytes(hex_to_little_endian(temp[0]))).decode('utf-8')
                BlockLengthsCount=ast.literal_eval("0x"+stripZeros(flipped))
                Blocks=True
                break

            count+=1
        if Blocks == False:
            continue
        Bnk.seek(BlockLengthsOffset)
        BlockCounts=[]
        for i in range(BlockLengthsCount):
            data=binascii.hexlify(bytes(Bnk.read(16))).decode("utf-8")
            temp=[data[i:i+4] for i in range(0, len(data), 4)]
            Offset=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(temp[0]))).decode('utf-8')))
            Counts=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(temp[4]))).decode('utf-8')))
            BlockCounts.append(int(Counts))
        Bnk.seek(0)
        #print("opened bnk")
        #print(BlockCounts)
        ##############################
        tooSmall=0
        while True:
            data=binascii.hexlify(bytes(Bnk.read(4))).decode("utf-8")
            if data == "f7998080":
                break
            BnkHeader.append(data)
            tooSmall+=1
            if tooSmall == 30:
                break
            #print("stuck")
            #print(data)
        #print(BnkHeader)
        if tooSmall == 30:
            continue
        Bnk.seek(0)
        data=binascii.hexlify(bytes(Bnk.read())).decode("utf-8")
        Data=[data[i:i+32] for i in range(0, len(data), 32)]
        count=0
        Entires=False
        for Line in Data:
            temp=[Line[i:i+8] for i in range(0, len(Line), 8)]
            if "f7998080" in temp:
                count+=1
                EntryCount=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(temp[0]))).decode('utf-8')))
                EntryStartingOffset=count*16
                Entries=True
                break
            count+=1
        Bnk.seek(EntryStartingOffset)
        StringData=[]#Start Offset,Length
        CurrentOffset=EntryStartingOffset
        j=0
        num=0
        if Entries == False:
            continue
        for i in range(int(EntryCount)):
            if j == BlockCounts[num]:
                num+=1
                j=0
            EntryData=binascii.hexlify(bytes(Bnk.read(32))).decode("utf-8")
            Data=[EntryData[i:i+4] for i in range(0, len(EntryData), 4)]
            StringOffset=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(str(Data[4])+str(Data[5])))).decode('utf-8')))
            StrLength=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Data[10]))).decode('utf-8')))
            StringData.append([int(StringOffset)+CurrentOffset+8,int(StrLength),RefHashes[num],CurrentOffset])
            CurrentOffset+=32
            j+=1
            
            
            
            
        #print(StringData)
            
            
        
        #print("notstuck")
        #for i in range(4):
        data=binascii.hexlify(bytes(Bnk.read(4))).decode("utf-8")
        BnkGap.append(data)
        #onto Str
        #print(BnkLengths)
        
        HashVal=0
        count=0
        #print(str(len(RefHashes))+" ----- "+str(len(BlockCounts)))
        for String in StringData:
            #print(String)
            out=open(os.getcwd()+"/cache/output.txt","a")
            Bnk.seek(String[0])
            text=Bnk.read(String[1]).decode()
            Hash=int(String[2],16)
            
            
                
            textout=str(FileName)+" // "+str(Hash)+" // "+text+"\n"
            #print(textout)
            try:
                out.write(textout)
            except UnicodeEncodeError:
                out.write(str(FileName)+" // "+str(Hash)+" // ?\n")
            
                
            out.close()
            
            #print("written")
            count+=1
                
                    
                
           
            
        Bnk.close()
        #break
    for file in os.listdir(custom_direc):
        if file != "audio":
            os.remove(custom_direc+"/"+file)
            
    Popup()

def RefDataRead():
    file=open(os.getcwd()+"/cache/refFile.txt","r")
    dat=file.read()
    RefDat=dat.split("\n")
    file.close()
    return RefDat

class DDS:
    def __init__(self,Name,Type,Header,Main,Location):
        #print(Name)
        self.CWD=os.getcwd()
        if Type == "Cube":
            self.SaveLoc=os.getcwd()+"/Textures/Cubemaps"
        else:
            self.SaveLoc=os.getcwd()+"/Textures"
        self.SaveLoc=Location
        self.FileName=Name
        self.Main=Main
        self.Header=Header
        self.ReadData()
        if Type == "Norm":
            self.ProcessNorm()
            self.OutputNorm()
        else:
            self.Process()
            self.Output()
    def ReadData(self):
        self.texFormat=self.Header[8:12]
        self.width=self.Header[68:72]
        flipped=binascii.hexlify(bytes(hex_to_little_endian(self.width))).decode('utf-8')
        self.width=(ast.literal_eval("0x"+flipped))
        #print(self.width)
        #print(self.width)
        self.height=self.Header[72:76]
        flipped=binascii.hexlify(bytes(hex_to_little_endian(self.height))).decode('utf-8')
        self.height=(ast.literal_eval("0x"+flipped))
        #print(self.height)
        self.arraySize=self.Header[80:84]
        flipped=binascii.hexlify(bytes(hex_to_little_endian(self.arraySize))).decode('utf-8')
        self.arraySize=ast.literal_eval("0x"+stripZeros(flipped))
    def ProcessNorm(self):
        self.dxtmiscFlags2 = ""
        self.compressed=False
        flipped=binascii.hexlify(bytes(hex_to_little_endian(self.texFormat))).decode('utf-8')
        new=ast.literal_eval("0x"+stripZeros(flipped))
        #print(new)
        if (70< new < 99):
            self.compressed=True
        self.Norm=new
        self.texFormat=c_uint32(new)
        self.MagicNumber = c_uint32(542327876)
        self.dwSize = c_uint32(124)
        self.dwFlags = c_uint32((0x1 + 0x2 + 0x4 + 0x1000) + 0x8)
        self.dwHeight = c_uint32(self.height)
        self.dwWidth= c_uint32(self.width)
        self.dwPitchOrLinearSize = c_uint32(0)
        self.dwDepth = c_uint32(0)
        self.dwMipMapCount = c_uint32(0)
        self.dwReserved1 = c_uint32(0)
        self.dwPFSize = c_uint32(32)
        self.dwPFRGBBitCount = c_uint32(0)
        self.dwPFRGBBitCount = c_uint32(32)
        self.dwPFRBitMask = c_uint32(0xFF)
        self.dwPFGBitMask = c_uint32(0xFF00)
        self.dwPFBBitMask = c_uint32(0xFF0000)
        self.dwPFABitMask = c_uint32(0xFF000000)
        self.dwCaps = c_uint32(0x1000)
        self.dwCaps2 = c_uint32(0x0)
        self.dwCaps3 = c_uint32(0)
        self.dwCaps4 = c_uint32(0)
        self.dwReserved2 = c_uint32(0)
        #print(self.compressed)
        if self.compressed == True:
            self.dwPFFlags = c_uint32(0x1 + 0x4) 
            self.dwPFFourCC = c_uint32(808540228)
            self.dxtdxgiFormat = c_uint32(new)
            self.dxtresourceDimension = c_uint32(3)
            if (self.arraySize % 6) == 0:
                self.dxtmiscFlag = c_uint32(4)
                self.dxtArraySize = c_uint32(self.arraySize // 6)
            else:
                self.dxtmiscFlag = c_uint32(0)
                self.dxtArraySize = c_uint32(1)
        else:
            self.dwPFFlags = c_uint32(0x1 + 0x4)  # contains alpha data + contains uncompressed RGB data
            self.dwPFFourCC = c_uint32(808540228)
            self.dxtmiscFlag = c_uint32(0)
            self.dxtArraySize = c_uint32(1)
            self.dxtmiscFlags2 = c_uint32(0x1)
            self.dxtdxgiFormat = c_uint32(new)
            self.dxtresourceDimension = c_uint32(3)
        self.arraySize=c_uint32(self.arraySize)
    def Process(self):
        self.dxtmiscFlags2 = ""
        self.compressed=False
        flipped=binascii.hexlify(bytes(hex_to_little_endian(self.texFormat))).decode('utf-8')
        new=ast.literal_eval("0x"+stripZeros(flipped))
        if (70< new < 99):
            self.compressed=True
        self.texFormat=c_uint32(new)
        self.MagicNumber = c_uint32(542327876)
        self.dwSize = c_uint32(124)
        self.dwFlags = c_uint32((0x1 + 0x2 + 0x4 + 0x1000) + 0x8)
        self.dwHeight = c_uint32(self.height)
        self.dwWidth= c_uint32(self.width)
        self.dwPitchOrLinearSize = c_uint32(0)
        self.dwDepth = c_uint32(0)
        self.dwMipMapCount = c_uint32(0)
        self.dwReserved1 = c_uint32(0)
        self.dwPFSize = c_uint32(32)
        self.dwPFRGBBitCount = c_uint32(0)
        self.dwPFRGBBitCount = c_uint32(32)
        self.dwPFRBitMask = c_uint32(0xFF)
        self.dwPFGBitMask = c_uint32(0xFF00)
        self.dwPFBBitMask = c_uint32(0xFF0000)
        self.dwPFABitMask = c_uint32(0xFF000000)
        self.dwCaps = c_uint32(0x1000)
        self.dwCaps2 = c_uint32(0x200)
        self.dwCaps3 = c_uint32(0)
        self.dwCaps4 = c_uint32(0)
        self.dwReserved2 = c_uint32(0)
        if self.compressed == True:
            self.dwPFFlags = c_uint32(0x1 + 0x4 ) 
            self.dwPFFourCC = c_uint32(808540228)
            self.dxtdxgiFormat = self.texFormat
            self.dxtresourceDimension = c_uint32(3)
            if (self.arraySize % 6) == 0:
                self.dxtmiscFlag = c_uint32(4)
                self.dxtArraySize = c_uint32(self.arraySize // 6)
            else:
                self.dxtmiscFlag = c_uint32(0)
                self.dxtArraySize = c_uint32(1)
        else:
            self.dxtdwPFFlags = c_uint32(0x1 + 0x40)  # contains alpha data + contains uncompressed RGB data
            self.dxtdwPFFourCC = c_uint32(0)
            self.dxtmiscFlag = c_uint32(0)
            self.dxtArraySize = c_uint32(1)
            self.dxtmiscFlags2 = c_uint32(0x1)
        self.arraySize=c_uint32(self.arraySize)
    def OutputNorm(self):
        File=open(self.FileName.split(".")[0]+".dds","wb")
        thingsToAdd=[self.MagicNumber,self.dwSize,self.dwFlags,self.dwHeight,self.dwWidth,self.dwPitchOrLinearSize,self.dwDepth,self.dwMipMapCount,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwPFSize,self.dwPFFlags,self.dwPFFourCC,self.dwPFRGBBitCount,self.dwPFRBitMask,self.dwPFGBitMask,self.dwPFBBitMask,self.dwPFABitMask,self.dwCaps,self.dwCaps2,self.dwCaps3,self.dwCaps4,self.dwReserved2]
        new=0
        for thing in thingsToAdd:
            File.write(thing)
        thingsToAdd=[self.dxtdxgiFormat,self.dxtresourceDimension,self.dxtmiscFlag,self.dxtArraySize]
        for thing in thingsToAdd:
            File.write(thing)
        if self.dxtmiscFlags2 != "":
            File.write(c_uint32(659757824))
        else:
            File.write(c_uint32(0))
        File.write(binascii.unhexlify(self.Main))
        File.close()       
        #cmd="texassemble.exe h-cross "+self.FileName.split(".")[0]+".dds"+" -y -nologo -o "+self.FileName.split(".")[0]+".bmp"
        #os.system('cmd /c '+cmd)
        DXGI_FORMAT = [
        "UNKNOWN",
        "R32G32B32A32_TYPELESS",
        "R32G32B32A32_FLOAT",
        "R32G32B32A32_UINT",
        "R32G32B32A32_SINT",
        "R32G32B32_TYPELESS",
        "R32G32B32_FLOAT",
        "R32G32B32_UINT",
        "R32G32B32_SINT",
        "R16G16B16A16_TYPELESS",
        "R16G16B16A16_FLOAT",
        "R16G16B16A16_UNORM",
        "R16G16B16A16_UINT",
        "R16G16B16A16_SNORM",
        "R16G16B16A16_SINT",
        "R32G32_TYPELESS",
        "R32G32_FLOAT",
        "R32G32_UINT",
        "R32G32_SINT",
        "R32G8X24_TYPELESS",
        "D32_FLOAT_S8X24_UINT",
        "R32_FLOAT_X8X24_TYPELESS",
        "X32_TYPELESS_G8X24_UINT",
        "R10G10B10A2_TYPELESS",
        "R10G10B10A2_UNORM",
        "R10G10B10A2_UINT",
        "R11G11B10_FLOAT",
        "R8G8B8A8_TYPELESS",
        "R8G8B8A8_UNORM",
        "R8G8B8A8_UNORM_SRGB",
        "R8G8B8A8_UINT",
        "R8G8B8A8_SNORM",
        "R8G8B8A8_SINT",
        "R16G16_TYPELESS",
        "R16G16_FLOAT",
        "R16G16_UNORM",
        "R16G16_UINT",
        "R16G16_SNORM",
        "R16G16_SINT",
        "R32_TYPELESS",
        "D32_FLOAT",
        "R32_FLOAT",
        "R32_UINT",
        "R32_SINT",
        "R24G8_TYPELESS",
        "D24_UNORM_S8_UINT",
        "R24_UNORM_X8_TYPELESS",
        "X24_TYPELESS_G8_UINT",
        "R8G8_TYPELESS",
        "R8G8_UNORM",
        "R8G8_UINT",
        "R8G8_SNORM",
        "R8G8_SINT",
        "R16_TYPELESS",
        "R16_FLOAT",
        "D16_UNORM",
        "R16_UNORM",
        "R16_UINT",
        "R16_SNORM",
        "R16_SINT",
        "R8_TYPELESS",
        "R8_UNORM",
        "R8_UINT",
        "R8_SNORM",
        "R8_SINT",
        "A8_UNORM",
        "R1_UNORM",
        "R9G9B9E5_SHAREDEXP",
        "R8G8_B8G8_UNORM",
        "G8R8_G8B8_UNORM",
        "BC1_TYPELESS",
        "BC1_UNORM",
        "BC1_UNORM_SRGB",
        "BC2_TYPELESS",
        "BC2_UNORM",
        "BC2_UNORM_SRGB",
        "BC3_TYPELESS",
        "BC3_UNORM",
        "BC3_UNORM_SRGB",
        "BC4_TYPELESS",
        "BC4_UNORM",
        "BC4_SNORM",
        "BC5_TYPELESS",
        "BC5_UNORM",
        "BC5_SNORM",
        "B5G6R5_UNORM",
        "B5G5R5A1_UNORM",
        "B8G8R8A8_UNORM",
        "B8G8R8X8_UNORM",
        "R10G10B10_XR_BIAS_A2_UNORM",
        "B8G8R8A8_TYPELESS",
        "B8G8R8A8_UNORM_SRGB",
        "B8G8R8X8_TYPELESS",
        "B8G8R8X8_UNORM_SRGB",
        "BC6H_TYPELESS",
        "BC6H_UF16",
        "BC6H_SF16",
        "BC7_TYPELESS",
        "BC7_UNORM",
        "BC7_UNORM_SRGB",
        "AYUV",
        "Y410",
        "Y416",
        "NV12",
        "P010",
        "P016",
        "420_OPAQUE",
        "YUY2",
        "Y210",
        "Y216",
        "NV11",
        "AI44",
        "IA44",
        "P8",
        "A8P8",
        "B4G4R4A4_UNORM",
        "P208",
        "V208",
        "V408",
        "SAMPLER_FEEDBACK_MIN_MIP_OPAQUE",
        "SAMPLER_FEEDBACK_MIP_REGION_USED_OPAQUE",
        "FORCE_UINT"]
        dxgiFormat = DXGI_FORMAT[self.Norm]
        if str(self.Norm) == "28":
            dxgiFormat=dxgiFormat+"_SRGB"
        os.chdir(self.CWD+"/ThirdParty")   
        cmd='texconv.exe "'+self.CWD+"\\"+self.FileName.split(".")[0]+'.dds" -y -nologo -srgb -ft PNG -f '+dxgiFormat+' -o '+self.SaveLoc
        #print(cmd)
        subprocess.call(cmd, shell=True)
        os.chdir(self.CWD)
        #os.remove(self.FileName.split(".")[0]+".bmp")
        os.remove(self.FileName.split(".")[0]+".dds")
    def Output(self):
        File=open(self.FileName.split(".")[0]+".dds","wb")
        thingsToAdd=[self.MagicNumber,self.dwSize,self.dwFlags,self.dwHeight,self.dwWidth,self.dwPitchOrLinearSize,self.dwDepth,self.dwMipMapCount,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwReserved1,self.dwPFSize,self.dwPFFlags,self.dwPFFourCC,self.dwPFRGBBitCount,self.dwPFRBitMask,self.dwPFGBitMask,self.dwPFBBitMask,self.dwPFABitMask,self.dwCaps,self.dwCaps2,self.dwCaps3,self.dwCaps4,self.dwReserved2]
        for thing in thingsToAdd:
            File.write(thing)
        thingsToAdd=[self.dxtdxgiFormat,self.dxtresourceDimension,self.dxtmiscFlag,self.dxtArraySize]
        for thing in thingsToAdd:
            File.write(thing)
        if self.dxtmiscFlags2 != "":
            File.write(self.dxtmiscFlags2)
        else:
            File.write(c_uint32(0))
        new=ast.literal_eval("0x"+self.Hash)
        DirName=Hex_String(Package_ID(new))+"-"+Hex_String(Entry_ID(new))+".cdat"
        file2=open(custom_direc+"/"+DirName,"rb")
        Data=file2.read()
        file2.close()
        File.write(Data)
        File.close()
        os.chdir(self.CWD+"/ThirdParty")
        cmd="texassemble.exe h-cross "+self.CWD+"/"+self.FileName.split(".")[0]+".dds"+" -y -nologo -o "+self.CWD+"/"+self.FileName.split(".")[0]+".bmp"
        print(cmd)
        subprocess.call(cmd, shell=True) 
        DXGI_FORMAT = [
        "UNKNOWN",
	"R32G32B32A32_TYPELESS",
	"R32G32B32A32_FLOAT",
	"R32G32B32A32_UINT",
	"R32G32B32A32_SINT",
	"R32G32B32_TYPELESS",
	"R32G32B32_FLOAT",
	"R32G32B32_UINT",
	"R32G32B32_SINT",
	"R16G16B16A16_TYPELESS",
	"R16G16B16A16_FLOAT",
	"R16G16B16A16_UNORM",
	"R16G16B16A16_UINT",
	"R16G16B16A16_SNORM",
	"R16G16B16A16_SINT",
	"R32G32_TYPELESS",
	"R32G32_FLOAT",
	"R32G32_UINT",
	"R32G32_SINT",
	"R32G8X24_TYPELESS",
	"D32_FLOAT_S8X24_UINT",
	"R32_FLOAT_X8X24_TYPELESS",
	"X32_TYPELESS_G8X24_UINT",
	"R10G10B10A2_TYPELESS",
	"R10G10B10A2_UNORM",
	"R10G10B10A2_UINT",
	"R11G11B10_FLOAT",
	"R8G8B8A8_TYPELESS",
	"R8G8B8A8_UNORM",
	"R8G8B8A8_UNORM_SRGB",
	"R8G8B8A8_UINT",
	"R8G8B8A8_SNORM",
	"R8G8B8A8_SINT",
	"R16G16_TYPELESS",
	"R16G16_FLOAT",
	"R16G16_UNORM",
	"R16G16_UINT",
	"R16G16_SNORM",
	"R16G16_SINT",
	"R32_TYPELESS",
	"D32_FLOAT",
	"R32_FLOAT",
	"R32_UINT",
	"R32_SINT",
	"R24G8_TYPELESS",
	"D24_UNORM_S8_UINT",
	"R24_UNORM_X8_TYPELESS",
	"X24_TYPELESS_G8_UINT",
	"R8G8_TYPELESS",
	"R8G8_UNORM",
	"R8G8_UINT",
	"R8G8_SNORM",
	"R8G8_SINT",
	"R16_TYPELESS",
	"R16_FLOAT",
	"D16_UNORM",
	"R16_UNORM",
	"R16_UINT",
	"R16_SNORM",
	"R16_SINT",
	"R8_TYPELESS",
	"R8_UNORM",
	"R8_UINT",
	"R8_SNORM",
	"R8_SINT",
	"A8_UNORM",
	"R1_UNORM",
	"R9G9B9E5_SHAREDEXP",
	"R8G8_B8G8_UNORM",
	"G8R8_G8B8_UNORM",
	"BC1_TYPELESS",
	"BC1_UNORM",
	"BC1_UNORM_SRGB",
	"BC2_TYPELESS",
	"BC2_UNORM",
	"BC2_UNORM_SRGB",
	"BC3_TYPELESS",
	"BC3_UNORM",
	"BC3_UNORM_SRGB",
	"BC4_TYPELESS",
	"BC4_UNORM",
	"BC4_SNORM",
	"BC5_TYPELESS",
	"BC5_UNORM",
	"BC5_SNORM",
	"B5G6R5_UNORM",
	"B5G5R5A1_UNORM",
	"B8G8R8A8_UNORM",
	"B8G8R8X8_UNORM",
	"R10G10B10_XR_BIAS_A2_UNORM",
	"B8G8R8A8_TYPELESS",
	"B8G8R8A8_UNORM_SRGB",
	"B8G8R8X8_TYPELESS",
	"B8G8R8X8_UNORM_SRGB",
	"BC6H_TYPELESS",
	"BC6H_UF16",
	"BC6H_SF16",
	"BC7_TYPELESS",
	"BC7_UNORM",
	"BC7_UNORM_SRGB",
	"AYUV",
	"Y410",
	"Y416",
	"NV12",
	"P010",
	"P016",
	"420_OPAQUE",
	"YUY2",
	"Y210",
	"Y216",
	"NV11",
	"AI44",
	"IA44",
	"P8",
	"A8P8",
	"B4G4R4A4_UNORM",
	"P208",
	"V208",
	"V408",
	"SAMPLER_FEEDBACK_MIN_MIP_OPAQUE",
	"SAMPLER_FEEDBACK_MIP_REGION_USED_OPAQUE",
	"FORCE_UINT"]
        #dxgiFormat = DXGI_FORMAT[self.texFormat]
        cmd="texconv.exe "+self.CWD+"\\"+self.FileName.split(".")[0]+".bmp -y -nologo -ft PNG -o "+self.SaveLoc
        subprocess.call(cmd, shell=True)
        #print(cmd)
        os.chdir(self.CWD)
        os.remove(self.FileName.split(".")[0]+".bmp")
        os.remove(self.FileName.split(".")[0]+".dds")
    
def Hash64(packagesPath):
    file1=open(os.getcwd()+"/cache/h64.txt","w")
    filelist = []
    for file in os.listdir(packagesPath)[::-1]:
        if fnmatch.fnmatch(file,'w64_*'):
            filelist.append(file)
    pkgIDs = set()
    hash64Table = {}
    # Getting all packages
    count=0
    for entry in filelist:
        count+=1
        pkgPath = packagesPath+"/"+entry
        #print(pkgPath)
        with open(pkgPath, "rb") as pkgFile:
            # Hash64 Table
            pkgFile.seek(0xB8)
            hash64TableCountBytes = pkgFile.read(4)
            hash64TableCount = struct.unpack("<I", hash64TableCountBytes)[0]
            #print(hash64TableCount)
            if hash64TableCount == 0:
                #print("empty")
                continue
            hash64TableOffsetBytes = pkgFile.read(4)
            hash64TableOffset = struct.unpack("<I", hash64TableOffsetBytes)[0]
            hash64TableOffset += 64 + 0x10

            for i in range(hash64TableOffset, hash64TableOffset + hash64TableCount * 0x10, 0x10):
                pkgFile.seek(i)
                h64ValBytes = binascii.hexlify(bytes(pkgFile.read(8))).decode()
                flipped=binascii.hexlify(bytes(hex_to_little_endian(h64ValBytes))).decode('utf-8')
                hValBytes = binascii.hexlify(bytes(pkgFile.read(4))).decode()
                flipped2=binascii.hexlify(bytes(hex_to_little_endian(hValBytes))).decode('utf-8')
                hValRef = binascii.hexlify(bytes(pkgFile.read(4))).decode()
                flipped3=binascii.hexlify(bytes(hex_to_little_endian(hValRef))).decode('utf-8')
                file1.write(str("0x"+flipped)+": "+str("0x"+flipped2)+str(": 0x"+flipped3)+"\n")
    file1.close()
def ClearDir(top):
    for file in os.listdir(os.getcwd()+"/out"):
        if file != "audio":
            os.remove(os.getcwd()+"/out/"+file)
    Popup()
def ClearMaps(top):
    for file in os.listdir(os.getcwd()+"/data/Statics"):
        os.remove(os.getcwd()+"/data/Statics/"+file)
    for file in os.listdir(os.getcwd()+"/data/Instances"):
        os.remove(os.getcwd()+"/data/Instances/"+file)
    for file in os.listdir(os.getcwd()+"/data/Materials"):
        os.remove(os.getcwd()+"/data/Materials/"+file)
    for file in os.listdir(os.getcwd()+"/data/Dynamics"):
        os.remove(os.getcwd()+"/data/Dynamics/"+file)
    for file in os.listdir(os.getcwd()+"/data/Entities"):
        os.remove(os.getcwd()+"/data/Entities/"+file)
    for file in os.listdir(os.getcwd()+"/data/DynMaterials"):
        os.remove(os.getcwd()+"/data/DynMaterials/"+file)
    for file in os.listdir(os.getcwd()+"/data/Textures"):
        os.remove(os.getcwd()+"/data/Textures/"+file)
    
    Popup()
def ClearTextures(top):
    for file in os.listdir(os.getcwd()+"/Textures"):
        if file != "cubemaps":
            os.remove(os.getcwd()+"/Textures/"+file)
    for file in os.listdir(os.getcwd()+"/Textures/Cubemaps"):
        os.remove(os.getcwd()+"/Textures/Cubemaps/"+file)
    Popup()
def ClearAudio(top):
    for File in os.listdir(os.getcwd()+"/out/audio"):
        os.remove(os.getcwd()+"/out/audio/"+File)
    Popup()
    #MainWindow(top)
def DevMenu():
    global lst, combo_box
    lst=[]
    for widget in top.winfo_children():
        widget.destroy()
    bg = PhotoImage(file = os.getcwd()+"/ThirdParty/destiny.png")
    label1 = Label(top, image = bg)
    label1.pack()
    for File in os.listdir(path):
        temp=File.split("_")
        new="_".join(temp[:(len(temp)-2)])
        if new not in lst:
            lst.append(new)
    #print(lst)
    lst.sort(reverse=False)
    useful=[]
    combo_box = ttk.Combobox(top,height=20, width=30)
    combo_box['values'] = lst
    combo_box.bind('<KeyRelease>', check_input)
    combo_box.place(x=500, y=125)
    Activity = Button(top, text="Extract Dev Strings", height=1, width=20,command=partial(DevRipper,combo_box,False))
    Activity.place(x=500, y=175)
    Activity2 = Button(top, text="Extract Dev Strings(All)", height=1, width=20,command=partial(DevRipper,combo_box,True))
    Activity2.place(x=500, y=225)
    Back = Button(top, text="Back", height=1, width=15,command=partial(MainWindow,top))
    Back.place(x=10, y=10)
    filelist = []
    top.mainloop()
def DevRipper(entry,Answer):
    filelist=[]
    for file in os.listdir(path)[::-1]:
            if fnmatch.fnmatch(file,entry.get()+"*"):       #Customize this to what pkgs you need from. Can wildcard with * for all packages, or all of a certain type.
                filelist.append(file)
    if Answer == True:
        useful=["All","Scripts"]
    else:
        useful=["0x80800000"]
    unpack_all(path,custom_direc,useful,filelist)
    file=open(os.getcwd()+"/cache/output.txt","r")
    data=file.read()
    StrData=data.split("\n")
    file.close()
    newStrData=[]
    for String in StrData:
        try:
            String.split(" // ")[1]
        except IndexError:
            continue
        try:
            int(String.split(" // ")[1])
        except ValueError:
            continue
            
        try:
            newStrData.append([(String.split(" // ")[0]),int(String.split(" // ")[1]),String.split(" // ")[2]])
        except IndexError:
            #print(String)
            continue
        
        #print(newStrData)
    newStrData.sort(key=lambda x: x[1])
    for File in os.listdir(custom_direc):
        if File != "audio":
            #continue
            Pointers=[]
            #print(File)
            file=open(custom_direc+"/"+File,"rb")
            Data=binascii.hexlify(bytes(file.read())).decode()
            temp=[Data[i:i+8] for i in range(0, len(Data), 8)]
            FileHash=False
            count=0
            StringStartP=False
            for Hash in temp:
                if Hash == "00000000":
                    continue
                if Hash == "65008080":
                    StringStartP=count
                    break
                if len(list(Hash)) == 8:
                    flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode())
                    dec=ast.literal_eval("0x"+flipped)
                    PkgID=Hex_String(Package_ID(dec))
                    EntryID=Hex_String(Entry_ID(dec))
                    DirName=PkgID+"-"+EntryID
                    if DirName.upper() == File.split(".")[0].upper():
                        FileHash=Hash
                        break
                count+=1
                    
                
            Max=len(temp)
            Pointer=0
            DataBlocks=[]
            DataBlocks2=[]
            DataBlocks3=[]
            DataBlocks4=[]
            StringPointer=""
            DataBlocks5=[]
            DataBlocks6=[]
            DataBlocks7=[]
            DataBlocks8=[]
            DataBlocks9=[]
            DataBlocks10=[]
            DataBlocks11=[]
            DataBlocks12=[]
            DataBlocks13=[]
            DataBlocks14=[]
            DataBlocks15=[]
            DataBlocks16=[]
            DataBlocks17=[]
            DataBlocks18=[]
            DataBlocks19=[]
            for i in range(len(temp)):
                if temp[Pointer] == "65008080":
                    StringPointer=Pointer
                    break
                if temp[Pointer].upper() == "1EB13A0F":
                    print("FOUND: "+File)
                if temp[Pointer] == "79008080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks.append(dat)
                    #Pointer+=5
                if temp[Pointer] == "53008080":
                    dat=temp[Pointer+1:Pointer+2]
                    dat.append((Pointer+1)*4)
                    #print(dat)
                    #Pointer+=2
                    DataBlocks2.append(dat)
                if temp[Pointer] == "5a9b8080":
                    dat=temp[Pointer+1:Pointer+2]
                    dat.append((Pointer+1)*4)
                    DataBlocks3.append(dat)  
                    #Pointer+=2
                if temp[Pointer] == "0d018080":
                    flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(temp[Pointer+1]))).decode())
                    Count=ast.literal_eval("0x"+flipped)
                    Pointer+=3
                    for i in range(Count):
                        dat=temp[Pointer:Pointer+3]
                        dat.append((Pointer)*4)
                        DataBlocks4.append(dat)
                        Pointer+=4
                    #print(dat)
                    #Pointer-=2
                if temp[Pointer] == "70008080":
                    
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    #print(dat)
                    
                    DataBlocks5.append(dat)
                    #Pointer+=2
                if temp[Pointer] == "ef008080":  ####TODO
                    dat=temp[Pointer+1:Pointer+12]
                    dat.append((Pointer+1)*4)
                    DataBlocks7.append(dat)  
                    #Pointer+=2
                #if temp[Pointer] == "04008080":  ####TODO----Find Hash Val and ref to name 
                #    dat=temp[Pointer+1:Pointer+2]
                #    dat.append((Pointer+1)*4)
                #    DataBlocks3.append(dat)  
                    #Pointer+=2
                if temp[Pointer] == "01998080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks8.append(dat)
                if temp[Pointer] == "fe988080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks9.append(dat)
                if temp[Pointer] == "00998080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks10.append(dat)
                if temp[Pointer] == "47998080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks11.append(dat)
                if temp[Pointer] == "00998080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks12.append(dat)
                if temp[Pointer] == "189b8080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks13.append(dat)
                if temp[Pointer] == "b68e8080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks14.append(dat)
                if temp[Pointer] == "029b8080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks15.append(dat)
                if temp[Pointer] == "46998080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks16.append(dat)
                if temp[Pointer] == "b68e8080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks17.append(dat)
                if temp[Pointer] == "b38e8080":
                    dat=temp[Pointer+1:Pointer+5]
                    dat.append((Pointer+1)*4)
                    DataBlocks18.append(dat)
                #if temp[Pointer] == "46998080":
                #    dat=temp[Pointer+1:Pointer+5]
                #    dat.append((Pointer+1)*4)
                #    DataBlocks19.append(dat)
                if FileHash != False:
                    if temp[Pointer] == FileHash.lower():
                        dat=temp[Pointer+1:Pointer+5]
                        dat.append((Pointer+1)*4)
                        DataBlocks6.append(dat)  
                Pointer+=1
            #print(DataBlocks)
            DataBlocks.reverse()
            Offset=len(Data)
            Run=False
            First=True
            outfile=open(os.getcwd()+"/Scripts/"+File.split(".")[0]+".txt","w")
            outfile.close()
            for Hash in temp:
                dat=StringHash(Hash,newStrData,"")
                if dat != False:
                    if First == True:
                        outfile=open(os.getcwd()+"/Scripts/"+File.split(".")[0]+".txt","a")
                        outfile.write("Strings\n")
                        outfile.write(dat+"\n")
                        First=False
                    else:
                        outfile.write(dat+"\n")
            if First == False:
                outfile.close()
            if DataBlocks != []:
                outfile=open(os.getcwd()+"/Scripts/"+File.split(".")[0]+".txt","a")
                outfile.write("Block1  "+str(len(DataBlocks))+"\n")
                for Block in DataBlocks:
                    #CurrentRef=[]
                    flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[0]))).decode())
                    new=ast.literal_eval("0x"+flipped)
                    flipped2=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[2]))).decode())
                    new2=ast.literal_eval("0x"+flipped2)
                    file.seek(new+Block[4])
                    Length=Offset-(new+Block[4])
                    Text=[]
                    for i in range(150):
                        temp=binascii.hexlify(bytes(file.read(1))).decode()
                        #print(str(temp))
                        if str(temp) != "00":
                            #print(binascii.unhexlify(temp).decode())
                            Text.append(binascii.unhexlify(temp).decode())
                        else:
                            
                            break
                    CurrentRef="".join(Text)
                    Offset=new+Block[4]
                    outfile.write(str(Block))
                    outfile.write("\n"+CurrentRef+"\n")
                    #print(str(CurrentRef).split("\x00")[0])
                    file.seek(new2+Block[4]+8)
                    Text=[]
                    for i in range(150):
                        temp=binascii.hexlify(bytes(file.read(1))).decode()
                        #print(str(temp))
                        if str(temp) != "00":
                            #print(binascii.unhexlify(temp).decode())
                            Text.append(binascii.unhexlify(temp).decode())
                        else:
                            
                            break
                    Length=Offset-(new+Block[4])
                    CurrentRef="".join(Text)
                    Offset=new+Block[4]
                    outfile.write(CurrentRef+"\n\n\n")
                    #print("\n\n\n")
                outfile.close()
            
            
            if DataBlocks2 != []:
                outfile=open(os.getcwd()+"/Scripts/"+File.split(".")[0]+".txt","a")
                outfile.write("Block2  "+str(len(DataBlocks2))+"\n")
                for Block in DataBlocks2:
                    flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[0]))).decode())
                    new=ast.literal_eval("0x"+flipped)
                    file.seek(new+Block[1])
                    #Length=Offset-(new)
                    Text=[]
                    for i in range(150):
                        temp=binascii.hexlify(bytes(file.read(1))).decode()
                        #print(str(temp))
                        if str(temp) != "00":
                            #print(binascii.unhexlify(temp).decode())
                            try:
                                Text.append(binascii.unhexlify(temp).decode())
                            except UnicodeDecodeError:
                                continue
                        else:
                            break
                    CurrentRef="".join(Text)
                    #Offset=new+Block[4]
                    outfile.write(str(Block))
                    outfile.write("\n"+CurrentRef+"\n\n\n")
                outfile.close()
          
            if DataBlocks3 != []:
               
                outfile=open(os.getcwd()+"/Scripts/"+File.split(".")[0]+".txt","a")
                outfile.write("Block3  "+str(len(DataBlocks3))+"\n")
                for Block in DataBlocks3:
                    flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[0]))).decode())
                    new=ast.literal_eval("0x"+flipped)
                    file.seek(new+Block[1])
                    #Length=Offset-(new)
                    Text=[]
                    for i in range(150):
                        temp=binascii.hexlify(bytes(file.read(1))).decode()
                        #print(str(temp))
                        if str(temp) != "00":
                            #print(binascii.unhexlify(temp).decode())
                            try:
                                Text.append(binascii.unhexlify(temp).decode())
                            except UnicodeDecodeError:
                                continue
                        else:
                            break
                    CurrentRef="".join(Text)
                    #Offset=new+Block[4]
                    outfile.write(str(Block))
                    outfile.write("\n"+CurrentRef+"\n\n\n")
                outfile.close()
           
            if DataBlocks4 != []:
                
           
                outfile=open(os.getcwd()+"/Scripts/"+File.split(".")[0]+".txt","a")
                outfile.write("Block4  "+str(len(DataBlocks4))+"\n")
                #print(DataBlocks4)
                for Block in DataBlocks4:
                    if Block[0] != "00000000":
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[0]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[3])
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
                    if Block[2] != "00000000":
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[2]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[3]+8)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))
                        outfile.write(str(Block))
                        outfile.write("\n"+CurrentRef+"\n\n")
                    
                outfile.close()
            outfile=open(os.getcwd()+"/Scripts/"+File.split(".")[0]+".txt","a")
                
            if DataBlocks5 != []:
                
                outfile.write("Block5  "+str(len(DataBlocks5))+"\n")
                #print("b5")
                #print(DataBlocks5)
                for Block in DataBlocks5:   #Pointer0 Len?1 StrPoint3 Offset4
                    
                    try:
                        Block[3][4:]
                    except IndexError:
                        continue
                    except TypeError:
                        continue
                    
                    if Block[3][4:] == "8080":
                        Block2Find=Block[1]
                    else:
                        Block2Find=Block[3]
                    if Block2Find != "00000000":
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block2Find))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                     
                        for i in range(150):
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            
                            else:
                                break
                            
                        if Text == []:
                            continue
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        outfile.write("".join(str(Block)))
                        outfile.write("\n"+CurrentRef+"\n")
                    if Block[0] != "00000000":
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[0]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4])
                        temp=binascii.hexlify(bytes(file.read(4))).decode()
                        if temp == "00000000":
                            continue
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(temp))).decode())
                        new2=ast.literal_eval("0x"+flipped)
                        newSet=new2+new+Block[4]
                        #print(newSet)
                        file.seek(int(newSet))
                        Text=[]
                        for i in range(100):
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            
                            else:
                                break
                            
                            if Text == []:
                                continue
                        CurrentRef="".join(Text)
                        outfile.write("\n"+CurrentRef+"\n\n\n")
            outfile.write("\nBlock6\n")
            #if DataBlocks6 != []:
                #print(DataBlocks6)
            for Block in DataBlocks6:
                if len(Block) != 5:
                    continue
                if len(list(Block[3])) != 8:
                    continue
                if Block[3] != "00000000":
                    flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                    new=ast.literal_eval("0x"+flipped)
                    file.seek(new+Block[4]+12)
                    #Length=Offset-(new)
                    Text=[]
                    for i in range(150):
                        
                        temp=binascii.hexlify(bytes(file.read(1))).decode()
                        #print(str(temp))
                        if str(temp) != "00":
                            #print(binascii.unhexlify(temp).decode())
                            try:
                                Text.append(binascii.unhexlify(temp).decode())
                            except UnicodeDecodeError:
                                continue
                        else:
                            break
                    CurrentRef="".join(Text)
                    #Offset=new+Block[4]
                    outfile.write(str(Block))

                    outfile.write("\n"+CurrentRef+"\n\n")
                if Block[1] != "00000000":
                    flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[1]))).decode())
                    new=ast.literal_eval("0x"+flipped)
                    file.seek(new+Block[4]+4)
                    #Length=Offset-(new)
                    Text=[]
                    for i in range(150):
                        
                        temp=binascii.hexlify(bytes(file.read(1))).decode()
                        #print(str(temp))
                        if str(temp) != "00":
                            #print(binascii.unhexlify(temp).decode())
                            try:
                                Text.append(binascii.unhexlify(temp).decode())
                            except UnicodeDecodeError:
                                continue
                        else:
                            break
                    CurrentRef="".join(Text)
                    #Offset=new+Block[4]
                    outfile.write(str(Block))
            if DataBlocks7 != []:
                #print(DataBlocks7)
                outfile.write("\nBlock7\n\n")
                for Block in DataBlocks7:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if Block[0] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[0]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[11])
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
                    if Block[2] != "00000000":
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[2]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[11]+8)
                        
                        Text=binascii.hexlify(bytes(file.read(4))).decode()
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        outfile.write("\n"+CurrentRef+"\n\n")
                        
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Text))).decode())
                        try:
                            new2=ast.literal_eval("0x"+flipped)
                        except SyntaxError:
                            continue
                        file.seek(new+Block[11]+8+new2)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        outfile.write("\n"+CurrentRef+"\n\n")
                    if Block[3] != "00000000":
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[11]+12-4)
                        #Length=Offset-(new)
                        Text=binascii.hexlify(bytes(file.read(4))).decode()
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        outfile.write("\n"+CurrentRef+"\n\n")
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Text))).decode())
                        try:
                            new2=ast.literal_eval("0x"+flipped)
                        except SyntaxError:
                            continue
                        file.seek(new+Block[11]+8+new2)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        outfile.write("\n"+CurrentRef+"\n\n")
                    if Block[5] != "00000000":
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[5]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[11]+20-4)
                        Text=binascii.hexlify(bytes(file.read(4))).decode()
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        outfile.write("\n"+CurrentRef+"\n\n")
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Text))).decode())
                        try:
                            new2=ast.literal_eval("0x"+flipped)
                        except SyntaxError:
                            continue
                        file.seek(new+Block[11]+8+new2)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        outfile.write("\n"+CurrentRef+"\n\n")
                       

                        #outfile.write("\n"+CurrentRef+"\n\n")
            if DataBlocks8 != []:
                #print(DataBlocks8)
                outfile.write("\nBlock8\n\n")
                for Block in DataBlocks8:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if Block[3] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
            if DataBlocks9 != []:
                if len(Block) != 5:
                        continue
                outfile.write("\nBlock9\n\n")
                for Block in DataBlocks9:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if Block[3] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
            if DataBlocks10 != []:
                if len(Block) != 5:
                        continue
                outfile.write("\nBlock10\n\n")
                for Block in DataBlocks10:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if Block[3] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
            if DataBlocks11 != []:
                
                outfile.write("\nBlock11\n\n")
                for Block in DataBlocks11:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if len(Block) != 5:
                        continue
                    if Block[3] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
            if DataBlocks12 != []:
                
                outfile.write("\nBlock12\n\n")
                for Block in DataBlocks12:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if len(Block) != 5:
                        continue
                    if Block[3] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
            if DataBlocks13 != []:
                #print(DataBlocks13)
                outfile.write("\nBlock13\n\n")
                for Block in DataBlocks13:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if len(Block) != 5:
                        continue
                    if Block[3] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
            if DataBlocks14 != []:
                
                outfile.write("\nBlock14\n\n")
                for Block in DataBlocks14:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if len(Block) != 5:
                        continue
                    if Block[3] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
            #print("15")
            if DataBlocks15 != []:
                
                outfile.write("\nBlock15\n\n")
                for Block in DataBlocks15:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if len(Block) != 5:
                        continue
                    if Block[3] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
            #print("16")
            if DataBlocks16 != []:
                
                outfile.write("\nBlock16\n\n")
                for Block in DataBlocks16:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if len(Block) != 5:
                        continue
                    if Block[3] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
            #print("17")
            if DataBlocks17 != []:
                
                outfile.write("\nBlock17\n\n")
                for Block in DataBlocks17:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if len(Block) != 5:
                        continue
                    if Block[3] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
            #print("18")
            if DataBlocks18 != []:
                
                outfile.write("\nBlock18\n\n")
                for Block in DataBlocks18:#0 str ref, 2 rel off 3 rel off  5 RelOff
                    if len(Block) != 5:
                        continue
                    if Block[3] != "00000000":
                        outfile.write(str(Block))
                        flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Block[3]))).decode())
                        new=ast.literal_eval("0x"+flipped)
                        file.seek(new+Block[4]+12)
                        #Length=Offset-(new)
                        Text=[]
                        for i in range(150):
                            
                            temp=binascii.hexlify(bytes(file.read(1))).decode()
                            #print(str(temp))
                            if str(temp) != "00":
                                #print(binascii.unhexlify(temp).decode())
                                try:
                                    Text.append(binascii.unhexlify(temp).decode())
                                except UnicodeDecodeError:
                                    continue
                            else:
                                break
                        CurrentRef="".join(Text)
                        #Offset=new+Block[4]
                        #outfile.write(str(Block))

                        outfile.write("\n"+CurrentRef+"\n\n")
            #print("ref")
            outfile.write("References\n")
            RefFiles=[]
            temp=[Data[i:i+8] for i in range(0, len(Data), 8)]
            for Hash in temp:
                if len(Hash) == 8:
                    #print("ran")
                    temp=[Hash[i:i+2] for i in range(0, len(Hash), 2)]
                    if temp[3] == "80" or temp[3] == "81":
                        flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode()
                        new=ast.literal_eval("0x"+flipped)
                        PkgID=Hex_String(Package_ID(new))
                        EntryID=Hex_String(Entry_ID(new))
                        DirName=PkgID.upper()+"-"+EntryID.upper()+".bin"
                        #print(DirName)
                        #if DirName in os.listdir(custom_direc):
                        if DirName not in RefFiles:
                            RefFiles.append(DirName)
            if RefFiles != []:
                for Ref in RefFiles:
                    outfile.write(Ref+"\n")
            #print("test")
            outfile.write("TESTING\n")
            temp=[Data[i:i+8] for i in range(0, len(Data), 8)]
            TempLen=len(temp)
            Pointer=0
            for Hash in temp:
                if Hash == "65008080":
                    break
                if len(Hash) != 8:
                    continue
                if Hash != "00000000":
                    #print(Hash)
                    flipped=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode())
                    new=ast.literal_eval("0x"+flipped)
                    #Pointer+=1
                    #if new != 0:
                    Offset=(Pointer*4)+new
                    #print(Offset)
                    if StringPointer != "":
                        #print((len(temp)*4))
                        if int((StringPointer*4)) < Offset < int((TempLen*4)):
                            #print("Run")
                            
                        #print(newSet)
                            file.seek(Offset)
                            Text=[]
                            for i in range(150):
                                
                                temp=binascii.hexlify(bytes(file.read(1))).decode()
                                #print(str(temp))
                                if str(temp) != "00":
                                    #print(binascii.unhexlify(temp).decode())
                                    try:
                                        Text.append(binascii.unhexlify(temp).decode())
                                    except UnicodeDecodeError:
                                        continue
                                else:
                                    break
                            CurrentRef="".join(Text)
                            outfile.write("\n"+Hash+","+str(Pointer*4))
                            outfile.write("\n"+CurrentRef+"\n\n")
                            #CurrentRef="".join(Text)
                        #outfile.write("\n"+Hash+"\n"+CurrentRef+"\n\n")
                Pointer+=1
            if StringPointer != "":
                file.seek((StringPointer+2)*4)
                temp=binascii.hexlify(bytes(file.read())).decode()
                temp=temp.split("00")
                temp=binascii.unhexlify("20".join(temp)).decode()
                outfile.write("\n\nDump\n\n"+temp)
            outfile.close()
    Dev=open("mechout.txt","w")
    Dev.close()
    Dev=open("mechout.txt","a")
    for File in os.listdir(custom_direc):
        if File != "audio":
            file=open(custom_direc+"/"+File,"rb")
            Data=binascii.hexlify(bytes(file.read())).decode()
            count=0
            Data=[Data[i:i+8] for i in range(0, len(Data), 8)]
            for Hash in Data:
                if Hash == "65008080":
                    string="".join(Data[count+2:])
                    #print(File)
                    try:
                        temp=bytearray.fromhex(string).decode()
                    except:
                        continue
                    else:
                        temp2=temp.split(" ")
                        
                        Dev.write("/".join(temp2)+"\n")
                
                                   
                count+=1
    Dev.close()

    #for file in os.listdir(os.getcwd()+"/out"):
    #    if file != "audio":
    #        os.remove(os.getcwd()+"/out/"+file)
    Popup()
def Popup():
    tkinter.messagebox.showinfo(" ", "Done")
def NormalRipper(entry,Type):
    filelist=[]
    if Type == "Single":
        for file in os.listdir(path)[::-1]:
            if fnmatch.fnmatch(file,entry.get()+"*"):
                filelist.append(file)
    else:
        temp=entry.get().split("_")
        print(temp)
        new="_".join(temp[:len(temp)-1])
        print(new)
        for file in os.listdir(path)[::-1]:
            if fnmatch.fnmatch(file,new+"*"):
                filelist.append(file)
    useful=["Norm"]
    unpack_all(path,custom_direc,useful,filelist)
    lengths=[]
    for File in os.listdir(custom_direc):
        if File != "audio":
            if File.split(".")[1] == "norm":
                Tex=DDS(File,"Norm")
    for file in os.listdir(os.getcwd()+"/out"):
        if file != "audio":
            os.remove(os.getcwd()+"/out/"+file)
    Popup()
def twos_complement(hexstr, bits):
    value = int(hexstr, 16)
    if value & (1 << (bits - 1)):
        value -= 1 << bits
    return value
class LoadZone:
    def __init__(self,Name,InstCount,Ref):
        self.FileName=Name
        self.Statics=[]
        self.H64Sort=SortH64(ReadHash64())
        self.StaticMeta=[]
        self.Ref=Ref
        self.CWD=os.getcwd()
        self.DynNames=[]
        self.DynInstances=[]
        self.PullStatics()
        #self.ExtractFBX()
        self.InstCount=InstCount
        #if ans.upper() == "Y":
        #self.RipStatics()
        self.RipOwnStatics()
        self.PullStaticMeta()
        self.PullStaticData()
        self.OutputCFG()
        #self.PullDyns()
        #self.RipDyns()
        #self.PullMechanicStructs()
        #print(self.Statics)
        #print(str(len(self.Statics)))
   
    def RipDyns(self):
        os.chdir(self.CWD+"/ThirdParty")
        for Dyn in self.DynNames:
            cmd='MDE -p "'+path+'" -o "'+self.CWD+'/data/Entities" -i '+Dyn.upper()
            #print(cmd)
            ans=subprocess.call(cmd, shell=True)
            #for File in os.listdir(currentPath+"/ThirdParty/output/"+str(pkgID)):
            try:
                shutil.move(self.CWD+"/data/Entities/"+Dyn.upper()+"/"+Dyn.upper()+".fbx",self.CWD+"/data/Entities/"+Dyn.lower()+".fbx")
            except FileNotFoundError:
                continue
            else:
                os.rmdir(self.CWD+"/data/Entities/"+Dyn.upper())
        os.chdir(self.CWD)        
                    
    def PullDyn(self,Hash):
        os.chdir(self.CWD+"/ThirdParty")
        
        cmd='MDE -p "'+path+'" -o "'+self.CWD+'/data/Dynamics" -i '+Hash
        #print(cmd)
        ans=subprocess.call(cmd, shell=True)
        #for File in os.listdir(currentPath+"/ThirdParty/output/"+str(pkgID)):
        try:
            shutil.move(self.CWD+"/data/Dynamics/"+Hash+"/"+Hash+".fbx",self.CWD+"/data/Dynamics/"+Hash+".fbx")
        except FileNotFoundError:
            u=1
        else:
            os.rmdir(self.CWD+"/data/Dynamics/"+Hash)
        os.chdir(self.CWD)
                
    def PullDyns(self):
        #print(self.Ref)
        file=open(custom_direc+"/"+self.Ref,"rb")
        Tables=[]
        file.seek(0x50)
        dat=binascii.hexlify(bytes(file.read())).decode()
        Data=[dat[i:i+8] for i in range(0, len(dat), 8)]
        file.close()
        self.DynNames=[]
        self.DynInstances=[]
        for Hash in Data:
            flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8')
            num=ast.literal_eval("0x"+flipped)
            Name=Hex_String(Package_ID(num))+"-"+Hex_String(Entry_ID(num))
            if Name not in Tables:
                Tables.append(Name)
        for Table in Tables:
            file=open(custom_direc+"/"+Table+".dt","rb")
            Length=file.read()
            if len(Length) < 144:
                continue
            file.close()
            file=open(custom_direc+"/"+Table+".dt","rb")
            file.seek(0x20)
            Num=binascii.hexlify(bytes(file.read(1))).decode()
            Num=ast.literal_eval("0x"+Num)
            file.seek(0x28)
            temp=binascii.hexlify(bytes(file.read(4))).decode()

            if temp == "85988080":
                #print(Table)
                file.seek(0x30)
                Data=binascii.hexlify(bytes(file.read())).decode()
                Data=[Data[i:i+288] for i in range(0, len(Data), 288)]
                count=0
                for Dyn in Data:
                    if count >= Num:
                        break
                    #print(Dyn)
                    count+=1
                    DynDat=[Dyn[i:i+8] for i in range(0, len(Dyn), 8)]
                    #print(DynDat)
                    rotX=binascii.hexlify(bytes(hex_to_little_endian(DynDat[0]))).decode('utf-8')
                    rotY=binascii.hexlify(bytes(hex_to_little_endian(DynDat[1]))).decode('utf-8')
                    rotZ=binascii.hexlify(bytes(hex_to_little_endian(DynDat[2]))).decode('utf-8')
                    rotW=binascii.hexlify(bytes(hex_to_little_endian(DynDat[3]))).decode('utf-8')
                    PosX=binascii.hexlify(bytes(hex_to_little_endian(DynDat[4]))).decode('utf-8')
                    PosY=binascii.hexlify(bytes(hex_to_little_endian(DynDat[5]))).decode('utf-8')
                    PosZ=binascii.hexlify(bytes(hex_to_little_endian(DynDat[6]))).decode('utf-8')
                    ScaleX=binascii.hexlify(bytes(hex_to_little_endian(DynDat[7]))).decode('utf-8')
                    rotX=struct.unpack('!f', bytes.fromhex(rotX))[0]
                    rotY=struct.unpack('!f', bytes.fromhex(rotY))[0]
                    rotZ=struct.unpack('!f', bytes.fromhex(rotZ))[0]
                    rotW=struct.unpack('!f', bytes.fromhex(rotW))[0]
                    PosX=struct.unpack('!f', bytes.fromhex(PosX))[0]
                    PosY=struct.unpack('!f', bytes.fromhex(PosY))[0]
                    PosZ=struct.unpack('!f', bytes.fromhex(PosZ))[0]
                    ScaleX=struct.unpack('!f', bytes.fromhex(ScaleX))[0]
                    Name=binascii.hexlify(bytes(hex_to_little_endian(DynDat[12]+DynDat[13]))).decode('utf-8')
                    ValidDyn=False
                    for Line1 in Hash64Data:
                        Lines=Line1.split(": ")
                        #print(Lines)
                        if Lines[0].lower() == str("0x"+Name):
                            temp=list(Lines[1])
                            temp="".join(temp[2:])
                            DynHash=binascii.hexlify(bytes(hex_to_little_endian(temp))).decode('utf-8')
                            #print(DynHash)
                            if DynHash not in self.DynNames:
                                
                                #print(Table)
                                self.DynNames.append(DynHash)
                            ValidDyn=True
                    if ValidDyn == True:
                        file1=open(os.getcwd()+"/data/Instances/"+DynHash.lower()+".inst","a")
                        file1.write(str(rotX)+","+str(rotY)+","+str(rotZ)+","+str(rotW)+","+str(PosX)+","+str(PosY)+","+str(PosZ)+","+str(ScaleX)+"\n")
                        file1.close()


                    
                    
                    
                
                    
        
    def PullStatics(self):
        file=open(custom_direc+"/"+self.FileName,"rb")
        file.seek(128)
        Offset=binascii.hexlify(bytes(file.read(4))).decode()
        Offset=binascii.hexlify(bytes(hex_to_little_endian(Offset))).decode('utf-8')
        Offset=ast.literal_eval("0x"+Offset)
        file.seek(128+Offset)
        Length=binascii.hexlify(bytes(file.read(4))).decode()
        Length=binascii.hexlify(bytes(hex_to_little_endian(Length))).decode('utf-8')
        Length=ast.literal_eval("0x"+Length)
        file.seek(128+Offset+16)
        self.Statics=[]
        for i in range(Length):
            self.Statics.append(binascii.hexlify(bytes(file.read(4))).decode())
    def PullStaticMeta(self):
        file=open(custom_direc+"/"+self.FileName,"rb")
        Data=binascii.hexlify(bytes(file.read())).decode()
        file.seek(144)
        Offset=binascii.hexlify(bytes(file.read(4))).decode()
        Offset=binascii.hexlify(bytes(hex_to_little_endian(Offset))).decode('utf-8')
        Offset=ast.literal_eval("0x"+Offset)
        file.seek(144+Offset)
        Length=binascii.hexlify(bytes(file.read(4))).decode()
        Length=binascii.hexlify(bytes(hex_to_little_endian(Length))).decode('utf-8')
        Length=ast.literal_eval("0x"+Length)
        file.seek(144+Offset+16)
        self.StaticMeta=[]
        for i in range(Length):
            temp=binascii.hexlify(bytes(file.read(8))).decode()
            self.StaticMeta.append(temp)
        
        

    def OutputCFG(self):
        count=0
        for Static in self.StaticMeta:
            Data=[Static[i:i+4] for i in range(0, len(Static), 4)]
            flipped=binascii.hexlify(bytes(hex_to_little_endian(Data[0]))).decode('utf-8')
            NumofInstance=ast.literal_eval("0x"+stripZeros(flipped))
            flipped=binascii.hexlify(bytes(hex_to_little_endian(Data[1]))).decode('utf-8')
            InstanceOffset=ast.literal_eval("0x"+stripZeros(flipped))
            flipped2=binascii.hexlify(bytes(hex_to_little_endian(Data[2]))).decode('utf-8')
            Index=ast.literal_eval("0x"+stripZeros(flipped2))
            #Tally+=NumofInstance
            file=open(self.CWD+"/data/Instances/"+self.Statics[Index]+".inst","a")
            for i in range(NumofInstance):
                data=",".join(self.StaticData[InstanceOffset+i])
                file.write(str(data)+"\n")
            file.close()
        #print(Tally)
            
            
    def PullStaticData(self):
        self.StaticData=[]
        file=open(custom_direc+"/"+self.FileName,"rb")
        #print(self.FileName)
        file.seek(0x48)
        Offset=binascii.hexlify(bytes(file.read(4))).decode()
        Offset=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Offset))).decode('utf-8'))
        Offset=ast.literal_eval("0x"+Offset)
        file.seek(72+Offset)
        Length=binascii.hexlify(bytes(file.read(4))).decode()
        Length=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Length))).decode('utf-8'))
        Length=ast.literal_eval("0x"+Length)
        file.seek(72+Offset+16)
        for i in range(Length):
            
            Dat=binascii.hexlify(bytes(file.read(64))).decode()
            Dat=[Dat[i:i+8] for i in range(0, len(Dat), 8)]
            rotX=binascii.hexlify(bytes(hex_to_little_endian(Dat[0]))).decode('utf-8')
            rotY=binascii.hexlify(bytes(hex_to_little_endian(Dat[1]))).decode('utf-8')
            rotZ=binascii.hexlify(bytes(hex_to_little_endian(Dat[2]))).decode('utf-8')
            rotW=binascii.hexlify(bytes(hex_to_little_endian(Dat[3]))).decode('utf-8')
            #PosDat=[Position[i:i+8] for i in range(0, len(Position), 8)]
            PosX=binascii.hexlify(bytes(hex_to_little_endian(Dat[4]))).decode('utf-8')
            PosY=binascii.hexlify(bytes(hex_to_little_endian(Dat[5]))).decode('utf-8')
            PosZ=binascii.hexlify(bytes(hex_to_little_endian(Dat[6]))).decode('utf-8')
            #ScaleDat=[Scale[i:i+8] for i in range(0, len(Scale), 8)]
            ScaleX=binascii.hexlify(bytes(hex_to_little_endian(Dat[7]))).decode('utf-8')
            rotX=struct.unpack('!f', bytes.fromhex(rotX))[0]
            rotY=struct.unpack('!f', bytes.fromhex(rotY))[0]
            rotZ=struct.unpack('!f', bytes.fromhex(rotZ))[0]
            rotW=struct.unpack('!f', bytes.fromhex(rotW))[0]
            PosX=struct.unpack('!f', bytes.fromhex(PosX))[0]
            PosY=struct.unpack('!f', bytes.fromhex(PosY))[0]
            PosZ=struct.unpack('!f', bytes.fromhex(PosZ))[0]
            ScaleX=struct.unpack('!f', bytes.fromhex(ScaleX))[0]
            self.StaticData.append([str(rotX),str(rotY),str(rotZ),str(rotW),str(PosX),str(PosY),str(PosZ),str(ScaleX)])
        file.close()
        #print(self.StaticData[0])
        #print(self.StaticData[len(self.StaticData)-1])
    def GetBufferInfo(self):
        IndexBufferList=[]
        IndexHeaderList=[]
        VertexBufferList=[]
        VertexHeaderList=[]
        CWD=os.getcwd()
        os.chdir(CWD+"/out/")
        Files=sorted(os.listdir(CWD+"/out/"), key=os.path.getmtime)
        os.chdir(CWD)
        for File in Files:
            #if File.split("-")[0] != "0215":
            #    continue
            if File == "audio":
                continue
            temp=File.split(".")
            if temp[1] == "vert":
                VertexBufferList.append(File)
            elif temp[1] == "index":
                IndexBufferList.append(File)
            elif temp[1] == "iheader":
                IndexHeaderList.append(File)
            elif temp[1] == "vheader":
                VertexHeaderList.append(File)
        return VertexBufferList,IndexBufferList,IndexHeaderList,VertexHeaderList
    def RipOwnStatics(self):
        VertexBufferList,IndexBufferList,IndexHeaderList,VertexHeaderList=self.GetBufferInfo()
        TexturesToRip=[]
        outcount=0
        #print(len(self.Statics))
        for Static in self.Statics:
            #if Static != "2554c280":
                #continue
            #print(outcount)
            start=binascii.hexlify(bytes(hex_to_little_endian(Static))).decode('utf-8')

            new=ast.literal_eval("0x"+start)
            pkg = Hex_String(Package_ID(new))
            ent = Hex_String(Entry_ID(new))
            Bank=pkg+"-"+ent+".model"
            file=open(os.getcwd()+"/out/"+Bank,"rb")
            mainData=binascii.hexlify(bytes(file.read())).decode()
            file.seek(0x8)
            s = binascii.hexlify(bytes(file.read(4))).decode()
            file.seek(0x50)
            x=binascii.hexlify(bytes(file.read(4))).decode()
            xScale=struct.unpack('!f', bytes.fromhex(binascii.hexlify(bytes(hex_to_little_endian(x))).decode('utf-8')))[0]  #vert
            y=binascii.hexlify(bytes(file.read(4))).decode()
            yScale=struct.unpack('!f', bytes.fromhex(binascii.hexlify(bytes(hex_to_little_endian(y))).decode('utf-8')))[0]
            z=binascii.hexlify(bytes(file.read(4))).decode()
            zScale=struct.unpack('!f', bytes.fromhex(binascii.hexlify(bytes(hex_to_little_endian(z))).decode('utf-8')))[0]
            MainData=[mainData[i:i+8] for i in range(0, len(mainData), 8)]
            Materials=[]
            FoundMat=False
            flipped=binascii.hexlify(bytes(hex_to_little_endian(s))).decode('utf-8')
            new=ast.literal_eval("0x"+flipped)
            SubFileU32=new
            pkg = Hex_String(Package_ID(new))
            ent = Hex_String(Entry_ID(new))
            Bank=pkg+"-"+ent+".sub" #subfile
            sub=open(os.getcwd()+"/out/"+Bank,"rb")
            SubData=binascii.hexlify(bytes(sub.read())).decode()
            sub.seek(0x4C)
            Scale=binascii.hexlify(bytes(sub.read(4))).decode()
            Scale=struct.unpack('!f', bytes.fromhex(stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Scale))).decode('utf-8'))))[0]
            sub.seek(0x50)
            sub.seek(0x10)
            MatTable=binascii.hexlify(bytes(sub.read(4))).decode()
            MaterialData=[]
            for Hash in MainData:
                if Hash == "00000000":
                    continue
                if FoundMat == True:
                    Data=[Hash[i:i+2] for i in range(0, len(Hash), 2)]
                    if (Data[3] == "80") or (Data[3] == "81"):
                        Materials.append(Hash)
                if Hash == "14008080":
                    FoundMat=True
            #print(Materials)
            if MatTable != "00000000":
                MatOffset=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(MatTable))).decode('utf-8')))
                sub.seek(16+MatOffset)
                MatCount=binascii.hexlify(bytes(sub.read(4))).decode()
                MatCount=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(MatCount))).decode('utf-8')))
                sub.seek(16+MatOffset+16)
                for i in range(MatCount):
                    MatDat=binascii.hexlify(bytes(sub.read(6))).decode()
                    MaterialData.append([ast.literal_eval("0x"+stripZeros(MatDat[:2])),Materials[i]])
            #print(MaterialData)
                    
                    

            DataHashes=[]
            SubData=[SubData[i:i+8] for i in range(0, len(SubData), 8)]
            count=0
            for Hash in SubData:
                if Hash == "366d8080":
                    SubData=SubData[count:]
                count+=1
            for Hash in SubData:
                temp=[Hash[i:i+2] for i in range(0, len(Hash), 2)]
                if (temp[3] == "80") or (temp[3] == "81"):
                    if temp[2] != "80":
                    #isHash
                        flipped=binascii.hexlify(bytes(hex_to_little_endian("".join(temp)))).decode('utf-8')
                        DataHashes.append(flipped)  #index at 0 vert at 1
            #print("MADE IT")
            if len(DataHashes) < 2:
                #print("Not enough data")
                continue
            if len(DataHashes) > 2:
                #print("Finding UV")
                sub.seek(0x48)
                uvXScale=binascii.hexlify(bytes(sub.read(4))).decode()
                uvXScale=struct.unpack('!f', bytes.fromhex(binascii.hexlify(bytes(hex_to_little_endian(uvXScale))).decode('utf-8')))[0]
                sub.seek(0x50)
                uvYScale=binascii.hexlify(bytes(sub.read(4))).decode()
                uvYScale=struct.unpack('!f', bytes.fromhex(stripZeros(binascii.hexlify(bytes(hex_to_little_endian(uvYScale))).decode('utf-8'))))[0]
                uvXOff=binascii.hexlify(bytes(sub.read(4))).decode()
                if uvXOff == "00000000":
                    uxXOff=0
                else:
                    uvXOff=struct.unpack('!f', bytes.fromhex(stripZeros(binascii.hexlify(bytes(hex_to_little_endian(uvXOff))).decode('utf-8'))))[0]
                uvYOff=binascii.hexlify(bytes(sub.read(4))).decode()
                if uvYOff == "00000000":
                    uvYOff=0
                else:
                    uvYOff=struct.unpack('!f', bytes.fromhex(stripZeros(binascii.hexlify(bytes(hex_to_little_endian(uvYOff))).decode('utf-8'))))[0]
                FindUV=True
                FirstVert=False
            indFound=False
            vertFound=False
            new=ast.literal_eval("0x"+DataHashes[1])
            new=new+1
            pkg = Hex_String(Package_ID(new))
            ent = Hex_String(Entry_ID(new))
            IndexHeaderVal=ast.literal_eval("0x"+DataHashes[0])
            pkg = Hex_String(Package_ID(IndexHeaderVal))
            ent = Hex_String(Entry_ID(IndexHeaderVal))
            Bank=pkg+"-"+ent+".iheader"
            IndexHeader=open(os.getcwd()+"/out/"+Bank,"rb")
            IndexHeaderData=binascii.hexlify(bytes(IndexHeader.read(24))).decode()
            temp=[IndexHeaderData[i:i+8] for i in range(0, len(IndexHeaderData), 8)]
            IndexLength=int(ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(temp[2]))).decode('utf-8'))))
            IndexCount=0
            for Item in IndexHeaderList:
                if Item.lower() == Bank.lower():
                    IndexFileOffset=IndexCount
                    test=binascii.hexlify(bytes(open(os.getcwd()+"/out/"+IndexBufferList[IndexFileOffset],"rb").read())).decode()
                    if int(len(test)/2) != IndexLength:
                        for i in range(20):
                            
                            IndexFileOffset=IndexFileOffset+i+1
                            try:
                                IndexBufferList[IndexFileOffset]
                            except IndexError:
                                continue
                            test=binascii.hexlify(bytes(open(os.getcwd()+"/out/"+IndexBufferList[IndexFileOffset],"rb").read())).decode()
                            if int(len(test)/2) == IndexLength:
                                indFound=True
                                break
                        if indFound==True:
                            break
                        for i in range(20):
                            
                            IndexFileOffset=IndexFileOffset-i-1
                            try:
                                IndexBufferList[IndexFileOffset]
                            except IndexError:
                                continue
                           # print(VertexBufferList[VertexFileOffset])
                            test=binascii.hexlify(bytes(open(os.getcwd()+"/out/"+IndexBufferList[IndexFileOffset],"rb").read())).decode()
                            #print(len(test))
                            if int(len(test)/2) == IndexLength:
                                indFound=True
                                break
                        if indFound==True:
                            break
                    else:
                        indFound=True
                        break
                    #indFound = True
                IndexCount+=1
            #print(IndexBufferList[IndexFileOffset])
            
            VertexHeaderVal=ast.literal_eval("0x"+DataHashes[1])
            pkg = Hex_String(Package_ID(VertexHeaderVal))
            ent = Hex_String(Entry_ID(VertexHeaderVal))
            Bank=pkg+"-"+ent+".vheader"
            VertexCount=0
            for Item in VertexHeaderList:
                if Item.lower() == Bank.lower():
                    VHead=open(os.getcwd()+"/out/"+Bank,"rb")
                    VertLen=int(ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(binascii.hexlify(bytes(VHead.read(4))).decode()))).decode('utf-8'))))
                    #print("LENNN "+str(Len))
                    VertexFileOffset=VertexCount
                    test=binascii.hexlify(bytes(open(os.getcwd()+"/out/"+VertexBufferList[VertexFileOffset],"rb").read())).decode()
                    if int(len(test)/2) != VertLen:
                        for i in range(20):
                            
                            VertexFileOffset=VertexFileOffset+i+1
                            try:
                                VertexBufferList[VertexFileOffset]
                            except IndexError:
                                continue
                            #print(VertexBufferList[VertexFileOffset])
                            test=binascii.hexlify(bytes(open(os.getcwd()+"/out/"+VertexBufferList[VertexFileOffset],"rb").read())).decode()
                            #print(len(test))
                            if int(len(test)/2) == VertLen:
                                vertFound=True
                                break
                        if vertFound==True:
                            break
                        for i in range(20):
                            
                            VertexFileOffset=VertexFileOffset-i-1
                            try:
                                VertexBufferList[VertexFileOffset]
                            except IndexError:
                                continue
                           # print(VertexBufferList[VertexFileOffset])
                            test=binascii.hexlify(bytes(open(os.getcwd()+"/out/"+VertexBufferList[VertexFileOffset],"rb").read())).decode()
                            #print(len(test))
                            if int(len(test)/2) == VertLen:
                                vertFound=True
                                break
                        if vertFound==True:
                            break
                    else:
                        vertFound=True
                        break
                                
                            
                                                
                    
                    
                VertexCount+=1
            VertexHeader=open(os.getcwd()+"/out/"+Bank,"rb")
            VertexHeaderData=binascii.hexlify(bytes(VertexHeader.read(0xC))).decode()
            temp=[VertexHeaderData[i:i+8] for i in range(0, len(VertexHeaderData), 8)]
            VertexLength=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(temp[0]))).decode('utf-8')))
            UVFound=False
            if len(DataHashes) > 2:
                VertexHeaderVal=ast.literal_eval("0x"+DataHashes[2])#####FIX UV
                pkg = Hex_String(Package_ID(VertexHeaderVal))
                ent = Hex_String(Entry_ID(VertexHeaderVal))
                Bank=pkg+"-"+ent+".vheader"
                VertexCount=0
                UVHeader=open(os.getcwd()+"/out/"+Bank,"rb")
                UVLength=binascii.hexlify(bytes(UVHeader.read(4))).decode()
                print(Bank)
                #print(UVLength)
                UVLength=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(UVLength))).decode('utf-8')))
                FileOrder=[]
                for i in range(8):
                    
                    pkg = Hex_String(Package_ID(SubFileU32-8+i))
                    ent = Hex_String(Entry_ID(SubFileU32-8+i))
                    name=pkg+"-"+ent
                    try:
                        file=open(os.getcwd()+"/out/"+name+".index","rb")
                    except FileNotFoundError:
                        u=1
                    else:
                        FileOrder.append([name,"index"])
                    try:
                        file=open(os.getcwd()+"/out/"+name+".iheader","rb")
                    except FileNotFoundError:
                        u=1
                    else:
                        FileOrder.append([name,"iheader"])
                    try:
                        file=open(os.getcwd()+"/out/"+name+".vheader","rb")
                    except FileNotFoundError:
                        u=1
                    else:
                        FileOrder.append([name,"vheader"])
                    try:
                        file=open(os.getcwd()+"/out/"+name+".vert","rb")
                    except FileNotFoundError:
                        u=1
                    else:
                        FileOrder.append([name,"vert"])
                tally=0
                for File in FileOrder:
                    if File[1] == "vert":
                        tally+=1
                        if tally == 2:
                            UVName=File[0]+"."+File[1]
                            print(UVName)
                            UVFound=True
            VColorFound=False
            if len(DataHashes) > 3:
                VertexHeaderVal=ast.literal_eval("0x"+DataHashes[3])
                pkg = Hex_String(Package_ID(VertexHeaderVal))
                ent = Hex_String(Entry_ID(VertexHeaderVal))
                Bank=pkg+"-"+ent+".vheader"
                VertexCount=0
                for Item in VertexHeaderList:
                    if Item.lower() == Bank.lower():
                        VColorOffset=VertexCount
                        VColorFound = True
                    VertexCount+=1
            if vertFound == False:
                for i in range(int(8)):
                #    
                    new=int(ast.literal_eval("0x"+DataHashes[1]))+i
                    pkg = Hex_String(Package_ID(new))
                    ent = Hex_String(Entry_ID(new))
                    #print(pkg+"-"+ent)
                    if vertFound == False:     #very poor way of finding buffers
                        Bank=pkg+"-"+ent+".vert"
                        #print(Bank)
                        try:
                            vert=open(os.getcwd()+"/data/"+Bank,"rb") #hash +1???
                        except FileNotFoundError:
                            u=1
                        else:
                            test=binascii.hexlify(bytes(vert.read())).decode()
                            if int(len(test)/2) == VertLen:
                                vertFound=True
                                for i in range(len(VertexBufferList)):
                                    if VertexBufferList[i] == Bank:
                                        VertexFileOffset=i
                                        vertFound=True
                                        break
                if vertFound == True:
                    break
                for i in range(int(8)):
                #    
                    new=int(ast.literal_eval("0x"+DataHashes[1]))-i
                    pkg = Hex_String(Package_ID(new))
                    ent = Hex_String(Entry_ID(new))
                    #print(pkg+"-"+ent)
                    if vertFound == False:     #very poor way of finding buffers
                        Bank=pkg+"-"+ent+".vert"
                        #print(Bank)
                        try:
                            vert=open(os.getcwd()+"/data/"+Bank,"rb") #hash +1???
                        except FileNotFoundError:
                            u=1
                        else:
                            test=binascii.hexlify(bytes(vert.read())).decode()
                            if int(len(test)/2) == VertLen:
                                vertFound=True
                                for i in range(len(VertexBufferList)):
                                    if VertexBufferList[i] == Bank:
                                        VertexFileOffset=i
                                        vertFound=True
                                        break
                    if vertFound == True:
                        break
            if indFound == False:
                for i in range(int(8)):
                #    
                    new=int(ast.literal_eval("0x"+DataHashes[0]))+i
                    pkg = Hex_String(Package_ID(new))
                    ent = Hex_String(Entry_ID(new))
                    #'print(pkg+"-"+ent)
                    if indFound == False:     #very poor way of finding buffers
                        Bank=pkg+"-"+ent+".index"
                        #print(Bank)
                        try:
                            vert=open(os.getcwd()+"/data/"+Bank,"rb") #hash +1???
                        except FileNotFoundError:
                            u=1
                        else:
                            test=binascii.hexlify(bytes(vert.read())).decode()
                            if int(len(test)/2) == IndexLength:
                                indFound=True
                                for i in range(len(VertexBufferList)):
                                    if IndexBufferList[i] == Bank:
                                        IndexFileOffset=i
                                        indFound=True
                                        break
                if indFound == True:
                    break
                for i in range(int(8)):
                #    
                    new=int(ast.literal_eval("0x"+DataHashes[0]))-i
                    pkg = Hex_String(Package_ID(new))
                    ent = Hex_String(Entry_ID(new))
                    #'print(pkg+"-"+ent)
                    if indFound == False:     #very poor way of finding buffers
                        Bank=pkg+"-"+ent+".index"
                        #print(Bank)
                        try:
                            index=open(os.getcwd()+"/data/"+Bank,"rb") #hash +1???
                        except FileNotFoundError:
                            u=1
                        else:
                            test=binascii.hexlify(bytes(index.read())).decode()
                            if int(len(test)/2) == IndexLength:
                                indFound=True
                                for i in range(len(IndexBufferList)):
                                    if IndexBufferList[i] == Bank:
                                        IndexFileOffset=i
                                        indFound=True
                                        break
                    if indFound == True:
                        break
            if (vertFound == True) and (indFound == True):
                verts=[]
                #print("RUNNING")
                norms=[]
                Vert=open(os.getcwd()+"/out/"+VertexBufferList[VertexFileOffset],"rb")
                #print(VertexBufferList[VertexFileOffset])
                
                for i in range(int(99999)):
                    s = binascii.hexlify(bytes(Vert.read(16))).decode()
                    if s == "":
                        break
                    #print(s)
                    Data=[s[i:i+4] for i in range(0, len(s), 4)]
                    if len(Data) < 8:
                        continue
                    x= (twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Data[0]))).decode('utf-8'),16)/32767)*(Scale)
                    y= (twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Data[1]))).decode('utf-8'),16)/32767)*(Scale)
                    z= (twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Data[2]))).decode('utf-8'),16)/32767)*(Scale)
                    xNorm=(twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Data[3]))).decode('utf-8'),16)/32767)*(Scale*10)
                    yNorm=(twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Data[4]))).decode('utf-8'),16)/32767)*(Scale*10)
                    zNorm=(twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Data[5]))).decode('utf-8'),16)/32767)*(Scale*10)
                    wNorm=(twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Data[6]))).decode('utf-8'),16)/32767)*(Scale*10)
                    verts.append([x,y,z])
                    norms.append([xNorm,yNorm,zNorm,wNorm])
                #print(verts)
                if UVFound == True:
                    UV=open(os.getcwd()+"/out/"+UVName,"rb")
                    Data=binascii.hexlify(bytes(UV.read())).decode()
                    Length=len(Data)/8
                    UV.seek(0)
                    UVData=[]
                    for i in range(int(999999)):
                        Data=binascii.hexlify(bytes(UV.read(4))).decode()
                        if Data == "":
                            break
                        Uvs=[Data[i:i+4] for i in range(0, len(Data), 4)]
                        U= ((twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Uvs[0]))).decode('utf-8'),16)/32767) * float(uvYScale)) + float(uvXOff)
                        V= ((twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Uvs[1]))).decode('utf-8'),16)/32767) * float(uvYScale)*-1) - (float(uvYOff-1))
                        #print(U,V)
                        UVData.append([U,V])
                    
                for Hash in MainData:
                    if Hash == "00000000":
                        continue
                    if FoundMat == True:
                        Data=[Hash[i:i+2] for i in range(0, len(Hash), 2)]
                        if (Data[3] == "80") or (Data[3] == "81"):
                            if Hash not in Materials:
                                Materials.append(Hash)
                    if Hash == "14008080":
                        FoundMat=True
                #ParseMaterials
                MatRef=[]
                for Material in Materials:
                    Mats=[]
                    flipped=binascii.hexlify(bytes(hex_to_little_endian(Material))).decode('utf-8')
                    new=ast.literal_eval("0x"+flipped)
                    pkg = Hex_String(Package_ID(new))
                    #print(result)
                    ent = Hex_String(Entry_ID(new))
                    MatBank=pkg+"-"+ent+".mat"
                    #print(MatBank)
                    try:
                        MatFile=open(os.getcwd()+"/out/"+MatBank,"rb")
                    except FileNotFoundError:
                        continue
                    MatFile.seek(0x3E0)
                    Num=binascii.hexlify(bytes(MatFile.read(4))).decode()
                    Num=stripZeros(binascii.hexlify(bytes(hex_to_little_endian(Num))).decode('utf-8'))
                    if Num == "":
                        continue
                    Num=ast.literal_eval("0x"+Num)
                    MatFile.seek(0x3F0)
                    for i in range(Num):
                        Mat=binascii.hexlify(bytes(MatFile.read(0x18))).decode()
                        temp=[Mat[i:i+8] for i in range(0, len(Mat), 8)]
                        #print(temp)
                        try:
                            temp[4]
                        except IndexError:
                            continue
                        hashCheck=[temp[4][i:i+2] for i in range(0, len(temp[4]), 2)]
                        if (hashCheck == "80") or (hashCheck == "81"):
                            flipped=binascii.hexlify(bytes(hex_to_little_endian(temp[4]))).decode('utf-8')
                            new=ast.literal_eval="0x"+flipped
                            pkg = Hex_String(Package_ID(new))
                            #print(result)
                            ent = Hex_String(Entry_ID(new))
                            MatToAppend=pkg+"-"+ent
                            if MatToAppend not in Mats:
                                Mats.append(MatToAppend)
                        else:
                            h64=str(temp[4])+str(temp[5])
                            flipped=binascii.hexlify(bytes(hex_to_little_endian(h64))).decode('utf-8')
                            new=ast.literal_eval("0x"+flipped)
                            MatToAppend=Hash64Search(self.H64Sort,new)
                            if MatToAppend != False:
                                new=ast.literal_eval(MatToAppend)
                                pkg = Hex_String(Package_ID(new))
                                #print(result)
                                ent = Hex_String(Entry_ID(new))
                                MatToAppend=pkg+"-"+ent
                                if MatToAppend not in Mats:
                                    Mats.append(MatToAppend)
                            
                    if Mats != []:
                        MatRef.append([Material,Mats])
                Parts=True
                if Parts == True:
                    sub.seek(0x20)
                    Offset=binascii.hexlify(bytes(sub.read(4))).decode()
                    if Offset != "00000000":
                        Offset=binascii.hexlify(bytes(hex_to_little_endian(Offset))).decode('utf-8')
                        Offset=ast.literal_eval("0x"+stripZeros(Offset))
                        sub.seek(32+Offset)
                        Length=binascii.hexlify(bytes(sub.read(4))).decode()
                        Length=binascii.hexlify(bytes(hex_to_little_endian(Length))).decode('utf-8')
                        Length=ast.literal_eval("0x"+stripZeros(Length))
                        sub.seek(48+Offset)
                        PartData=[]
                        PartLengths=[]
                        for i in range(Length):
                            PartDat=binascii.hexlify(bytes(sub.read(12))).decode()
                            #if PartDat[21] == "1":
                            PartData.append(PartDat)
                            #print(PartDat)
                            temp=[PartDat[i:i+8] for i in range(0, len(PartDat), 8)]
                            if temp[0] != "00000000":
                                
                                PartLengths.append([ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(temp[0]))).decode('utf-8'))),PartDat[21],ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(temp[1]))).decode('utf-8')))])
                            else:
                                PartLengths.append([0,PartDat[21],ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(temp[1]))).decode('utf-8')))])
                new=ast.literal_eval("0x"+DataHashes[0])
                new=new-1
                pkg = Hex_String(Package_ID(new))
                #print(result)
                ent = Hex_String(Entry_ID(new))
                Bank=pkg+"-"+ent+".index"
                #ind=open(os.getcwd()+"/data/"+Bank,"rb") #hash +1???
                faces=[]
                ind=open(os.getcwd()+"/out/"+IndexBufferList[IndexFileOffset],"rb")
                ind.seek(0x0)
                Length = binascii.hexlify(bytes(ind.read())).decode()
                ind.seek(0x0)
                #print(IndexBufferList[IndexFileOffset])
                #print(VertexBufferList[VertexFileOffset])

                #print(faces[len(faces)-1]) 
                
                if VColorFound == True:
                    VColData=[]
                    VColor=open(os.getcwd()+"/out/"+VertexBufferList[VColorOffset],"rb")
                    for i in range(int(999999)):
                        Data=binascii.hexlify(bytes(UV.read(4))).decode()
                        if Data == "":
                            break
                        Uvs=[Data[i:i+2] for i in range(0, len(Data), 2)]
                        x=twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Uvs[0]))).decode('utf-8'),8)
                        y=twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Uvs[1]))).decode('utf-8'),8)
                        z=twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Uvs[2]))).decode('utf-8'),8)
                        w=twos_complement(binascii.hexlify(bytes(hex_to_little_endian(Uvs[3]))).decode('utf-8'),8)
                        #print(U,V)
                        VColData.append([x,y,z,w])
                memory_manager = fbx.FbxManager.Create()
                scene = fbx.FbxScene.Create(memory_manager, '')
                count99=0
                MaxDetail=ast.literal_eval("0x"+PartLengths[0][1])
                for Part in PartLengths:
                    #print(Part)
                    Detail=ast.literal_eval("0x"+Part[1])
                    if Detail != MaxDetail:
                        #print("broke")
                        break
                    my_mesh = fbx.FbxMesh.Create(scene, Static+"_"+str(count99))
                    count=0
                    
                    Length = binascii.hexlify(bytes(ind.read())).decode()
                    ind.seek(int(Part[0]*2))
                    faces=[]
                    #print(IndexHeaderData)
                    if IndexHeaderData[3] == "1":
                        ReadLen=4
                    else:
                        ReadLen=2
                    #print(ReadLen)
                    for i in range(round(Part[2]/3)):
                        x = binascii.hexlify(bytes(ind.read(ReadLen))).decode()
                        if x == "":
                            break
                        x=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(x))).decode('utf-8')))
                        y = binascii.hexlify(bytes(ind.read(ReadLen))).decode()
                        if y == "":
                            break
                        y=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(y))).decode('utf-8')))
                        z = binascii.hexlify(bytes(ind.read(ReadLen))).decode()
                        if z == "":
                            break
                        z=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(z))).decode('utf-8')))
                        
                        faces.append([x,y,z])
                    #print(faces)
                    #print(verts)
                    #print(len(verts))
                    usedVerts=[]
                    tempCheck=[]
                    count5=0
                    #print(verts)
                    for Face in faces:
                        for Val in Face:
                            try:
                                verts[int(Val)]
                            except IndexError:
                                continue
                            if int(Val) not in tempCheck:
                                usedVerts.append([verts[int(Val)],int(Val)])
                                tempCheck.append(int(Val))
                    for Face in usedVerts:
                        Face.append(count5)
                        count5+=1
                            
                            
                    count=0
        
                    usedVerts.sort(key=lambda x: x[1])
                    my_mesh.InitControlPoints(len(usedVerts))
                    for Set in usedVerts:
                        v = fbx.FbxVector4(Set[0][0]+xScale, Set[0][1]+yScale, Set[0][2]+zScale)
                        my_mesh.SetControlPointAt( v, count )
                        count+=1
                    for Face in faces:
                        my_mesh.BeginPolygon()
                        for Val in Face:
                            vertex_index = binary_search(usedVerts,int(Val))
                            my_mesh.AddPolygon(vertex_index)
                            my_mesh.EndPolygon()
                            
                    cubeLocation = (0, 0, 0)
                    cubeScale    = (Scale, Scale, Scale)

                    newNode = addNode(scene, Static+"_"+str(count99), location = cubeLocation)
                    rootNode = scene.GetRootNode()
                    #rootNode.LclTranslation.set(fbx.FbxDouble3(xScale, yScale, zScale))
                    rootNode.AddChild( newNode )

                    newNode.SetNodeAttribute( my_mesh )
                    newNode.ScalingActive.Set(1)
                    px = fbx.FbxDouble3(1, 1, 1)
                    if UVFound == True:
                        
                        layer = my_mesh.GetLayer(0)
                        uvLayer = fbx.FbxLayerElementUV.Create(my_mesh, "uv")
                        uvLayer.SetMappingMode(fbx.FbxLayerElement.EMappingMode.eByControlPoint)
                        uvLayer.SetReferenceMode(fbx.FbxLayerElement.EReferenceMode.eDirect)
                        for Vert in usedVerts:
                            Pos=Vert[1]
                            try:
                                UVData[Pos]
                            except IndexError:
                                continue
                            uvLayer.GetDirectArray().Add(fbx.FbxVector2(float(UVData[Pos][0]),float(UVData[Pos][1])))
            #for UV in UVData:
                        count=0
                        try:
                            layer.SetUVs(uvLayer)
                        except AttributeError:
                            u=1
                    normLayer = fbx.FbxLayerElementNormal.Create(my_mesh, Static)
                    normLayer.SetMappingMode(fbx.FbxLayerElement.EMappingMode.eByControlPoint)
                    normLayer.SetReferenceMode(fbx.FbxLayerElement.EReferenceMode.eDirect)
                    colorLayer=fbx.FbxLayerElementVertexColor.Create(my_mesh, Static)
                    colorLayer.SetMappingMode(fbx.FbxLayerElement.EMappingMode.eByControlPoint)
                    colorLayer.SetReferenceMode(fbx.FbxLayerElement.EReferenceMode.eDirect)
                    if VColorFound == True:
                        for Vert in usedVerts:
                            try:
                                Pos=Vert[1]
                            except IndexError:
                                continue
                            try:
                                VColData[Pos]
                            except IndexError:
                                continue
                            colorLayer.GetDirectArray().Add(fbx.FbxVector4(VColData[Pos][0],VColData[Pos][1],VColData[Pos][2],VColData[Pos][3]))
                        
                    
                    # Create the materials.
                    # Each polygon face will be assigned a unique material.
                    count=0
                    lLayer = my_mesh.GetLayer(0)
                   
                    for Vert in usedVerts:
                        Pos=Vert[1]
                        normLayer.GetDirectArray().Add(fbx.FbxVector4(norms[Pos][0],norms[Pos][1],norms[Pos][2],norms[Pos][3]))
                        
                    count99+=1
                
                filename = os.getcwd()+"\\data\\Statics\\"+Static+".fbx"
                FbxCommon.SaveScene(memory_manager, scene, filename)
                memory_manager.Destroy()
            else:
                print("Fucked it")
                
            countMat=0
            if len(MaterialData) > 0:
                MatOut=open(os.getcwd()+"/data/Materials/"+Static+".txt","w")
                #print(MaterialData)
                #print(MatRef)
                for i in range(count99):
                    for Mat in MaterialData:
                        if int(Mat[0]) == int(countMat):
                            CheckName=Mat[1]
                            for Texs in MatRef:
                                #print(Texs)
                                if CheckName == Texs[0]:
                                    for Texture in Texs[1]:
                                        if Texture not in TexturesToRip:
                                            TexturesToRip.append(Texture)
                                    Textures=",".join(Texs[1])
                                    MatOut.write(Static+"_"+str(countMat)+" : "+Mat[1]+" : "+Textures+"\n")
                                    break
                    countMat+=1
                MatOut.close()

        RipTextures(TexturesToRip)
def GetPackageName(ID):
    for File in os.listdir(path):
        temp=File.split("_")
        if temp[len(temp)-2] == ID:
            break
    return File
    
def RipTextures(TexturesToRip):
    Existing=os.listdir(os.getcwd()+"/data/Textures")
    #print(Existing)
    for Texture in TexturesToRip:
        DatName=Texture+".png"
        if DatName not in Existing:
            Package=GetPackageName(Texture.split("-")[0])
            Header=ExtractSingleEntry.unpack_entry(path,custom_direc,Package,Texture.split("-")[1])
            Hash=Header[120:]
            Hash=ast.literal_eval("0x"+binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8'))
            pkg = Hex_String(Package_ID(int(Hash)))
            ent = Hex_String(Entry_ID(int(Hash)))
            Package2=GetPackageName(pkg)
            Main=ExtractSingleEntry.unpack_entry(path,custom_direc,Package2,ent)
            Tex=DDS(Texture,"Norm",Header,Main,os.getcwd()+"/data/Textures")
        

def SortH64(Hash64Data):
    newH64=[]
    for Line in Hash64Data:
        if Line == "":
            continue
        temp=Line.split(": ")
        new=ast.literal_eval(temp[0])
        newH64.append([int(new),temp[1],temp[2]])
    newH64.sort(key=lambda x: x[0])
    #for row in newH64:
    #    print(row)
    return newH64
def Hash64Search2(Hash64Data,Input):
    Found=False
    ans=binary_search2(Hash64Data,int(Input))
    #print(ans)
    if str(ans) != "-1":
        Found=True
    if Found == True:
        return Hash64Data[ans]
    else:
        return False    
def Hash64Search(Hash64Data,Input):
    Found=False
    ans=binary_search2(Hash64Data,int(Input))
    #print(ans)
    if str(ans) != "-1":
        Found=True
    if Found == True:
        return Hash64Data[ans][1]
    else:
        return False
    
def addNode( pScene, nodeName, **kwargs ):
    
    # Obtain a reference to the scene's root node.
    #scaling = kwargs["scaling"]
    location = kwargs["location"]
    newNode = fbx.FbxNode.Create( pScene, nodeName )
    newNode.LclScaling.Set(fbx.FbxDouble3(1, 1, 1))
    newNode.LclTranslation.Set(fbx.FbxDouble3(location[0]*1, location[1]*1, location[2]*1))
    return newNode
           
def CubeRipper(entry):
    filelist=[]
    temp=entry.get().split("_")
    new="_".join(temp[:len(temp)-1])
    print(new)
    for file in os.listdir(path)[::-1]:
        if fnmatch.fnmatch(file,new+"*"):
            filelist.append(file)
    useful=["Cube"]
    unpack_all(path,custom_direc,useful,filelist)
    lengths=[]
    for File in os.listdir(custom_direc):
        if File != "audio":
            if File.split(".")[1] == "cube":
                Tex=DDS(File,"Cube")
                print("ran")
    for file in os.listdir(os.getcwd()+"/out"):
        if file != "audio":
            os.remove(os.getcwd()+"/out/"+file)
    Popup()
def RipAllTextures(entry):
    currentPath=os.getcwd()
    filelist=[]
    pkgID=entry.get().split("_")[len(entry.get().split("_"))-1]
    
    cmd= 'D2TextureRipper.exe -p "'+path+'" -o '+os.getcwd()+'/Textures -i '+pkgID
    os.chdir(os.getcwd()+"/ThirdParty")
    ans=subprocess.call(cmd, shell=True)
    os.chdir(currentPath)
    Popup()
def TextureWindow(top):
    global lst, combo_box
    lst=[]
    for widget in top.winfo_children():
        widget.destroy()
    bg = PhotoImage(file = os.getcwd()+"/ThirdParty/destiny.png")
    label1 = Label(top, image = bg)
    label1.pack()
    for File in os.listdir(path):
        temp=File.split("_")
        if "video" not in temp:
            new="_".join(temp[:(len(temp)-1)])
            if new not in lst:
                lst.append(new)
    #print(lst)
    useful=[]
    combo_box = ttk.Combobox(top,height=20, width=40)
    combo_box['values'] = lst
    combo_box.bind('<KeyRelease>', check_input)
    combo_box.place(x=500, y=125)
    Normal = Button(top, text="Extract Normal", height=1, width=30,command=partial(NormalRipper,combo_box,"Single"))
    Normal.place(x=500, y=175)
    NormalBulk = Button(top, text="Extract Normal(Bulk)", height=1, width=30,command=partial(NormalRipper,combo_box,"Bulk"))
    NormalBulk.place(x=500, y=225)
    Better = Button(top, text="Third Party (recommended)", height=1, width=30,command=partial(RipAllTextures,combo_box))
    Better.place(x=500, y=275)
    Cubemap = Button(top, text="Extract Cube", height=1, width=30,command=partial(CubeRipper,combo_box))
    Cubemap.place(x=750, y=175)
    Back = Button(top, text="Back", height=1, width=15,command=partial(MainWindow,top))
    Back.place(x=10, y=10)
    ClearTex = Button(top, text="Clear Textures", height=1, width=15,command=partial(ClearTextures,top))
    ClearTex.place(x=1000, y=470)
    filelist = []
    top.mainloop()
def LoadNames(top,ActId,ActName):
    for widget in top.winfo_children():
        widget.destroy()
    lengths=[]
    print(ActName)
    Rotations=[]
    Translations=[]
    DynamicHashes=[]
    file=open(os.getcwd()+"/cache/ActivityHashes.txt","r")
    Data=file.read().split("\n")
    file.close()
    for Act in Data:
        temp=Act.split(" : ")
        #print(temp)
        if ActName == temp[1]:
            StringContainer=temp[3]
            break
    Hash64Data=ReadHash64()
    for Line1 in Hash64Data:
        Lines=Line1.split(": ")
        #print(Lines)
        if Lines[0].lower() == str("0x"+StringContainer):
            Ref=Lines[1]
            num=ast.literal_eval(Ref)
            StrRef=Hex_String(Package_ID(num)).upper()+"-"+Hex_String(Entry_ID(num)).upper()
            break
    LoadNames=[]
    file=open(os.getcwd()+"/cache/output.txt","r")
    data=file.read()
    StrData=data.split("\n")
    file.close()
    newStrData=[]
    for String in StrData:
        try:
            String.split(" // ")[1]
        except IndexError:
            continue
        try:
            int(String.split(" // ")[1])
        except ValueError:
            continue
            
        try:
            newStrData.append([(String.split(" // ")[0]),int(String.split(" // ")[1]),String.split(" // ")[2]])
        except IndexError:
            #print(String)
            continue
        
        #print(newStrData)
    newStrData.sort(key=lambda x: x[1])
    MapHashes=[]
    OrderedLoads=[]
    for File in os.listdir(custom_direc):
        if File != "audio":
            if File.split(".")[1] == "act":
                
                file=open(custom_direc+"/"+File,"rb")
                Data=binascii.hexlify(bytes(file.read())).decode()
                file.close()
                DataSplit=[Data[i:i+16] for i in range(0, len(Data), 16)]
                if ActId in DataSplit:
                    file=open(custom_direc+"/"+File,"rb")
                    Hash=binascii.hexlify(bytes(file.read(4))).decode()
                    flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8')
                    new=ast.literal_eval("0x"+stripZeros(flipped))
                    currentPointer=4
                    while currentPointer < new:
                        Hash=binascii.hexlify(bytes(file.read(4))).decode()
                        currentPointer+=4
                        if Hash == "1d898080":
                            currentPointer+=12
                            file.read(12)
                            MapHash=binascii.hexlify(bytes(file.read(8))).decode()
                            flipped=binascii.hexlify(bytes(hex_to_little_endian(MapHash))).decode('utf-8')
                            MapHashes.append(flipped)
                            currentPointer+=8
                    file=open(custom_direc+"/"+File,"rb")
                    Data=binascii.hexlify(bytes(file.read())).decode()
                    file.close()
                    DataSplit=[Data[i:i+8] for i in range(0, len(Data), 8)]
                    for Hash in DataSplit:
                        if "0000" not in Hash:
                            dat=StringHash(Hash,newStrData,StrRef)
                            if dat != False:
                                if dat not in OrderedLoads:
                                    OrderedLoads.append(dat)
                            
                             
    TopNames=[]
    Hash64Data=ReadHash64()
    for Map in MapHashes:
        for Line1 in Hash64Data:
            Lines=Line1.split(": ")
            #print(Lines)
            #print(Lines)
            Hash="0x"+str(Map)
            #print(Hash)
            if str(Lines[0].lower()) == Hash:
                print("MATCH")
                LhashFile=Lines[1]
                num=ast.literal_eval(LhashFile)
                name=Hex_String(Package_ID(num))+"-"+Hex_String(Entry_ID(num))+".top"
                TopNames.append(name.lower())
                
                
                break
    print(MapHashes)
    print(TopNames)
    #time.sleep(60)
    for File in os.listdir(custom_direc):
        if File != "audio":
             if File.lower() in TopNames:
                 file=open(custom_direc+"/"+File,"rb")
                 file.seek(0x8)
                 Hash=binascii.hexlify(bytes(file.read(4))).decode()
                 flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8')
                 new=ast.literal_eval("0x"+flipped)
                 RefHash=Hex_String(Package_ID(new))+"-"+Hex_String(Entry_ID(new))+".mref"
                 file.seek(0x18)
                 Hash=binascii.hexlify(bytes(file.read(4))).decode()
                 file.close()
                 flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8')
                 new=ast.literal_eval("0x"+flipped)
                 LoadHash=new
                 StringTxt=""
                 possibleNames=[]
                 for String in StrData:
                     Lines=String.split(" // ")
                     try:
                         Lines[1]
                     except IndexError:
                         pass
                     else:
                         if Lines[1] == str(new):
                             if Lines[0] == StrRef:
                                 StringTxt=Lines[2]
                                 possibleNames.append(StringTxt)
                             
                 LoadNames.append([str([possibleNames]),File,RefHash])
    count=0
    for Load in LoadNames:
        file=open(custom_direc+"/"+Load[2],"rb")#mref
        print(Load[2])
        Data=binascii.hexlify(bytes(file.read())).decode()
        data=[Data[i:i+32] for i in range(0, len(Data), 32)]
        file.close() ##############################################################################################
        LoadHashes=[]
        First=True
        #print(len(data))
        for Line in data:
            split=[Line[i:i+8] for i in range(0, len(Line), 8)]
            if split[0].lower() == "ffffffff":
                Hash=str(split[2])+str(split[3])
                flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8')
                #print(flipped)
                for Line1 in Hash64Data:
                    Lines=Line1.split(": ")
                    #print(Lines)
                    if Lines[0].lower() == str("0x"+flipped):
                        LhashFile=Lines[1]
                        LoadNames[count].append(LhashFile)
                        break
        count+=1
    newLoadNames=[]
    #print(OrderedLoads)
    #for Load in OrderedLoads:
    #    for LoadName in LoadNames:
    #        if Load in LoadName[0]:
    #            newLoadNames.append(LoadName)
    #            break
        
            
        
            
    #print(LoadNames)
    #LoadNames=newLoadNames
    count=0    
    for Load in LoadNames:
        count+=1
        print(str(count)+" "+Load[0]+Load[2])
    global lst, combo_box
    lst=LoadNames
    #answer=int(input("Enter which Load you want to pull from: "))
    bg = PhotoImage(file = os.getcwd()+"/ThirdParty/destiny.png")
    label1 = Label(top, image = bg)
    label1.pack()
    #print(lst)
    useful=[]
    combo_box = ttk.Combobox(top,height=20, width=80)
    combo_box['values'] = lst
    combo_box.bind('<KeyRelease>', check_input)
    combo_box.place(x=500, y=125)
    Map = Button(top, text="Extract Load", height=1, width=30,command=partial(MapExtractor,combo_box,LoadNames,True))
    Map.place(x=500, y=400)
    Map2 = Button(top, text="Extract Map (No Dyn)", height=1, width=30,command=partial(MapExtractor,combo_box,LoadNames,False))
    Map2.place(x=500, y=350)
    Back = Button(top, text="Back", height=1, width=15,command=partial(MainWindow,top))
    Back.place(x=10, y=10)
    Clear = Button(top, text="Clear Audio", height=1, width=15,command=partial(ClearAudio,top))
    Clear.place(x=1000, y=550)
    #ClearOut = Button(top, text="Clear Out", height=1, width=15,command=partial(ClearDir,top))
    #ClearOut.place(x=1000, y=510)
    ClearTex = Button(top, text="Clear Textures", height=1, width=15,command=partial(ClearTextures,top))
    ClearTex.place(x=1000, y=470)
    ClearMap = Button(top, text="Clear Maps", height=1, width=15,command=partial(ClearMaps,top))
    ClearMap.place(x=1000, y=430)

    top.mainloop()



def MapExtractor(entry,LoadNames,Dyns):
    things=entry.get().split(" ")
    count=0
    for Load in LoadNames:
        if Load[2] in things:
            answer=count
        count+=1
            
    lengths=[]
    Rotations=[]
    Translations=[]
    DynamicHashes=[]        
    SubLoads=LoadNames[answer][3:]
    count5=1
    LoadFiles=[]
    print(SubLoads)
    InstCount=[]
    count3=0
    Dts=[]
    refs=[]
    for SubLoad in SubLoads:
        num=ast.literal_eval(SubLoad)
        EntityDts=[]
        print("SUB")
        Name=Hex_String(Package_ID(num))+"-"+Hex_String(Entry_ID(num))+".lhash"
        save=Name
        for File in os.listdir(custom_direc):
            if File != "Statics":
                if File.lower() == Name:  #change back to LHash
                    Tables=[]
                    file=open(custom_direc+"/"+File,"rb")
                    file.seek(0x50)
                    dat=binascii.hexlify(bytes(file.read())).decode()
                    Data=[dat[i:i+8] for i in range(0, len(dat), 8)]
                    for Hash in Data:
                        flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8')
                        num=ast.literal_eval("0x"+flipped)
                        Name=Hex_String(Package_ID(num))+"-"+Hex_String(Entry_ID(num))
                        if Name not in Tables:
                            Tables.append(Name)
                    count=0
                    
                    for Table in Tables:
                        for File in os.listdir(custom_direc):
                            if File != "audio":
                                if Table.lower() == File.split(".")[0].lower():   #opens multiple dts
                                    #print(File)
                                    tempName=File
                                    EntityDts.append(str(File))
                                    #print(EntityDts)
                                    H64=""
                                    StaticLz=""
                                    file=open(custom_direc+"/"+File,"rb")
                                    length=binascii.hexlify(bytes(file.read())).decode()
                                    file.close()
                                    if len(length) < 144:
                                        continue
                                    File=open(custom_direc+"/"+File,"rb")
                                    File.seek(0x20)
                                    Num=binascii.hexlify(bytes(File.read(8))).decode()
                                    flipped=binascii.hexlify(bytes(hex_to_little_endian(Num))).decode('utf-8')
                                    Length=ast.literal_eval("0x"+stripZeros(flipped))
                                    File.seek(0x30)
                                    #Data=binascii.hexlify(bytes(File.read(288*int(Length)))).decode()
                                    dat=[]
                                    count=0
                                    
                                    for i in range(Length):
                                        count+=1
                                        temp=binascii.hexlify(bytes(File.read(144))).decode()
                                        dat.append(temp)
                                        #print(temp)
                                        EntityDts=[]
                                    for Model in dat:
                                        Dat=[Model[i:i+8] for i in range(0, len(Model), 8)]
                                        #print(Dat)
                                        QuatX=(struct.unpack("<I", bytes.fromhex(Dat[0]))[0])*-1
                                        QuatY=(struct.unpack("<I", bytes.fromhex(Dat[1]))[0])*-1
                                        QuatZ=(struct.unpack("<I", bytes.fromhex(Dat[2]))[0])*-1
                                        QuatW=struct.unpack("<I", bytes.fromhex(Dat[3]))[0]
                                        fx=struct.unpack("<I", bytes.fromhex(Dat[4]))[0]
                                        fy=struct.unpack("<I", bytes.fromhex(Dat[5]))[0]
                                        fz=struct.unpack("<I", bytes.fromhex(Dat[6]))[0]
                                        lzscale=struct.unpack("<I", bytes.fromhex(Dat[7]))[0]
                                        Rotations.append([QuatX,QuatY,QuatZ,QuatW])
                                        Translations.append([fx,fy,fz,lzscale])
                                        File.read(4)
                                        Ref=binascii.hexlify(bytes(File.read(4))).decode()
                                        if Ref == "c96c8080":  #statics
                                            print("THISONE")
                                            File.read(16)
                                            Hash=binascii.hexlify(bytes(File.read(4))).decode()
                                            File.close()
                                            flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8')
                                            new=ast.literal_eval("0x"+flipped)
                                            DirName=Hex_String(Package_ID(new))+"-"+Hex_String(Entry_ID(new))
                                            #print(DirName+".test")
                                            File=open(custom_direc+"/"+DirName+".test","rb")
                                            File.seek(0x8)
                                            Hash=binascii.hexlify(bytes(File.read(4))).decode()
                                            #print(Hash)
                                            flipped=binascii.hexlify(bytes(hex_to_little_endian(Hash))).decode('utf-8')
                                            new=ast.literal_eval("0x"+flipped)
                                            DirName2=Hex_String(Package_ID(new))+"-"+Hex_String(Entry_ID(new))+".load"
                                            #print(DirName)
                                            File.close()
                                            #print(DirName2)
                                            File=open(custom_direc+"/"+DirName2,"rb")
                                            File.seek(0x50)
                                            Length=binascii.hexlify(bytes(File.read(2))).decode()
                                            File.close()
                                            flipped=binascii.hexlify(bytes(hex_to_little_endian(Length))).decode('utf-8')
                                            new=ast.literal_eval("0x"+stripZeros(flipped))
                                            print(str(count5)+" "+str(SubLoad)+" Instances: "+str(new))
                                            InstCount.append(str(new))
                                            count5+=1
                                            LoadFiles.append(DirName2)
                                            refs.append(save)
                                        
                                        
                                   
                
        
        #print(Dts)
                                            
    print(refs)                                   
    #print(LoadFiles)                                       
    #ans2=int(input("Enter which Load to extract from: "))
    InitialiseMapFiles(LoadFiles,InstCount,refs,Dyns)
def InitialiseMapFiles(loadfile,InstCount,Ref,Dyns):
    lengths=[]
    count=0
    if Dyns == True:
        PullMechanicStructs()
    for Load in loadfile:
        for File in os.listdir(custom_direc):
            if File != "audio":
                if File.lower() == Load:
                    Load=LoadZone(Load,InstCount[count],Ref[count])
                    lengths.append([File,str(len(Load.Statics))])
                    count+=1
    Popup()
def PullMechanicStructs():
    DynNames=[]
    H64Sort=SortH64(ReadHash64())
    for file in os.listdir(os.getcwd()+"/out"):
        if file == "audio":
            continue
        if file.split(".")[1] == "dt":
            Test=open(os.getcwd()+"/out/"+file,"rb")
            Test.seek(0x60)
            hcheck=binascii.hexlify(bytes(Test.read(8))).decode()
            flipped=binascii.hexlify(bytes(hex_to_little_endian(hcheck))).decode('utf-8')
            try:
                num=ast.literal_eval("0x"+flipped)
            except SyntaxError:
                Test.close()
                continue
            Check=Hash64Search2(H64Sort,num)
            
            if Check != False:
                flipped=binascii.hexlify(bytes(hex_to_little_endian(Check[1][2:]))).decode('utf-8')
                Exists=os.path.isfile(os.getcwd()+"/data/Dynamics/"+flipped+".fbx")
                if Exists != True:
                    if DynNames != []:
                        index=binary_search_single(sorted(DynNames),int(ast.literal_eval("0x"+Check[1][2:])))
                    else:
                        index=-1
                    if index == -1:
                        PullDyn(str(flipped))
                        DynNames.append(int(ast.literal_eval("0x"+flipped)))
                Exists=os.path.isfile(os.getcwd()+"/data/Dynamics/"+flipped+".fbx")
                file1=open(os.getcwd()+"/data/Instances/"+flipped.lower()+".inst","a")
                Test.seek(0x30)
                rotX=binascii.hexlify(bytes(hex_to_little_endian(binascii.hexlify(bytes(Test.read(4))).decode()))).decode('utf-8')
                rotY=binascii.hexlify(bytes(hex_to_little_endian(binascii.hexlify(bytes(Test.read(4))).decode()))).decode('utf-8')
                rotZ=binascii.hexlify(bytes(hex_to_little_endian(binascii.hexlify(bytes(Test.read(4))).decode()))).decode('utf-8')
                rotW=binascii.hexlify(bytes(hex_to_little_endian(binascii.hexlify(bytes(Test.read(4))).decode()))).decode('utf-8')
                PosX=binascii.hexlify(bytes(hex_to_little_endian(binascii.hexlify(bytes(Test.read(4))).decode()))).decode('utf-8')
                PosY=binascii.hexlify(bytes(hex_to_little_endian(binascii.hexlify(bytes(Test.read(4))).decode()))).decode('utf-8')
                PosZ=binascii.hexlify(bytes(hex_to_little_endian(binascii.hexlify(bytes(Test.read(4))).decode()))).decode('utf-8')
                ScaleX=binascii.hexlify(bytes(hex_to_little_endian(binascii.hexlify(bytes(Test.read(4))).decode()))).decode('utf-8')
                #print(PosX)
                if PosX != "00000000":
                    PosX=struct.unpack('!f', bytes.fromhex(PosX))[0]
                else:
                    PosX=0
                if PosY != "00000000":
                    PosY=struct.unpack('!f', bytes.fromhex(PosY))[0]
                else:
                    PosY=0
                if PosZ != "00000000":
                    PosZ=struct.unpack('!f', bytes.fromhex(PosZ))[0]
                else:
                    PosZ=0
                if rotX != "00000000":
                    rotX=struct.unpack('!f', bytes.fromhex(rotX))[0]
                else:
                    rotX=0
                if rotY != "00000000":
                    rotY=struct.unpack('!f', bytes.fromhex(rotY))[0]
                else:
                    rotY=0
                if rotZ != "00000000":
                    rotZ=struct.unpack('!f', bytes.fromhex(rotZ))[0]
                else:
                    rotZ=0
                if rotW != "00000000":
                    rotW=struct.unpack('!f', bytes.fromhex(rotW))[0]
                else:
                    rotW=0
               
                
                if ScaleX != "00000000":
                    ScaleX=struct.unpack('!f', bytes.fromhex(ScaleX))[0]
                else:
                    ScaleX=1
            
                file1.write(str(rotX)+","+str(rotY)+","+str(rotZ)+","+str(rotW)+","+str(PosX)+","+str(PosY)+","+str(PosZ)+","+str(ScaleX)+"\n")
                file1.close()
            Test.close()
def PullDyn(Hash):
    print("Start "+Hash)
    CWD=os.getcwd()
    os.chdir(CWD+"/ThirdParty")
    if os.path.isfile(CWD+'/data/Dynamics/'+Hash+'.fbx') != True:
        
        cmd='MDE -p "'+path+'" -o "'+CWD+'/data/Dynamics" -i '+Hash+' -t'
        #print(cmd)
        ans=subprocess.call(cmd, shell=True)
        try:
            os.listdir(CWD+"/data/Dynamics/"+Hash+"/Textures")
        except FileNotFoundError:
            u=1
        else:
            for File in os.listdir(CWD+"/data/Dynamics/"+Hash+"/Textures"):
                print(File)
                if File.split(".")[1] == "png":
                   
                    shutil.move(CWD+"/data/Dynamics/"+Hash+"/Textures/"+File,CWD+"/data/Textures/"+File)
                    #print("ran")
                elif File.split(".")[1] == "txt":
                    shutil.move(CWD+"/data/Dynamics/"+Hash+"/Textures/"+File,CWD+"/data/DynMaterials/"+Hash+".txt")
            os.rmdir(CWD+"/data/Dynamics/"+Hash+"/Textures")
                
        try:
            os.listdir(CWD+"/data/Dynamics/"+Hash+"/unk_textures")
        except FileNotFoundError:
            u=1
        else:
            for File in os.listdir(CWD+"/data/Dynamics/"+Hash+"/unk_textures"):
                os.remove(CWD+"/data/Dynamics/"+Hash+"/unk_textures/"+File)
            os.rmdir(CWD+"/data/Dynamics/"+Hash+"/unk_textures")
                
                        
        try:
            shutil.move(CWD+"/data/Dynamics/"+Hash+"/"+Hash+".fbx",CWD+"/data/Dynamics/"+Hash+".fbx")
        except FileNotFoundError:
            u=1
        else:
            os.rmdir(CWD+"/data/Dynamics/"+Hash)
    print("End "+Hash)
    os.chdir(CWD)
def MapRipper(entry,top,skip):
    
    filelist=[]
    package=""
    ActId=""
    ActName=entry.get()
    File2=open(os.getcwd()+"/cache/ActivityHashes.txt","r")
    data=File2.read()
    File2.close()
    Activities=data.split("\n")
    for Act in Activities:
        temp=Act.split(" : ")
        if entry.get() in temp:
            package=temp[2]
            ActId=temp[0]
            print("found")
            break
    for file in os.listdir(path)[::-1]:
        if fnmatch.fnmatch(file,package+"*"):
            filelist.append(file)
    useful=["Map","0x808093ad","0x80806d44","0x80806c81","0x80809ed2","0x80806daa","0x80806d30","0x80808707","0x80809883","0x8080891e","0x80808701","0x808093b1","0x80806a0d","0x80808e8e","0x80806daa"]
    if skip == False:
        unpack_all(path,custom_direc,useful,filelist)
    LoadNames(top,ActId,ActName)
def QuitOut(top):
    top.destroy()
    sys.exit()
def MapWindow(top):
    global lst, combo_box
    lst=[]
    file=open(os.getcwd()+"/cache/ActivityHashes.txt","r")
    data=file.read()
    file.close()
    ActDat=data.split("\n")
    ActDat.remove("")
    for Act in ActDat:
        #print(Act)
        things=Act.split(" : ")
        lst.append(things[1])
    for widget in top.winfo_children():
        widget.destroy()
    lst.sort(reverse=False)
    bg = PhotoImage(file = os.getcwd()+"/ThirdParty/destiny.png")
    label1 = Label(top, image = bg)
    label1.pack()
    #print(lst)
    useful=[]
    combo_box = ttk.Combobox(top,height=20, width=40)
    combo_box['values'] = lst
    combo_box.bind('<KeyRelease>', check_input)
    combo_box.place(x=500, y=125)
    Map = Button(top, text="Extract Map", height=1, width=30,command=partial(MapRipper,combo_box,top,False))
    Map.place(x=500, y=175)
    
    Map2 = Button(top, text="Extract Map(no ext)", height=1, width=30,command=partial(MapRipper,combo_box,top,True))
    Map2.place(x=800, y=175)
    Back = Button(top, text="Back", height=1, width=15,command=partial(MainWindow,top))
    Back.place(x=10, y=10)
    ClearMap = Button(top, text="Clear Maps", height=1, width=15,command=partial(ClearMaps,top))
    ClearMap.place(x=1000, y=430)
    top.mainloop()
def ClearScripts(top):
    for file in os.listdir(os.getcwd()+"/Scripts"):
        os.remove(os.getcwd()+"/Scripts/"+file)
    Popup()
def MainWindow(top):
    for widget in top.winfo_children():
        widget.destroy()
    bg = PhotoImage(file = os.getcwd()+"/ThirdParty/destiny.png")
    label1 = Label(top, image = bg)
    label1.pack()
    String = Button(top, text="Generate String DB", height=1, width=15,command=partial(Strings,"y"))
    String.place(x=500, y=125)
    ActName = Button(top, text="Generate Activity DB", height=1, width=15,command=partial(GenerateActivityNames))
    ActName.place(x=700, y=175)
    String2 = Button(top, text="No Ext (Debug)", height=1, width=15,command=partial(Strings,"n"))
    String2.place(x=700, y=125)
    Activity = Button(top, text="Extract Activity Data", height=1, width=15,command=partial(ActivityMenu,top))
    Activity.place(x=500, y=175)
    Map = Button(top, text="Map Extractor", height=1, width=15,command=partial(MapWindow,top))
    Map.place(x=500, y=225)
    #Map["state"] = DISABLED
    Texture = Button(top, text="Texture Ripper", height=1, width=15,command=partial(TextureWindow,top))
    Texture.place(x=500, y=275)
    #Texture["state"] = DISABLED
    Cutscene = Button(top, text="Cutscene Extractor", height=1, width=15,command=partial(CutsceneView,top))
    Cutscene.place(x=500, y=325)
    Dev = Button(top, text="Script Extractor", height=1, width=15,command=partial(DevMenu))
    Dev.place(x=500, y=375)
    Clear = Button(top, text="Clear Audio", height=1, width=15,command=partial(ClearAudio,top))
    Clear.place(x=1000, y=550)
    ClearOut = Button(top, text="Clear Out", height=1, width=15,command=partial(ClearDir,top))
    ClearOut.place(x=1000, y=510)
    ClearTex = Button(top, text="Clear Textures", height=1, width=15,command=partial(ClearTextures,top))
    ClearTex.place(x=1000, y=470)
    ClearMap = Button(top, text="Clear Maps", height=1, width=15,command=partial(ClearMaps,top))
    ClearMap.place(x=1000, y=430)
    ClearScript = Button(top, text="Clear Scripts", height=1, width=15,command=partial(ClearScripts,top))
    ClearScript.place(x=1000, y=390)
    Quit = Button(top, text="Quit", height=1, width=15,command=partial(QuitOut,top))
    Quit.place(x=100, y=510)
    
    top.mainloop()
    
if __name__ == '__main__':
    
    top = Tk()
    top.title("The Tech")
    top.geometry("1200x600")
    bg = PhotoImage(file = os.getcwd()+"/ThirdParty/destiny.png")
    label1 = Label(top, image = bg)
    label1.pack()
    entry1 = Entry(top)
    entry1.place(x=500,y=105)
    turn_on = Button(top, text="Set D2 Location", height=1, width=12,command=partial(setD2Location, entry1,top))
    turn_on.place(x=500, y=125)
    try:
        os.makedirs(os.getcwd()+"/Cutscenes")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/Activity")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/out")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/out/audio")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/Textures")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/Textures/cubemaps")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/cache")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/data/Statics")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/data/Instances")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/data/Materials")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/data/Dynamics")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/data/Entities")
    except FileExistsError:
        print("Drive Exists")
    try:
        os.makedirs(os.getcwd()+"/Scripts")
    except FileExistsError:
        print("Drive Exists")
    Hash64(path)
    Hash64Data=ReadHash64()
    
    
    
    
    
    #turn_on.pack()

    top.mainloop()
    

    