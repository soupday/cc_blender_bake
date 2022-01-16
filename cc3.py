import bpy
from . import utils

NODE_PREFIX = "cc3iid_"


def get_material_cache(mat):
        """Returns the material cache for this material.

        Fetches the material cache for the material. Returns None if the material is not in the cache.
        """

        props = bpy.context.scene.CC3ImportProps
        if mat is not None:
            for chr_cache in props.import_cache:
                for cache in chr_cache.eye_material_cache:
                    if cache.material == mat:
                        return cache
                for cache in chr_cache.hair_material_cache:
                    if cache.material == mat:
                        return cache
                for cache in chr_cache.head_material_cache:
                    if cache.material == mat:
                        return cache
                for cache in chr_cache.skin_material_cache:
                    if cache.material == mat:
                        return cache
                for cache in chr_cache.tongue_material_cache:
                    if cache.material == mat:
                        return cache
                for cache in chr_cache.teeth_material_cache:
                    if cache.material == mat:
                        return cache
                for cache in chr_cache.tearline_material_cache:
                    if cache.material == mat:
                        return cache
                for cache in chr_cache.eye_occlusion_material_cache:
                    if cache.material == mat:
                        return cache
                for cache in chr_cache.pbr_material_cache:
                    if cache.material == mat:
                        return cache
                for cache in chr_cache.sss_material_cache:
                    if cache.material == mat:
                        return cache
        return None