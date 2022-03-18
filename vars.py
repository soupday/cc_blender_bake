
VERSION_STRING = "v0.0.0"

def set_version_string(bl_info):
    global VERSION_STRING
    VERSION_STRING = "v" + str(bl_info["version"][0]) + "." + str(bl_info["version"][1]) + "." + str(bl_info["version"][2])

BAKE_PREFIX = "bakeutil_"

NO_SIZE = 64
DEFAULT_SIZE = 1024

BAKE_TARGETS = [
    ("BLENDER","Blender", "Bake textures for Blender. The baked textures should be more performant than the complex node materials"),
    ("RL","Reallusion", "Bake textures for iClone / Character Creator"),
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
    elif target == "RL":
        return RL_MAPS
    return BLENDER_MAPS

# global_suffix: ['target_suffix', 'prop_name']
RL_MAPS = {
    "Diffuse": ["Diffuse", "diffuse_size"],
    "AO": ["AO", "ao_size"],
    "Blend": ["BlendMultiply", "diffuse_size"],
    "Subsurface": ["SSS", "sss_size"],
    "Thickness": ["Transmission", "thickness_size"],
    "Metallic": ["Metallic", "metallic_size"],
    "Specular": ["Specular", "specular_size"],
    "Roughness": ["Roughness", "roughness_size"],
    "Emission": ["Emission", "emissive_size"],
    "Alpha": ["Alpha", "alpha_size"],
    "Normal": ["Normal", "normal_size"],
    "Bump": ["Bump", "bump_size"],
    "MicroNormal": ["MicroNormal", "micronormal_size"],
    "MicroNormalMask": ["MicroNormalMask", "micronormalmask_size"],
}

BLENDER_MAPS = {
    "Diffuse": ["Diffuse", "diffuse_size"],
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
    "Diffuse": ["baseColor", "basemap_size"],
    "AO": ["occlusion", "gltf_size"],
    "Metallic": ["metallic", "gltf_size"],
    "Roughness": ["roughness", "gltf_size"],
    "Emission": ["emission", "emissive_size"],
    "Alpha": ["alpha", "basemap_size"],
    "Normal": ["normal", "normal_size"],
    # packed maps
    "BaseMap": ["baseMap", "basemap_size"],
    "GLTF": ["glTF", "gltf_size"],
}

UNITY_URP_MAPS = {
    "Diffuse": ["Diffuse", "basemap_size"],
    "AO": ["Occlusion", "ao_size"],
    "Metallic": ["Metallic", "metallic_alpha_size"],
    "Roughness": ["Roughness", "metallic_alpha_size"],
    "Emission": ["Emission", "emission_size"],
    "Alpha": ["Opacity", "basemap_size"],
    "Normal": ["Normal", "normal_size"],
    "Bump": ["bump", "bump_size"],
    "MicroNormal": ["Mask", "micronormalmask_size"],
    "MicroNormalMask": ["Detail", "detail_size"],
    # packed maps
    "BaseMap": ["BaseMap", "basemap_size"],
    "MetallicAlpha": ["MetallicAlpha", "metallic_alpha_size"],
}

UNITY_HDRP_MAPS = {
    "Diffuse": ["Diffuse", "basemap_size"],
    "AO": ["Occlusion", "mask_size"],
    "Subsurface": ["Subsurface", "sss_size"],
    "Thickness": ["Thickness", "thickness_size"],
    "Metallic": ["Metallic", "mask_size"],
    "Roughness": ["Roughness", "mask_size"],
    "Emission": ["Emission", "emission_size"],
    "Alpha": ["Opacity", "basemap_size"],
    "Normal": ["Normal", "normal_size"],
    "Bump": ["bump", "bump_size"],
    "MicroNormal": ["MicroNormal", "detail_size"],
    "MicroNormalMask": ["MicroNormalMask", "mask_size"],
    # packed maps
    "BaseMap": ["BaseMap", "basemap_size"],
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
        ["DIFFUSE"], ["Base Color:DIFFUSE"]
    ],

    "ao_size": [
        ["AO"], ["Base Color:AO"]
    ],

    "blend_size": [
        ["BLEND1"], ["Base Color:BLEND"]
    ],

    "sss_size": [
        ["SSS"], None
    ],

    "thickness_size": [
        ["TRANSMISSION"], None
    ],

    "transmission_size": [
        ["TRANSMISSION_OVERRIDE"], ["Transmission"]
        # note: there is no '_TRANSMISSION_B', it's just a key to override the
        # transmission texture size in the TEX_SIZE_OVERRIDE list...
    ],

    "specular_size": [
        ["SPECULAR", "SPECMASK"], ["Specular"]
    ],

    "metallic_size": [
        ["METALLIC"], ["Metallic"]
    ],

    "roughness_size": [
        ["ROUGHNESS"], ["Roughness"]
    ],

    "smoothness_size": [
        ["ROUGHNESS"], ["Roughness"]
    ],

    "emission_size": [
        ["EMISSION"], ["Emission"]
    ],

    "alpha_size": [
        ["ALPHA"], ["Alpha"]
    ],

    "normal_size": [
        ["NORMAL", "NORMALBLEND", "SCLERANORMAL"], ["Normal:NORMAL"]
    ],

    "bump_size": [
        ["BUMP"], ["Normal:BUMP"]
    ],

    "detail_size": [
        ["MICRONORMAL"], None
    ],

    "micronormalmask_size": [
        ["MICRONMASK"], None
    ],

    "micronormal_size": [
        ["MICRONORMAL"], None
    ],

    "mask_size": [
        ["ROUGHNESS", "AO", "METALLIC", "MICRONMASK"],
        ["Base Color:AO", "Roughness", "Metallic"]
    ],

    "metallic_alpha_size": [
        ["ROUGHNESS", "METALLIC"],
        ["Roughness", "Metallic"]
    ],

    "gltf_size": [
        ["AO", "ROUGHNESS", "METALLIC"],
        ["Base Color:AO", "Roughness", "Metallic"]
    ],

    "basemap_size": [
        ["DIFFUSE", "ALPHA"],
        ["Base Color:DIFFUSE", "Alpha"]
    ],
}


# override the texture size for procedurally generated maps
TEX_SIZE_OVERRIDE = {
    "CORNEA_LEFT": {
        "ROUGHNESS": 256,
        "SSS": 256,
        "SPECULAR": 256,
        "ALPHA": 256,
        "TRANSMISSION_OVERRIDE": 256,
    },

    "CORNEA_RIGHT": {
        "ROUGHNESS": 256,
        "SSS": 256,
        "SPECULAR": 256,
        "ALPHA": 256,
        "TRANSMISSION_OVERRIDE": 256,
    },

    "EYE_LEFT": {
        "ROUGHNESS": 256,
        "SSS": 256,
        "SPECULAR": 256,
    },

    "EYE_RIGHT": {
        "ROUGHNESS": 256,
        "SSS": 256,
        "SPECULAR": 256,
    },

    "OCCLUSION_LEFT": {
        "ALPHA": 256,
    },

    "OCCLUSION_RIGHT": {
        "ALPHA": 256,
    },

    "HAIR": {
        "BUMP": 2048,
    },

    "SMART_HAIR": {
        "BUMP": 2048,
    },

    "SCALP": {
        "BUMP": 2048,
    },
}