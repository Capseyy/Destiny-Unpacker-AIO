import bpy
import json
import mathutils
import os
import binascii
import ast
import math
import struct
#!!!DO NOT MANUALLY IMPORT THE FBX, THE SCRIPT WILL DO IT FOR YOU!!!

#Adapted from Monteven's UE5 import script
def stripZeros(txt):
    if txt == "0000":
        return("0")
    elif txt == "00000000":
        return("0")
    elif txt == "0000000000000000":
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
def euler_from_quaternion(x, y, z, w):
    if 1 == 1:
        """
        Convert a quaternion into euler angles (roll, pitch, yaw)
        roll is rotation around x in radians (counterclockwise)
        pitch is rotation around y in radians (counterclockwise)
        yaw is rotation around z in radians (counterclockwise)
        """
        t0 = +2.0 * (w * x + y * z)
        t1 = +1.0 - 2.0 * (x * x + y * y)
        roll_x = math.atan2(t0, t1)
     
        t2 = +2.0 * (w * y - z * x)
        t2 = +1.0 if t2 > +1.0 else t2
        t2 = -1.0 if t2 < -1.0 else t2
        pitch_y = math.asin(t2)
     
        t3 = +2.0 * (w * z + x * y)
        t4 = +1.0 - 2.0 * (y * y + z * z)
        yaw_z = math.atan2(t3, t4)
     
        return roll_x, pitch_y, yaw_z # in radians
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
#installLoc="C:/Users/sjcap/Desktop/MyUnpacker/DestinyUnpackerNew/new/GUI/"
Filepath = os.path.abspath(bpy.context.space_data.text.filepath+"/..") #"OUTPUT_DIR"
def InstanceDyn(ObjectData,NameData,SortedIDs,EnemyData,AltData,AltDataReverse,AltDataNorm):
    InstancedWIDs=[]
    for EntityData in ObjectData:
        #print(HasRoot)
        try:
            file=open(Filepath+"/Instances/"+EntityData[0]+".inst","r")
        except FileNotFoundError:
            continue
        else:
        
            print(EntityData[0])#  
            data=file.read().split("\n")#
            file.close()
            #print(data)
            try:
                data.remove('')
            except ValueError:
                u=1
            #print(data)
                         
            #flipped=binascii.hexlify(bytes(hex_to_little_endian(Object.name[:8]))).decode('utf-8')
    #print(flipped)
            
            for instance in data:
                instance=instance.split(",")
                if len(instance) < 3:
                    continue
                for Object,HasRoot in EntityData[1]:
                   
                    ob_copy = bpy.data.objects[Object.name].copy()
                    bpy.context.collection.objects.link(ob_copy) #makes the instances
                    try:
                        instance[7]
                    except IndexError:
                        continue
                    location = [float(instance[4]), float(instance[5]), float(instance[6])]
                    #Reminder that blender uses WXYZ, the order in the confing file is XYZW, so W is always first
                    quat = mathutils.Quaternion([float(instance[3]), float(instance[0]), float(instance[1]), float(instance[2])])
                    #x,y,z=euler_from_quaternion(float(instance[0]),float(instance[1]),float(instance[2]),float(instance[3])) 
                    ob_copy.location = location
                    if EntityData[2] == True:
                        x,y,z=euler_from_quaternion(float(instance[0]),float(instance[1]),float(instance[2]),float(instance[3]))

                        
                        x=x+1.5708
                        if x > 1.57079632679:
                            x=1.57079632679-(x-1.57079632679)
                        elif x < 1.57079632679:
                            x=1.57079632679+(1.57079632679-x)
                        ob_copy.rotation_euler= (x,y*-1,z+3.1415)
                    else:
                        ob_copy.rotation_mode = 'QUATERNION'
                        ob_copy.rotation_quaternion = quat
                    #ob_copy.location = location
                    #ob_copy.rotation_mode = 'QUATERNION'
                    if HasRoot == True:
                        ob_copy.delta_scale=[0.01]*3
                    #if 7<Scale<8:
                    
                        #ob_copy.delta_scale=([Scale/10])*3
                    ob_copy.scale = [float(instance[7])]*3
                try:
                    instance[8]
                except IndexError:
                    continue
                if instance[8] != "ffffffffffffffff":
                    NamesToAdd=[]
                    holder=instance[8].split(":")
                    for Entry in holder:
                        print(Entry)
                        #print(int(ast.literal_eval("0x"+stripZeros(Entry))))
                        #print(AltData)
                        Index=binary_search2(SortedIDs,int(ast.literal_eval("0x"+stripZeros(Entry))))
                        if Index != -1:
                            
                            NamesToAdd.append(str(SortedIDs[Index][1]))
                        Index=binary_search2(AltData,int(ast.literal_eval("0x"+stripZeros(Entry))))
                        if Index != -1:
                            Link=AltData[Index][1]
                            Index=binary_search2(SortedIDs,int(ast.literal_eval("0x"+stripZeros(Link))))
                            if Index != -1:
                                NamesToAdd.append(str(SortedIDs[Index][1]))
                        print(ast.literal_eval("0x"+Entry))
                        InstancedWIDs.append([ast.literal_eval("0x"+Entry),location,quat,Object])
                    NameTo="-".join(NamesToAdd) 
                    bpy.ops.object.text_add()
                    ob=bpy.context.object
                    ob.data.body = str(NameTo)
                    ob.name = str(Object.name)
                    ob.location= location
                    ob.rotation_mode = 'QUATERNION'
                    ob.rotation_quaternion = quat
                    ob.scale = [float(instance[7])]*3
                try:
                    instance[9]
                except IndexError:
                    continue
                else:
                    print(instance[9])
                    try:
                        test=int(ast.literal_eval("0x"+stripZeros(instance[9])))
                    except SyntaxError:
                        u=1
                    else:
                        Index=binary_search2(EnemyData,test)
                        if Index != -1:
                            bpy.ops.object.text_add()
                            ob=bpy.context.object
                            ob.data.body = str(EnemyData[Index][1])
                            ob.name = str(Object.name)
                            ob.location= location
                            ob.rotation_mode = 'QUATERNION'
                            ob.rotation_quaternion = quat
                            ob.scale = [float(instance[7])]*3
                try:
                    instance[10]
                except IndexError:
                    continue
                else:
                    bpy.ops.object.text_add()
                    ob=bpy.context.object
                    ob.data.body = str(instance[10])
                    ob.name = str(Object.name)
                    #location=[float(instance[4]), float(instance[5]), float(instance[6])-0.5]
                    ob.location= location
                    ob.rotation_mode = 'QUATERNION'
                    ob.rotation_quaternion = quat
                    ob.scale = [float(instance[7])]*3
    InstancedWIDs.sort(key=lambda x: x[0])     
    print(InstancedWIDs) 
    bpy.ops.object.select_all(action='DESELECT')
    for Obj in bpy.data.objects:
        if Obj.name[:4] == "root":
            Obj.select_set(state=True)
    bpy.ops.object.delete()
    bpy.ops.object.select_all(action='DESELECT')
    for Val in AltDataNorm:
        print(ast.literal_eval("0x"+Val[1]))
        Index1=binary_search2(InstancedWIDs,int(ast.literal_eval("0x"+Val[1])))
        if Index1 != -1:
            print("found1")
            Index2=binary_search2(InstancedWIDs,ast.literal_eval("0x"+Val[0]))
            if Index2 != -1:
                print("found2")
                ObjectToCopy=InstancedWIDs[Index1][3]
                print(ObjectToCopy.name)
                
                path2=Filepath+"/Dynamics/"+ObjectToCopy.name[:8]+".fbx"
                print(path2)
                bpy.ops.import_scene.fbx(filepath=path2, use_custom_normals=True, ignore_leaf_bones=True, automatic_bone_orientation=True)
                for obj in bpy.context.selected_objects:
                    print(obj.name)
                    ob_copy = bpy.data.objects[obj.name].copy()
                    bpy.context.collection.objects.link(ob_copy) #makes the instances
                    ob_copy.location=InstancedWIDs[Index2][1]
                    ob_copy.rotation_mode = 'QUATERNION'
                    ob_copy.rotation_quaternion = InstancedWIDs[Index2][2]
                    ob_copy.scale = [float(1)]*3

            #count=0
def Material(Obj):
    try:
        file=open(Filepath+"/Materials/"+Obj.name[:8]+".txt","r")
    except FileNotFoundError:
        u=1
    else:
        data=file.read()
        data=data.split("\n")
        for Line in data:
            temp=Line.split(" : ")
            if Obj.name.lower() == temp[0].lower():
                try:
                    temp[2]
                except IndexError:
                    continue
                else:
                    MaterialsToAdd=list(temp[2])
                    while " " in MaterialsToAdd:
                        MaterialsToAdd.remove(" ")
                    #print(MaterialsToAdd)
                    MaterialsToAdd="".join(MaterialsToAdd)
                    MaterialList=MaterialsToAdd.split(",")
                    mat_name = temp[1]
                    mat = (bpy.data.materials.get(mat_name) or   bpy.data.materials.new(mat_name))
                    mat.use_nodes = True
                    nodes = mat.node_tree.nodes
                    bsdf = mat.node_tree.nodes["Principled BSDF"]
                    for Texture in MaterialList:
                        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
                        #print(Texture)
                        try:
                            texImage.image = bpy.data.images.load(Filepath+"/Textures/"+Texture+".png")
                        except RuntimeError:
                            continue
                        mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
                    try:
                        Obj.data.materials.append(mat)
                    except AttributeError:
                        u=1
ObjectData=[] 
        
file=open(Filepath+"/EntityBulk.txt","r")
data=file.read().split("\n")
data.remove("")
used=[]
SortedIDs=[]
EnemyNames=[]
for Line in data:
    temp=Line.split(" : ")
    #print(Line)
    SortedIDs.append([int(ast.literal_eval("0x"+stripZeros(temp[1]))),temp[2]])
    EnemyNames.append([int(ast.literal_eval("0x"+stripZeros(temp[0]))),temp[2]])
SortedIDs.sort(key=lambda x: x[0])
EnemyNames.sort(key=lambda x: x[0])
file.close()
NameData=[]
file=open(Filepath+"/NamedEntities.txt","r").read()
data=file.split("\n")
data.remove("")
for Line in data:
    temp=Line.split(" : ")
    if temp[0] == "":
        continue
    Val=ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(temp[0]))).decode('utf-8')))
    NameData.append([int(Val),temp[1]])
NameData.sort(key=lambda x: x[0])
file=open(Filepath+"/AltMapping.txt","r").read()
data=file.split("\n")
data.remove("")
AltData=[]
AltDataReverse=[]
AltDataNorm=[]
for Line in data:
    temp=Line.split(" : ")
    if temp[0] == "":
        continue
    Val=ast.literal_eval("0x"+stripZeros(temp[0]))
    Val2=ast.literal_eval("0x"+stripZeros(temp[1]))
    AltData.append([int(Val),temp[1]])
    AltDataReverse.append([int(Val2),temp[0]])
    AltDataNorm.append([temp[0],temp[1]])
AltData.sort(key=lambda x: x[0])    
AltDataReverse.sort(key=lambda x: x[0])  
                                                 
for Fbx in os.listdir(Filepath+"/Instances"):
    split=Fbx.split(".")
    #if split[0] != "3029a680":
       # continue
    Havok=False
    ans=os.path.isfile(Filepath+"/Dynamics/"+split[0]+".fbx")
    ans2=os.path.isfile(Filepath+"/Havok/"+split[0]+".obj")
    print(ans)
    bpy.ops.object.select_all(action='DESELECT')
    AddedObjs=[]
    if (ans == True) or (ans2 == True):
        print("running")
        try:
            split[1]
        except IndexError:
            continue
        if 1==1:
            #print(count)
            print(Fbx)
            path=Filepath+"/Dynamics/"+split[0]+".fbx"
            path2=Filepath+"/Havok/"+split[0]+".obj"
            print("ran")
            bpy.ops.object.select_all(action='DESELECT')
            thing=(0,0,0)
            bpy.context.scene.cursor.rotation_euler = (0, 0, 0)
            bpy.data.collections.new(str(split[0]).upper())
            bpy.context.scene.collection.children.link(bpy.data.collections[str(split[0]).upper()])
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[str(split[0]).upper()]
            if ans2 == True:
                bpy.ops.import_scene.obj(filepath=path2)
            else:
                try:
                    bpy.ops.import_scene.fbx(filepath=path, use_custom_normals=True, ignore_leaf_bones=True, automatic_bone_orientation=True)
                except RuntimeError:
                    continue
            HasRoot=False
            if ans == True:
                Havok=False
            elif ans2 == True:
                Havok=True
            #bpy.ops.object.select_all(action='DESELECT')
            newobjects = bpy.data.collections[str(split[0]).upper()].objects
            Keep=[]
            #bpy.ops.outliner.orphans_purge()
            for Obj in newobjects:
                if Obj.name[:4] == "root":
                    #Obj.parent = None
                    Obj.select_set(state=True)
                    print("found")
                    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                    HasRoot=True
               
                    #bpy.context.view_layer.objects.active = bpy.context.selected_objects
            #MSH_OBJS = [m for m in bpy.data.collections[str(split[0]).upper()].objects if m.type == 'MESH']
            bpy.ops.outliner.orphans_purge()
            for OBJS in newobjects:
                #Select all mesh objects
                OBJS.parent = None
                OBJS.select_set(state=True)
                bpy.context.view_layer.objects.active = OBJS
                bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
                Material(OBJS)
                AddedObjs.append([OBJS,HasRoot])
            #bpy.ops.object.join()

           
            modelExists=True
            if modelExists == True:
                #count+=1
                for obj in bpy.context.selected_objects:
                    
                    obj.location=[0,0,0]
                    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                    AddedObjs.append([obj,HasRoot])
                    Index=binary_search2(NameData,int(ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(str(split[0])))).decode('utf-8')))))
                    if Index != -1:
            #Object.name=NameData[Index][1]
                        bpy.ops.object.text_add()
                        ob=bpy.context.object
                        ob.data.body = str(NameData[Index][1])
                        ob.name = str(split[0])
                        AddedObjs.append([ob,False])
    else:
        if str(split[0]) == "NonEntity":
            Index=-1
        else:
            Index=binary_search2(NameData,int(ast.literal_eval("0x"+stripZeros(binascii.hexlify(bytes(hex_to_little_endian(str(split[0])))).decode('utf-8')))))
        if Index != -1:
            #Object.name=NameData[Index][1]
            bpy.ops.object.text_add()
            ob=bpy.context.object
            ob.data.body = str(NameData[Index][1])
            ob.name = str(split[0])
            AddedObjs.append([ob,False])
        else:
            bpy.ops.object.text_add()
            ob=bpy.context.object
            ob.name = str(split[0])
            ob.data.body = str("")
            AddedObjs.append([ob,False])
        
        #File=open(Filepath+"/DynInstances/"+Fbx,"r")
        #Data=File.read().split("\n")
        #Data.remove("")
        #for Line in Data:
        #    instance=Line.split(",")
        #    if instance[8] != "ffffffffffffffff":
        #        Index=binary_search2(SortedIDs,int(ast.literal_eval("0x"+stripZeros(instance[8]))))
        #        if Index != -1:
        #            bpy.ops.object.text_add()
        #            ob=bpy.context.object
        #            ob.data.body = str(SortedIDs[Index][1])
        #            ob.name = str(split[0])
        #            ObjectData.append([ob,False])
        #File.close()
    ObjectData.append([split[0],AddedObjs,Havok])    


#        
#for Line in used:
#    split=Line.split(" : ")
#    bpy.ops.object.text_add()
#    ob=bpy.context.object
#    ob.data.body = str(split[1])
#    ob.name = str(split[0])
#    ObjectData.append([ob,False])
    
InstanceDyn(ObjectData,NameData,SortedIDs,EnemyNames,AltData,AltDataReverse,AltDataNorm)
        
