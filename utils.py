import bpy
import time

timer = 0

def log_info(msg, self = None):
    """Log an info message to console."""
    print(msg)
    if self:
        self.report({'INFO'}, msg)


def log_warn(msg, self = None):
    """Log a warning message to console."""
    print("Warning: " + msg)
    if self:
        self.report({'WARNING'}, msg)


def log_error(msg, self = None):
    """Log an error message to console and raise an exception."""
    print("Error: " + msg)
    if self:
        self.report({'ERROR'}, msg)


def start_timer():
    global timer
    timer = time.perf_counter()


def log_timer(msg, unit = "s"):
    global timer
    duration = time.perf_counter() - timer
    if unit == "ms":
        duration *= 1000
    elif unit == "us":
        duration *= 1000000
    elif unit == "ns":
        duration *= 1000000000
    elif unit == "m":
        duration /= 60
    elif unit == "h":
        duration /= 3600
    print(msg + ": " + str(duration) + " " + unit)


# remove any .001 from the material name
def strip_name(name):
    if name[-3:].isdigit() and name[-4] == ".":
        name = name[:-4]
    return name

def get_active_object():
    return bpy.context.view_layer.objects.active


def set_active_object(obj):
    bpy.context.view_layer.objects.active = obj


def set_mode(mode):
    if bpy.context.object == None:
        if mode != "OBJECT":
            log_error("No context object, unable to set any mode but OBJECT!")
            return False
        return True
    else:
        bpy.ops.object.mode_set(mode=mode)
        if bpy.context.object.mode != mode:
            log_error("Unable to set " + mode + " on object: " + bpy.context.object.name)
            return False
        return True


def find_cc3_rig():
    cc3_import_props = bpy.context.scene.CC3ImportProps
    for p in cc3_import_props.import_objects:
        obj = p.object
        if obj.type == "ARMATURE":
            if "Base_Spine01" in obj.pose.bones or "CC_Base_Spine01" in obj.pose.bones:
                return obj
    return None


def get_cc3_import_meshes():
    cc3_import_props = bpy.context.scene.CC3ImportProps
    meshes = []
    for p in cc3_import_props.import_objects:
        obj = p.object
        if obj.type == "MESH":
            meshes.append(obj)
    return meshes


def rest_pose(rig):
    if rig is not None and rig.type == "ARMATURE":
        rig.data.pose_position = 'REST'
        return True
    return False


def remove_collection(coll, item):
    for i in range(0, len(coll)):
        if coll[i] == item:
            coll.remove(i)
            return

def get_tex_image_size(node):
    if node is not None:
        return node.image.size[0] if node.image.size[0] > node.image.size[1] else node.image.size[1]
    return 64