
if "bpy" in locals():
    import importlib
    importlib.reload(vars)
    importlib.reload(utils)
    importlib.reload(nodeutils)
    importlib.reload(cc3)
    importlib.reload(bake)

import bpy
from . import addon_updater_ops
from . import vars
from . import utils
from . import nodeutils
from . import cc3
from . import bake

bl_info = {
    "name": "CC3 Bake",
    "author": "Victor Soupday",
    "version": (0, 1, 1),
    "blender": (2, 80, 0),
    "category": "Character",
    "location": "3D View > Properties> CC3 Bake",
    "description": "Baking and stuff.",
    "wiki_url": "https://soupday.github.io/cc3_blender_bake/index.html",
    "tracker_url": "https://github.com/soupday/cc3_blender_bake/issues",
}

CLASSES = (bake.CC3BakeCache, bake.CC3BakeSettings, bake.CC3BakeMaterialSettings,
            bake.CC3BakeProps, bake.CC3Baker, bake.CC3Jpegify, bake.CC3BakePanel, bake.CC3BakeUtilityPanel,
            bake.MATERIAL_UL_weightedmatslots)

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


class CC3BakeAddonPreferences(bpy.types.AddonPreferences):
    # this must match the add-on name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__.partition(".")[0]

    # addon updater preferences
    auto_check_update: bpy.props.BoolProperty(
	    name="Auto-check for Update",
	    description="If enabled, auto-check for updates using an interval",
	    default=False,
	    )
    updater_intrval_months: bpy.props.IntProperty(
		name='Months',
		description="Number of months between checking for updates",
		default=0,
		min=0
		)
    updater_intrval_days: bpy.props.IntProperty(
		name='Days',
		description="Number of days between checking for updates",
		default=7,
		min=0,
		max=31
		)
    updater_intrval_hours: bpy.props.IntProperty(
		name='Hours',
		description="Number of hours between checking for updates",
		default=0,
		min=0,
		max=23
		)
    updater_intrval_minutes: bpy.props.IntProperty(
		name='Minutes',
		description="Number of minutes between checking for updates",
		default=0,
		min=0,
		max=59
		)

    def draw(self, context):
        addon_updater_ops.update_settings_ui(self,context)
