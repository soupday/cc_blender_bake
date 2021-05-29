

if "bpy" in locals():
    import importlib
    importlib.reload(utils)
    importlib.reload(nodeutils)
    importlib.reload(bake)
    importlib.reload(cc3)

import bpy
import os
from . import utils
from . import nodeutils
from . import bake
from . import cc3

bl_info = {
    "name": "CC3 Baking",
    "author": "Victor Soupday",
    "version": (0, 1, 0),
    "blender": (2, 80, 0),
    "category": "Character",
    "location": "3D View > Properties> CC3 Bake",
    "description": "Baking and stuff.",
}

CLASSES = (bake.CC3BakeCache, bake.CC3BakeSettings, bake.CC3BakeMaterialSettings,
            bake.CC3BakeProps, bake.CC3Baker, bake.CC3Jpegify, bake.CC3BakePanel, bake.CC3BakeUtilityPanel,
            bake.MATERIAL_UL_weightedmatslots)

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.CC3BakeProps = bpy.props.PointerProperty(type=bake.CC3BakeProps)

def unregister():
    for cls in CLASSES:
        bpy.utils.unregister_class(cls)
    del(bpy.types.Scene.CC3BakeProps)