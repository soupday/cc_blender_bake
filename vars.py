

BAKE_PREFIX = "bakeutil_"

NO_SIZE = 64
DEFAULT_SIZE = 1024

BAKE_TARGETS = [
    ("BLENDER","Blender", "Bake textures for Blender. The baked textures should be more performant than the complex node materials"),
    ("SKETCHFAB","Sketchfab", "Bake and name the textures for Sketchfab. Uploading the baked textures with the .blend file to Sketchfab should auto connect the textures to the materials"),
    ("GLTF","GLTF", "Bake the relevant textures to be compatible with the GLTF exporter"),
    ("UNITY_HDRP","Unity HDRP","Bake and pack the textures for the Unity HDRP/Lit shader. Once baked only the BaseMap, Mask and Detail, Subsurface, Thickness and Emission textures are needed"),
    ("UNITY_URP","Unity 3D/URP","Bake the textures for Unity 3D Standard shader or for URP/Lit shader"),
]

TARGET_FORMATS = [
    ("PNG","PNG", "Bake textures to PNG Format."),
    ("JPEG","JPEG", "Bake textures to JPEG Format."),
]

CONVERSION_FUNCTIONS = [
    ("IR","1 - R", "Inverted Roughness"),
    ("SIR","(1 - R)^2", "Squared Inverted Roughnes"),
    ("IRS","1 - R^2", "Inverted Roughness Squared"),
    ("IRSR","1 - sqrt(R)","Inverted Roughness Square Root"),
    ("SRIR","sqrt(1 - R)","Square Root of Inverted Roughness"),
    ("SRIRS","sqrt(1 - R^2)","Square Root of Inverted Roughness Squared"),
]

def get_bake_target_maps(target):
    if target == "SKETCHFAB":
        return SKETCHFAB_MAPS
    elif target == "GLTF":
        return GLTF_MAPS
    elif target == "UNITY_URP":
        return UNITY_URP_MAPS
    elif target == "UNITY_HDRP":
        return UNITY_HDRP_MAPS
    return BLENDER_MAPS

# global_suffix: ['target_suffix', 'prop_name']
BLENDER_MAPS = {
    "Diffuse": ["Diffuse", "diffuse_size"],
    #"AO": ["AO", "ao_size"],
    "Subsurface": ["Subsurface", "sss_size"],
    "Metallic": ["Metallic", "metallic_size"],
    "Specular": ["Specular", "specular_size"],
    "Roughness": ["Roughness", "roughness_size"],
    "Emission": ["Emission", "emissive_size"],
    "Alpha": ["Alpha", "alpha_size"],
    "Transmission": ["Transmission", "transmission_size"],
    "Normal": ["Normal", "normal_size"],
    "Bump": ["Bump", "bump_size"],
    "MicroNormal": ["MicroNormal", "micronormal_size"],
    "MicroNormalMask": ["MicroNormalMask", "micronormalmask_size"],
}

SKETCHFAB_MAPS = {
    "Diffuse": ["diffuse", "diffuse_size"],
    "AO": ["ao", "ao_size"],
    "Subsurface": ["subsurface", "sss_size"],
    "Thickness": ["thickness", "thickness_size"],
    "Metallic": ["metallic", "metallic_size"],
    "Specular": ["specularf0", "specular_size"],
    "Roughness": ["roughness", "roughness_size"],
    "Emission": ["emission", "emissive_size"],
    "Alpha": ["opacity", "alpha_size"],
    "Normal": ["normal", "normal_size"],
    "Bump": ["bump", "bump_size"],
}

GLTF_MAPS = {
    "Diffuse": ["baseColor", "diffuse_size"],
    "AO": ["occlusion", "ao_size"],
    "Metallic": ["metallic", "metallic_size"],
    "Roughness": ["roughness", "roughness_size"],
    "Emission": ["emission", "emissive_size"],
    "Alpha": ["alpha", "alpha_size"],
    "Normal": ["normal", "normal_size"],
}

UNITY_URP_MAPS = {
    "Diffuse": ["Diffuse", "diffuse_size"],
    "Metallic": ["Metallic", "metallic_size"],
    "Roughness": ["Roughness", "roughness_size"],
    "Emission": ["Emission", "emission_size"],
    "Alpha": ["Opacity", "diffuse_size"],
    "Normal": ["Normal", "normal_size"],
    "Bump": ["bump", "bump_size"],

    "Smoothness": ["Smoothness", "roughness_size"],
}

UNITY_HDRP_MAPS = {
    "Diffuse": ["Diffuse", "diffuse_size"],
    "AO": ["AO", "mask_size"],
    "Subsurface": ["Subsurface", "sss_size"],
    "Thickness": ["Thickness", "thickness_size"],
    "Metallic": ["Metallic", "mask_size"],
    "Roughness": ["Roughness", "mask_size"],
    "Emission": ["Emission", "emission_size"],
    "Alpha": ["Opacity", "diffuse_size"],
    "Normal": ["Normal", "normal_size"],
    "Bump": ["bump", "bump_size"],
    "MicroNormal": ["MicroNormal", "detail_size"],
    "MicroNormalMask": ["MicroNormalMask", "mask_size"],

    "BaseMap": ["BaseMap", "diffuse_size"],
    "Mask": ["Mask", "mask_size"],
    "Detail": ["Detail", "detail_size"],
}


TEX_LIST = [
        ("64","64 x 64","64 x 64 texture size"),
        ("128","128 x 128","128 x 128 texture size"),
        ("256","256 x 256","256 x 256 texture size"),
        ("512","512 x 512","512 x 512 texture size"),
        ("1024","1024 x 1024","1024 x 1024 texture size"),
        ("2048","2048 x 2048","2048 x 2048 texture size"),
        ("4096","4096 x 4096","4096 x 4096 texture size"),
        ("8192","8192 x 8192","8192 x 8192 texture size"),
    ]


TEX_SIZE_DETECT = {
    "diffuse_size": [
        ["diffuse_tex"], ["Base Color:DIFFUSE"]
    ],

    "ao_size": [
        ["ao_tex"], ["Base Color:AO"]
    ],

    "sss_size": [
        ["sss_tex"], None
    ],

    "thickness_size": [
        ["transmission_tex"], None
    ],

    "transmission_size": [
        ["transmissionb_tex"], ["Transmission"]
        # note: there is no 'transmissionb_tex', it's just a key to override the
        # transmission texture size in the TEX_SIZE_OVERRIDE list...
    ],

    "specular_size": [
        ["specular_tex", "specular_mask_tex"], ["Specular"]
    ],

    "metallic_size": [
        ["metallic_tex"], ["Metallic"]
    ],

    "roughness_size": [
        ["roughness_tex"], ["Roughness"]
    ],

    "smoothness_size": [
        ["roughness_tex"], ["Roughness"]
    ],

    "emission_size": [
        ["emission_tex"], ["Emission"]
    ],

    "alpha_size": [
        ["opacity_tex"], ["Alpha"]
    ],

    "normal_size": [
        ["normal_tex", "normal_blend_tex", "sclera_normal_tex"], ["Normal:NORMAL"]
    ],

    "bump_size": [
        ["bump_tex"], ["Normal:BUMP"]
    ],

    "detail_size": [
        ["micro_normal_tex"], None
    ],

    "micronormalmask_size": [
        ["micro_normal_mask_tex"], None
    ],

    "micronormal_size": [
        ["micro_normal_tex"], None
    ],

    "mask_size": [
        ["roughness_tex", "ao_tex", "metallic_tex", "micro_normal_mask_tex"],
        ["Base Color", "Roughness", "Metallic"]
    ],
}


# override the texture size for procedurally generated maps
TEX_SIZE_OVERRIDE = {
    "CORNEA_LEFT": {
        "roughness_tex": 256,
        "sss_tex": 256,
        "specular_tex": 256,
        "opacity_tex": 256,
        "transmissionb_tex": 256,
    },

    "CORNEA_RIGHT": {
        "roughness_tex": 256,
        "sss_tex": 256,
        "specular_tex": 256,
        "opacity_tex": 256,
        "transmissionb_tex": 256,
    },

    "EYE_LEFT": {
        "roughness_tex": 256,
        "sss_tex": 256,
        "specular_tex": 256,
    },

    "EYE_RIGHT": {
        "roughness_tex": 256,
        "sss_tex": 256,
        "specular_tex": 256,
    },

    "OCCLUSION_LEFT": {
        "opacity_tex": 256,
    },

    "OCCLUSION_RIGHT": {
        "opacity_tex": 256,
    },

    "HAIR": {
        "bump_tex": 2048,
    },

    "SMART_HAIR": {
        "bump_tex": 2048,
    },

    "SCALP": {
        "bump_tex": 2048,
    },
}