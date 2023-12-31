import bpy
import json
import mathutils
import os
import binascii
import ast
import math
import struct
#!!!DO NOT MANUALLY IMPORT THE FBX, THE SCRIPT WILL DO IT FOR YOU!!!#

#Adapted from Monteven's UE5 import script
#installLoc="C:/Users/sjcap/Desktop/MyUnpacker/DestinyUnpackerNew/new/GUI/"
Filepath = os.path.abspath(bpy.context.space_data.text.filepath+"/..") #"OUTPUT_DIR"

objects = bpy.data.objects
scene = bpy.context.scene
Type = "Map"
Name = "Terrain"
def Is_Map():
    if "Map" in Type:
        return True
    if "Terrain" in Type:
        return True
    else:
        return False
def hex_to_little_endian(hex_string):
    little_endian_hex = bytearray.fromhex(hex_string)[::-1]
    return little_endian_hex
def cleanup():
    print(f"Cleaning up...")
    #Delete all the objects in static_names
    #if Is_Map():
    #    for name in static_names.values():
    #        bpy.data.objects.remove(bpy.data.objects[name[0]])
        
    #Removes unused data such as duplicate images, materials, etc.
    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)

    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)

    for block in bpy.data.textures:
        if block.users == 0:
            bpy.data.textures.remove(block)

    for block in bpy.data.images:
        if block.users == 0:
            bpy.data.images.remove(block)
    print("Done cleaning up!")
def add_to_collection():
    # List of object references
    objs = bpy.context.selected_objects
    # Set target collection to a known collection 
    coll_target = bpy.context.scene.collection.children.get(str(Name))
    # If target found and object list not empty
    if coll_target and objs:
        # Loop through all objects
        for ob in objs:
            # Loop through all collections the obj is linked to
            for coll in ob.users_collection:
                # Unlink the object
                coll.objects.unlink(ob)
            # Link each object to the target collection
            coll_target.objects.link(ob)

        
def assemble_map():
    print(f"Starting import on {Type}: {Name}")
    
    #make a collection with the name of the imported fbx for the objects
    bpy.data.collections.new(str(Name))
    bpy.context.scene.collection.children.link(bpy.data.collections[str(Name)])
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[str(Name)]

    #bpy.ops.import_scene.fbx(filepath=FileName, use_custom_normals=True, ignore_leaf_bones=True, automatic_bone_orientation=True) #Just imports the fbx, no special settings needed
    
    #assign_materials()
    #add_to_collection() 
    bpy.ops.object.select_all(action='DESELECT')
    for Obj in bpy.data.objects:
        if len(Obj.data.materials) == 0:
            Obj.select_set(state=True)
            #bpy.data.objects.remove(Obj)
    newobjects = bpy.data.collections[str(Name)].objects
    objects = bpy.data.objects
    for O in objects:
        print(str(O.name)[:8])
    #print(newobjects)
    print(f"Imported {Type}: {Name}")
    
    #Merge statics, create instances for maps only
    if Is_Map():
        print("Merging Map Statics... ")
        tmp = []
        bpy.ops.object.select_all(action='DESELECT')
     


        newobjects = [] #Clears the list just in case
        newobjects = bpy.data.collections[str(Name)].objects #Readds the objects in the collection to the list

        print("Instancing...")
        
        for Object in bpy.data.objects:
            try:
                file=open(Filepath+"/Instances/"+(str(Object.name)[:8]).lower()+".inst","r")
            except:
                print("no file")
            else:
                
                data=file.read().split("\n")
                file.close()
                #print(data)
                #data.remove('')
                #print(data)
                print(Object.name)               
                flipped=binascii.hexlify(bytes(hex_to_little_endian(Object.name[:8]))).decode('utf-8')

                for instance in data:
                    instance=instance.split(",")
                    ob_copy = bpy.data.objects[Object.name].copy()
                    bpy.context.collection.objects.link(ob_copy) #makes the instances

                    location = [float(instance[4]), float(instance[5]), float(instance[6])]
                    #Reminder that blender uses WXYZ, the order in the confing file is XYZW, so W is always first
                    quat = mathutils.Quaternion([1, float(instance[0]), float(instance[1]), float(instance[2])])
                
                    ob_copy.location = location
                    ob_copy.rotation_mode = 'QUATERNION'
                    ob_copy.rotation_quaternion = quat
                    #if 7<Scale<8:
                    
                        #ob_copy.delta_scale=([Scale/10])*3
                    ob_copy.scale = [float(instance[7])]*3



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


for Fbx in os.listdir(Filepath+"/Terrain"):
    #if Fbx != "8321ba80.fbx":
    #continue
    split=Fbx.split(".")
    if split[1] == "fbx":
        path=Filepath+"/Terrain/"+Fbx
        print("ran")
        bpy.ops.object.select_all(action='DESELECT')
        thing=(0,0,0)
        bpy.context.scene.cursor.rotation_euler = (0, 0, 0)
        bpy.data.collections.new(str(split[0]).upper())
        bpy.context.scene.collection.children.link(bpy.data.collections[str(split[0]).upper()])
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[str(split[0]).upper()]
        #bpy.ops.import_scene.fbx(filepath=path)
        bpy.ops.import_scene.fbx(filepath=path, use_custom_normals=True, ignore_leaf_bones=True, automatic_bone_orientation=True)        #for Obj in bpy.data.objects:
           # Obj.parent = None
        #    split=Obj.name.split("_")
        #    if split[1] == "0":
        #        bpy.data.objects.remove(Obj)
        #for Obj in bpy.data.objects:
        
        bpy.ops.object.select_all(action='DESELECT')
        newobjects = bpy.data.collections[str(split[0]).upper()].objects
        #newobjects = bpy.data.collections[str(Name)].objects
        #for obj in newobjects:
         #   Material(obj)
        #    #deselect all objects
        #    bpy.ops.object.select_all(action='DESELECT')
        #    tmp.append(obj.name[:8])
            #print(obj.name[:8])
            
        count=0
        MSH_OBJS = [m for m in bpy.data.collections[str(split[0]).upper()].objects if m.type == 'MESH']
        bpy.ops.outliner.orphans_purge()
        for OBJS in MSH_OBJS:
            #Select all mesh objects
            OBJS.select_set(state=True)
            bpy.context.view_layer.objects.active = OBJS
        #bpy.ops.object.join()
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')


assemble_map()
