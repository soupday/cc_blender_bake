import bpy
from . import utils

NODE_PREFIX = "cc3iid_"

def get_material_cache(mat):
    """Returns the material cache for this material.

    Fetches the material cache for the material. Returns None if the material is not in the cache.
    """
    props = bpy.context.scene.CC3ImportProps
    if mat is not None:
        for cache in props.material_cache:
            if cache.material == mat:
                return cache
    return None

def get_cc3_tex(mat, id):
    nodes = mat.node_tree.nodes
    for node in nodes:
        if node.type == "TEX_IMAGE" and node.name.startswith(NODE_PREFIX + id):
            return node
    return None
