
if "bpy" in locals():
    import importlib
    importlib.reload(vars)
    importlib.reload(utils)
    importlib.reload(nodeutils)
    importlib.reload(cc3)
    importlib.reload(prefs)
    importlib.reload(bake)

import bpy
from . import addon_updater_ops
from . import vars
from . import utils
from . import nodeutils
from . import cc3
from . import prefs
from . import bake

bl_info = {
    "name": "CC/iC Baking Tool",
    "author": "Victor Soupday",
    "version": (1, 0, 6),
    "blender": (2, 80, 0),
    "category": "Character",
    "location": "3D View > Properties > CC/iC Bake",
    "description": "Baking and stuff.",
    "wiki_url": "https://soupday.github.io/cc_blender_bake/index.html",
    "tracker_url": "https://github.com/soupday/cc_blender_bake/issues",
}

vars.set_version_string(bl_info)

CLASSES = (bake.CC3BakeCache, bake.CC3BakeSettings, bake.CC3BakeMaterialSettings,
            bake.CC3BakeProps, bake.CC3Baker, bake.CC3Jpegify, bake.CC3BakePanel, bake.CC3BakeUtilityPanel,
            bake.MATERIAL_UL_weightedmatslots,
            prefs.CC3BakeAddonPreferences
            )

def register():
    addon_updater_ops.register(bl_info)

    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.CC3BakeProps = bpy.props.PointerProperty(type=bake.CC3BakeProps)

def unregister():
    addon_updater_ops.unregister()

    for cls in CLASSES:
        bpy.utils.unregister_class(cls)
    del(bpy.types.Scene.CC3BakeProps)





