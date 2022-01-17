import bpy
import os
import mathutils
from . import addon_updater_ops
from . import utils
from . import nodeutils
from . import cc3
from . import vars


def make_new_image(name, size, format, ext, dir, data, alpha):
    img = bpy.data.images.new(name, size, size, alpha=alpha, is_data=data)
    img.pixels[0] = 0
    img.file_format = format
    dir = os.path.join(bpy.path.abspath("//"), dir)
    os.makedirs(dir, exist_ok=True)
    img.filepath_raw = os.path.join(dir, name + ext)
    img.save()
    return img


def get_image_format():
    props = bpy.context.scene.CC3BakeProps
    format = props.target_format
    ext = ".jpg"

    if format == "PNG":
        ext = ".png"
    elif format == "JPEG":
        ext = ".jpg"

    return format, ext


def get_bake_path():
    props = bpy.context.scene.CC3BakeProps

    base_dir = os.path.join(bpy.path.abspath("//"))
    bake_path = props.bake_path
    try:
        if os.path.isabs(bake_path):
            path = bake_path
        else:
            path = os.path.join(base_dir, bake_path)
    except:
        path = os.path.join(base_dir, "Bake")

    return path


def make_image_target(nodes, name, size, data = True, alpha = False):
    props = bpy.context.scene.CC3BakeProps

    format, ext = get_image_format()
    depth = 24
    if alpha:
        format = "PNG"
        ext = ".png"
        depth = 32

    path = get_bake_path()

    # find an old image with the same name to reuse:
    for img in bpy.data.images:
        if img.name.startswith(name) and img.name.endswith(name):

            img_path, img_file = os.path.split(img.filepath)
            same_path = False
            try:
                if os.path.samefile(path, img_path):
                    same_path = True
            except:
                same_path = False

            if img.file_format == format and img.depth == depth and same_path:
                utils.log_info("Reusing image: " + name)
                try:
                    if img.size[0] != size or img.size[1] != size:
                        utils.log_info("Scaling image: " + name + " to: " + str(size))
                        img.scale(size, size)
                    return img
                except:
                    utils.log_info("Bad image: " + img.name)
                    bpy.data.images.remove(img)
            else:
                utils.log_info("Wrong path or format: " + img.name + ", " + img_path + "==" + path + "?, " + img.file_format + "==" + format + "?, depth: " + str(depth) + "==" + str(img.depth) + "?")
                bpy.data.images.remove(img)

    # or just make a new one:
    utils.log_info("Creating new image: " + name + " size: " + str(size))
    img = make_new_image(name, size, format, ext, path, data, alpha)
    return img


def copy_image_target(image_node, name, size, data = True, alpha = False):
    props = bpy.context.scene.CC3BakeProps

    # return None if it's a bad image source
    if image_node is None or image_node.image is None:
        return None
    if image_node.image.size[0] == 0 or image_node.image.size[1] == 0:
        return None

    format, ext = get_image_format()
    depth = 24
    if alpha:
        format = "PNG"
        ext = ".png"
        depth = 32

    path = get_bake_path()

    # find an old image with the same name to reuse:
    for img in bpy.data.images:
        if img.name.startswith(name) and img.name.endswith(name):

            img_path, img_file = os.path.split(img.filepath)
            same_path = False
            try:
                if os.path.samefile(path, img_path):
                    same_path = True
            except:
                same_path = False

            if same_path:
                utils.log_info("Removing existing copy: " + img.name)
                bpy.data.images.remove(img)

    utils.log_info("Copying existing image: " + image_node.image.name)
    img = image_node.image.copy()
    img.name = name
    if img.size[0] != size or img.size[1] != size:
        utils.log_info("Resizing image: " + str(size))
        img.scale(size, size)
    if img.file_format != format:
        if utils.check_blender_version("3.0.0"):
            utils.log_info("Changing image format: " + format)
            img.file_format = format
        else:
            utils.log_info("Not changing image format of copy in Blender <= 2.93 (causes crash): " + format)

    dir = os.path.join(bpy.path.abspath("//"), path)
    os.makedirs(dir, exist_ok=True)
    img.filepath_raw = os.path.join(dir, name + ext)
    img.save()

    return img


def copy_target(source_mat, mat, source_node, source_socket, map_suffix, data):
    props = bpy.context.scene.CC3BakeProps
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    target_suffix = get_target_map_suffix(map_suffix)
    mat_name = utils.strip_name(mat.name)
    size = get_target_map_size(source_mat, map_suffix)

    utils.log_info("Copying direct image source: " + source_node.name)

    image = copy_image_target(source_node, mat_name + "_" + target_suffix, size, data)

    # fall back to baking the source if we can't copy the image:
    if image is None and source_socket:
        utils.log_info("Bad image source, falling back to baking!")
        return bake_target(source_mat, mat, source_node, source_socket, map_suffix, data)

    if image:
        image_node = nodeutils.make_image_node(nodes, image)
        image_node.name = vars.BAKE_PREFIX + mat_name + "_" + map_suffix
        return image_node

    return None


old_samples = 64
old_file_format = "PNG"
old_quality = 90
old_compression = 15
old_view_transform = "Standard"
old_look = "None"
old_gamma = 1
old_exposure = 0
old_colorspace = "Raw"

def prep_bake(width, height):
    global old_samples, old_file_format, old_quality, old_compression
    global old_view_transform, old_look, old_gamma, old_exposure, old_colorspace

    old_samples = bpy.context.scene.cycles.samples
    old_file_format = bpy.context.scene.render.image_settings.file_format
    old_quality = bpy.context.scene.render.image_settings.quality
    old_compression = bpy.context.scene.render.image_settings.compression
    old_view_transform = bpy.context.scene.view_settings.view_transform
    old_look = bpy.context.scene.view_settings.look
    old_gamma = bpy.context.scene.view_settings.gamma
    old_exposure = bpy.context.scene.view_settings.exposure
    old_colorspace = bpy.context.scene.sequencer_colorspace_settings.name

    props = bpy.context.scene.CC3BakeProps

    bpy.context.scene.cycles.samples = props.bake_samples
    # blender 3.0
    if utils.check_blender_version("3.0.0"):
        bpy.context.scene.cycles.preview_samples = props.bake_samples
        bpy.context.scene.cycles.use_adaptive_sampling = False
        bpy.context.scene.cycles.use_preview_adaptive_sampling = False
        bpy.context.scene.cycles.use_denoising = False
        bpy.context.scene.cycles.use_preview_denoising = False
        bpy.context.scene.cycles.use_auto_tile = False

    bpy.context.scene.render.use_bake_multires = False
    bpy.context.scene.render.bake.use_selected_to_active = False
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.target = 'IMAGE_TEXTURES'
    bpy.context.scene.render.bake.margin = 1
    bpy.context.scene.render.bake.use_clear = True
    bpy.context.scene.render.image_settings.file_format = get_image_format()[0]
    bpy.context.scene.render.image_settings.quality = props.jpeg_quality
    bpy.context.scene.render.image_settings.compression = props.png_compression

    bpy.context.scene.view_settings.view_transform = 'Standard' #'Raw'
    bpy.context.scene.view_settings.look = 'None'
    bpy.context.scene.view_settings.gamma = 1
    bpy.context.scene.view_settings.exposure = 0
    bpy.context.scene.sequencer_colorspace_settings.name = 'Raw'

def post_bake():
    global old_samples, old_file_format, old_quality, old_compression
    global old_view_transform, old_look, old_gamma, old_exposure, old_colorspace

    bpy.context.scene.cycles.samples = old_samples

    bpy.context.scene.render.image_settings.file_format = old_file_format
    bpy.context.scene.render.image_settings.quality = old_quality
    bpy.context.scene.render.image_settings.compression = old_compression

    bpy.context.scene.view_settings.view_transform = old_view_transform
    bpy.context.scene.view_settings.look = old_look
    bpy.context.scene.view_settings.gamma = old_gamma
    bpy.context.scene.view_settings.exposure = old_exposure
    bpy.context.scene.sequencer_colorspace_settings.name = old_colorspace



def bake_target(source_mat, mat, source_node, source_socket, map_suffix, data):
    props = bpy.context.scene.CC3BakeProps
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    target_suffix = get_target_map_suffix(map_suffix)
    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")
    mat_name = utils.strip_name(mat.name)
    target_size = get_target_map_size(source_mat, map_suffix)
    source_size = detect_size_from_suffix(source_mat, map_suffix)

    if props.scale_maps and target_size < source_size:
        utils.log_info("Baking source size: " + str(source_size))
        size = source_size
    else:
        size = target_size

    image = make_image_target(nodes, mat_name + "_" + target_suffix, size, data)
    image_node = nodeutils.make_image_node(nodes, image)
    image_node.name = vars.BAKE_PREFIX + mat_name + "_" + map_suffix

    bpy.context.scene.cycles.samples = props.bake_samples
    utils.log_info("Baking: " + source_node.name + " / " + source_socket + " suffix " + target_suffix)

    prep_bake(size, size)

    nodeutils.link_nodes(links, source_node, source_socket, output_node, "Surface")
    image_node.select = True
    nodes.active = image_node
    bpy.ops.object.bake(type='COMBINED')

    if props.scale_maps and target_size < source_size:
        utils.log_info("Scaling to target size: " + str(target_size))
        image.scale(target_size, target_size)

    image.save_render(filepath = image.filepath, scene = bpy.context.scene)
    image.reload()

    post_bake()

    return image_node


def bake_shader_normal(source_mat, mat):
    props = bpy.context.scene.CC3BakeProps

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    target_suffix = get_target_map_suffix("Normal")
    shader_node = nodeutils.get_shader_node(nodes)
    bsdf_node = nodeutils.get_bsdf_node(nodes)
    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")
    mat_name = utils.strip_name(mat.name)

    target_size = get_target_map_size(source_mat, "Normal")
    source_size = detect_size_from_suffix(source_mat, "Normal")

    if props.scale_maps and target_size < source_size:
        size = source_size
    else:
        size = target_size

    image = make_image_target(nodes, mat_name + "_" + target_suffix, size, True)
    image_node = nodeutils.make_image_node(nodes, image)
    image_node.name = vars.BAKE_PREFIX + mat_name + "_Normal"

    prep_bake(size, size)

    nodeutils.link_nodes(links, bsdf_node, "BSDF", output_node, "Surface")
    image_node.select = True
    nodes.active = image_node
    bpy.ops.object.bake(type='NORMAL')

    if props.scale_maps and target_size < source_size:
        image.scale(target_size, target_size)

    image.save_render(filepath = image.filepath, scene = bpy.context.scene)
    image.reload()

    post_bake()

    return image_node


def bake_socket_input(source_mat, mat, to_node, to_socket, suffix, data = True):
    from_node = nodeutils.get_node_connected_to_input(to_node, to_socket)
    from_socket = nodeutils.get_socket_connected_to_input(to_node, to_socket)
    return bake_socket_output(source_mat, mat, from_node, from_socket, suffix, data)


def bake_socket_output(source_mat, mat, from_node, from_socket, suffix, data = True):
    if from_node:
        # Note: Don't copy Alpha inputs as full textures, just Color inputs:
        if from_node.type == "TEX_IMAGE" and from_socket == "Color":
            return copy_target(source_mat, mat, from_node, from_socket, suffix, data)
        else:
            return bake_target(source_mat, mat, from_node, from_socket, suffix, data)
    return from_node


def position(node, loc):
    if node:
        node.location = loc


def prep_diffuse(mat, shader_node):
    props = bpy.context.scene.CC3BakeProps
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    # turn off depth for cornea parallax
    parallax_tiling_node = nodeutils.find_node_by_keywords(nodes, nodeutils.NODE_PREFIX, "(tiling_rl_cornea_shader_DIFFUSE_mapping)")
    if parallax_tiling_node:
        nodeutils.set_node_input(parallax_tiling_node, "Depth", 0.0)
    # for baking separate diffuse and AO, set the amount of AO to bake into the diffuse map
    if shader_node:
        nodeutils.set_node_input(shader_node, "AO Strength", props.ao_in_diffuse)


def prep_ao(mat, shader_node):
    props = bpy.context.scene.CC3BakeProps
    ao_strength = 1.0
    if shader_node:
        # fetch the intended ao strength
        ao_strength = nodeutils.get_node_input(shader_node, "AO Strength", 1.0)
        # max out the ao strength for baking
        nodeutils.set_node_input(shader_node, "AO Strength", 1.0)
    return ao_strength


def prep_sss(shader_node, bsdf_node : bpy.types.Node):
    props = bpy.context.scene.CC3BakeProps
    sss_radius = mathutils.Vector((0.01, 0.01, 0.01))
    sss_radius = nodeutils.get_node_input(bsdf_node, "Subsurface Radius", sss_radius)
    return sss_radius


def prep_alpha(mat, shader_node):
    props = bpy.context.scene.CC3BakeProps
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    return


def bake_material(obj, mat, source_mat):
    props = bpy.context.scene.CC3BakeProps
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader_node : bpy.types.Node = nodeutils.get_shader_node(nodes)
    bsdf_node = nodeutils.get_bsdf_node(nodes)
    bake_maps = vars.get_bake_target_maps(props.target_mode)

    utils.log_info("Baking for " + props.target_mode + ": " + obj.name + " / " + mat.name)
    utils.log_info("")

    # Texture Map Baking
    #

    # Diffuse Maps & AO
    diffuse_bake_node = None
    ao_bake_node = None
    ao_strength = 1.0
    if nodeutils.is_connected(bsdf_node, "Base Color"):
        if shader_node:
            # if the shader_node does not have an "AO" output node, then copy the AO texture directly.
            # note: so far, nothing has an "AO" output node.
            if "AO" in bake_maps:
                ao_strength = prep_ao(mat, shader_node)
                if "AO" in shader_node.outputs:
                    ao_bake_node = bake_socket_output(source_mat, mat, shader_node, "AO", "AO")
                else:
                    ao_node = nodeutils.find_shader_texture(nodes, "AO")
                    if ao_node:
                        ao_bake_node = bake_socket_output(source_mat, mat, ao_node, "Color", "AO")
            if "Diffuse" in bake_maps:
                # if there is a "Diffuse" output node, bake that, otherwise bake the "Base Color" output node.
                prep_diffuse(mat, shader_node)
                if "Diffuse" in shader_node.outputs:
                    diffuse_bake_node = bake_socket_output(source_mat, mat, shader_node, "Diffuse", "Diffuse", False)
                else:
                    diffuse_bake_node = bake_socket_output(source_mat, mat, shader_node, "Base Color", "Diffuse", False)
        elif bsdf_node:
            # bake BSDF base color input
            diffuse_bake_node = bake_socket_input(source_mat, mat, bsdf_node, "Base Color", "Diffuse", False)

    # Subsurface Scattering Maps
    sss_bake_node = None
    sss_radius = 1.0
    if nodeutils.is_connected(bsdf_node, "Subsurface"):
        if "Subsurface" in bake_maps:
            sss_radius = prep_sss(mat, shader_node)
            if shader_node:
                sss_bake_node = bake_socket_output(source_mat, mat, shader_node, "Subsurface", "Subsurface")
            elif bsdf_node:
                sss_bake_node = bake_socket_input(source_mat, mat, bsdf_node, "Subsurface", "Subsurface")

    # Thickness Maps (Subsurface transmission)
    # the transmission map texture is not used, but it is added to the material nodes
    thickness_bake_node = None
    if "Thickness" in bake_maps:
        utils.log_info("Processing Thickness/Transmission")
        thickness_node = nodeutils.find_shader_texture(nodes, "TRANSMISSION")
        if thickness_node:
            utils.log_info("thickness texture found...")
            thickness_bake_node = bake_socket_output(source_mat, mat, thickness_node, "Color", "Thickness")

    # Metallic Maps
    metallic_bake_node = None
    if nodeutils.is_connected(bsdf_node, "Metallic"):
        if "Metallic" in bake_maps:
            utils.log_info("Processing Metallic")
            if shader_node:
                metallic_bake_node = bake_socket_output(source_mat, mat, shader_node, "Metallic", "Metallic")
            elif bsdf_node:
                metallic_bake_node = bake_socket_input(source_mat, mat, bsdf_node, "Metallic", "Metallic")

    # Specular Maps
    specular_bake_node = None
    if nodeutils.is_connected(bsdf_node, "Specular"):
        if "Specular" in bake_maps:
            utils.log_info("Processing Specular")
            if shader_node:
                specular_bake_node = bake_socket_output(source_mat, mat, shader_node, "Specular", "Specular")
            elif bsdf_node:
                specular_bake_node = bake_socket_input(source_mat, mat, bsdf_node, "Specular", "Specular")
    specular_scale = 1.0
    if shader_node:
        specular_scale = nodeutils.get_node_input(shader_node, "Specular Scale", specular_scale)
        specular_scale = nodeutils.get_node_input(shader_node, "Front Specular", specular_scale)
    nodeutils.set_node_input(bsdf_node, "Specular", 0.5 * specular_scale)

    # Roughness Maps
    roughnesss_bake_node = None
    if nodeutils.is_connected(bsdf_node, "Roughness"):
        if "Roughness" in bake_maps:
            utils.log_info("Processing Roughness")
            if shader_node:
                roughnesss_bake_node = bake_socket_output(source_mat, mat, shader_node, "Roughness", "Roughness")
            elif bsdf_node:
                roughnesss_bake_node = bake_socket_input(source_mat, mat, bsdf_node, "Roughness", "Roughness")

    # Emission Maps
    # copy emission maps directly...
    emission_bake_node = None
    if nodeutils.is_connected(bsdf_node, "Emission"):
        if "Emission" in bake_maps:
            utils.log_info("Processing Emission")
            emission_node = nodeutils.find_shader_texture(nodes, "EMISSION")
            if emission_node:
                emission_bake_node = bake_socket_output(source_mat, mat, emission_node, "Color", "Emission")

    # Alpha Maps
    alpha_bake_node = None
    if nodeutils.is_connected(bsdf_node, "Alpha") or (shader_node and "Opacity" in shader_node.outputs):
        if ((mat.blend_method != "OPAQUE" and "Alpha" in bake_maps) or
            (shader_node and "Opacity" in shader_node.outputs and "Alpha" in bake_maps)):
            prep_alpha(mat, shader_node)
            if shader_node:
                if "Opacity" in shader_node.outputs:
                    alpha_bake_node = bake_socket_output(source_mat, mat, shader_node, "Opacity", "Alpha")
                    mat.blend_method = "BLEND"
                    mat.shadow_method = "NONE"
                else:
                    alpha_bake_node = bake_socket_output(source_mat, mat, shader_node, "Alpha", "Alpha")
            elif bsdf_node:
                alpha_bake_node = bake_socket_input(source_mat, mat, bsdf_node, "Alpha", "Alpha")

    # Transmission Maps (Refractive Transparency)
    transmission_bake_node = None
    if nodeutils.is_connected(bsdf_node, "Transmission"):
        if "Transmission" in bake_maps:
            if shader_node:
                transmission_bake_node = bake_socket_output(source_mat, mat, shader_node, "Transmission", "Transmission")
            elif bsdf_node:
                transmission_bake_node = bake_socket_input(source_mat, mat, bsdf_node, "Transmission", "Transmission")

    # Bump Maps
    # if shader group node has a "Bump Map" input, then copy the bump map texture directly
    bump_bake_node = None
    bump_distance = 0.01
    if nodeutils.is_connected(bsdf_node, "Normal"):
        if "Bump" in bake_maps and props.allow_bump_maps:
            if shader_node:
                bump_node = nodeutils.find_shader_texture(nodes, "BUMP")
                bump_distance = nodeutils.get_node_input(shader_node, "Bump Strength", 0.01)
                if bump_node:
                    bump_bake_node = bake_socket_output(source_mat, mat, bump_node, "Color", "Bump")
            elif bsdf_node:
                input_node = nodeutils.get_node_connected_to_input(bsdf_node, "Normal")
                if input_node.type == "BUMP":
                    height_node = nodeutils.get_node_connected_to_input(input_node, "Height")
                    if height_node:
                        bump_bake_node = bake_socket_input(source_mat, mat, input_node, "Height", "Bump")
                        bump_distance = nodeutils.get_node_input(input_node, "Distance", 1.0)

    # Normal Maps
    # if the shader group node has a "Blend Normal" color output, bake that,
    # otherwise copy the normal map texture directly
    # DO NOT BAKE the normal vector output.
    normal_bake_node = None
    normal_strength = 1.0
    bump_to_normal = False
    if nodeutils.is_connected(bsdf_node, "Normal"):
        if "Normal" in bake_maps:
            if "Bump" not in bake_maps or not props.allow_bump_maps:
                bump_to_normal = True
            if shader_node:
                normal_strength = nodeutils.get_node_input(shader_node, "Normal Strength", 1.0)
                if "Blend Normal" in shader_node.outputs:
                    normal_strength = 1.0
                    normal_bake_node = bake_socket_output(source_mat, mat, shader_node, "Blend Normal", "Normal")
                else:
                    normal_node = nodeutils.find_shader_texture(nodes, "NORMAL")
                    if normal_node:
                        normal_bake_node = bake_socket_output(source_mat, mat, normal_node, "Color", "Normal")
                    else:
                        normal_bake_node = bake_shader_normal(source_mat, mat)
            elif bsdf_node:
                input_node = nodeutils.get_node_connected_to_input(bsdf_node, "Normal")
                if input_node:
                    if input_node.type == "NORMAL_MAP":
                        # just a normal mapper, bake the entire normal input
                        normal_bake_node = bake_shader_normal(source_mat, mat)
                        normal_strength = nodeutils.get_node_input(input_node, "Strength", 1.0)
                    elif input_node.type == "BUMP":
                        # bump node mappers can have heightmap and normal inputs
                        normal_node = nodeutils.get_node_connected_to_input(input_node, "Normal")
                        height_node = nodeutils.get_node_connected_to_input(input_node, "Height")
                        if bump_to_normal:
                            # bake everything into the normal
                            normal_bake_node = bake_shader_normal(source_mat, mat)
                            normal_strength = 1.0
                        else:
                            # bake the normal separately
                            if normal_node:
                                normal_bake_node = bake_socket_input(source_mat, mat, input_node, "Normal", "Normal")
                                normal_strength = nodeutils.get_node_input(normal_node, "Strength", 1.0)
                    else:
                        # something is plugged into the normals, but can't tell what, so just bake the shader normals
                        normal_bake_node = bake_shader_normal(source_mat, mat)

    # Micro Normals
    # always copy the micro normal map texture directly
    micro_normal_bake_node = None
    micro_normal_strength = 1
    micro_normal_tiling = 20
    micro_normal_scale = mathutils.Vector((1, 1, 1))
    if nodeutils.is_connected(bsdf_node, "Normal"):
        if "MicroNormal" in bake_maps:
            micro_normal_node = nodeutils.find_shader_texture(nodes, "MICRONORMAL")
            if micro_normal_node:
                tiling_node = nodeutils.get_node_connected_to_input(micro_normal_node, "Vector")
                if tiling_node:
                    if "Tiling" in tiling_node.inputs:
                        micro_normal_scale = nodeutils.get_node_input(tiling_node, "Tiling", micro_normal_scale)
                        micro_normal_tiling = micro_normal_scale[0]
                        micro_normal_scale = mathutils.Vector((micro_normal_tiling, micro_normal_tiling, 1))
                    elif "Scale" in tiling_node.inputs:
                        micro_normal_scale = nodeutils.get_node_input(tiling_node, "Scale", micro_normal_scale)
                        micro_normal_tiling = micro_normal_scale[0]
                        micro_normal_scale = mathutils.Vector((micro_normal_tiling, micro_normal_tiling, 1))
                utils.log_info(f"Tiling: {micro_normal_scale}")
                # disconnect any tiling/mapping nodes before baking the micro normal...
                nodeutils.unlink_node(links, micro_normal_node, "Vector")
                micro_normal_bake_node = bake_socket_output(source_mat, mat, micro_normal_node, "Color", "MicroNormal")

    # Micro Normal Mask
    # if the shader group node as a "Normal Mask" float output, bake that,
    # otherwise copy the micro normal mask directly
    micro_normal_mask_bake_node = None
    micro_normal_stength = 1.0
    if nodeutils.is_connected(bsdf_node, "Normal"):
        if "MicroNormalMask" in bake_maps:
            if shader_node:
                if "Normal Mask" in shader_node.outputs:
                    micro_normal_mask_bake_node = bake_socket_output(source_mat, mat, shader_node, "Normal Mask", "MicroNormalMask")
                    micro_normal_strength = 1.0
                else:
                    micro_normal_mask_node = nodeutils.find_shader_texture(nodes, "MICRONMASK")
                    micro_normal_strength = nodeutils.get_node_input(shader_node, "Micro Normal Strength", 1.0)
                    if micro_normal_mask_node:
                        micro_normal_mask_bake_node = bake_socket_output(source_mat, mat, micro_normal_mask_node, "Color", "MicroNormalMask")

    # Post processing
    #
    utils.log_info("Post Processing Textures...")
    utils.log_info("")

    if props.target_mode == "BLENDER":
        pass

    elif props.target_mode == "SKETCHFAB":
        pass

    elif props.target_mode == "GLTF":
        if props.pack_gltf:
            # BaseMap: RGB: diffuse, A: alpha
            combine_diffuse_tex(nodes, source_mat, mat,
                    diffuse_bake_node, alpha_bake_node)
            # GLTF pack: R: Ao, G: Roughness, B: Metallic
            combine_gltf(nodes, source_mat, mat, ao_bake_node, roughnesss_bake_node, metallic_bake_node)

    elif props.target_mode == "UNITY_URP":
        # BaseMap: RGB: diffuse, A: alpha
        combine_diffuse_tex(nodes, source_mat, mat,
                diffuse_bake_node, alpha_bake_node)

        # MetallicAlpha: RGB: Metallic, A: Smoothness = f(Rougness)
        make_metallic_smoothness_tex(nodes, source_mat, mat, metallic_bake_node, roughnesss_bake_node)

    elif props.target_mode == "UNITY_HDRP":
        # BaseMap: RGB: diffuse, A: alpha
        combine_diffuse_tex(nodes, source_mat, mat,
                diffuse_bake_node, alpha_bake_node)

        # Mask: R: Metallic, G: AO, B: Micro-Normal Mask, A: Smoothness = f(Roughness)
        combine_hdrp_mask_tex(nodes, source_mat, mat,
                metallic_bake_node, ao_bake_node, micro_normal_mask_bake_node, roughnesss_bake_node)

        # Detail: R: 0.5, G: Micro-Normal.R, B: 0.5, A: Micro-Normal.G
        combine_hdrp_detail_tex(nodes, source_mat, mat,
                micro_normal_bake_node)

        # invert the thickness map
        process_hdrp_subsurfaces_tex(sss_bake_node, thickness_bake_node)

    # reconnect the materials

    utils.log_info("Reconnecting baked material:")
    utils.log_info("")

    reconnect_material(mat, ao_strength, sss_radius, bump_distance, normal_strength, micro_normal_strength, micro_normal_scale)


def combine_diffuse_tex(nodes, source_mat, mat, diffuse_node, alpha_node):
    diffuse_data = None
    alpha_data = None
    bsdf_node = nodeutils.get_bsdf_node(nodes)
    diffuse_value = nodeutils.get_node_input(bsdf_node, "Base Color", (1,1,1,1))
    # image.pixels object fetches the entire array anew every call and is extremely slow to use
    # directly so, for speed, make a copy of it into a tuple or a list and work on that.
    if diffuse_node:
        # read-only tuple copy for fastest read speed
        diffuse_data = diffuse_node.image.pixels[:]

    if alpha_node:
        # read-only tuple copy for fastest read speed
        alpha_data = alpha_node.image.pixels[:]

    if diffuse_node is None and alpha_node is None:
        return

    utils.log_info("Combining diffuse with alpha...")

    map_suffix = "BaseMap"
    target_suffix = get_target_map_suffix(map_suffix)
    mat_name = utils.strip_name(mat.name)
    size = get_target_map_size(source_mat, map_suffix)
    image = make_image_target(nodes, mat_name + "_" + target_suffix, size, False, True)
    image_node = nodeutils.make_image_node(nodes, image)
    image_node.name = vars.BAKE_PREFIX + mat_name + "_" + map_suffix
    image_node.select = True
    nodes.active = image_node
    # writeable list copy for fastest write speed
    image_data = list(image.pixels)
    l = len(image_data)

    for i in range(0, l, 4):
        if diffuse_data:
            image_data[i+0] = diffuse_data[i+0]
            image_data[i+1] = diffuse_data[i+1]
            image_data[i+2] = diffuse_data[i+2]
        else:
            image_data[i+0] = diffuse_value[0]
            image_data[i+1] = diffuse_value[1]
            image_data[i+2] = diffuse_value[2]

        if alpha_data:
            image_data[i+3] = alpha_data[i]
        else:
            image_data[i+3] = 1

    # replace in-place in one go.
    image.pixels[:] = image_data
    image.update()
    image.save()


def combine_hdrp_mask_tex(nodes, source_mat, mat, metallic_node, ao_node, mask_node, roughness_node):
    props = bpy.context.scene.CC3BakeProps

    metallic_data = None
    ao_data = None
    mask_data = None
    roughness_data = None

    if metallic_node:
        metallic_data = metallic_node.image.pixels[:]
    if ao_node:
        ao_data = ao_node.image.pixels[:]
    if mask_node:
        mask_data = mask_node.image.pixels[:]
    if roughness_node:
        roughness_data = roughness_node.image.pixels[:]

    if metallic_node is None and ao_node is None and mask_node is None and roughness_node is None:
        return

    utils.log_info("Combining Unity HDRP Mask Texture...")

    bsdf_node = nodeutils.get_bsdf_node(nodes)
    metallic_value = nodeutils.get_node_input(bsdf_node, "Metallic", 0.0)
    roughness_value = nodeutils.get_node_input(bsdf_node, "Roughness", 0.0)
    ao_value = 1
    mask_value = 1

    map_suffix = "Mask"
    target_suffix = get_target_map_suffix(map_suffix)
    mat_name = utils.strip_name(mat.name)
    size = get_target_map_size(source_mat, map_suffix)
    image = make_image_target(nodes, mat_name + "_" + target_suffix, size, True, True)
    image_node = nodeutils.make_image_node(nodes, image)
    image_node.name = vars.BAKE_PREFIX + mat_name + "_" + map_suffix
    image_node.select = True
    nodes.active = image_node
    image_data = list(image.pixels)
    l = len(image_data)

    # Mask: R: Metallic, G: AO, B: Micro-Normal Mask, A: Smoothness = 0.5 + 0.5*(1-Roughess)^2
    for i in range(0, l, 4):

        # Red
        if metallic_data:
            image_data[i] = metallic_data[i]
        else:
            image_data[i] = metallic_value

        # Green
        if ao_data:
            image_data[i+1] = ao_data[i]
        else:
            image_data[i+1] = ao_value

        # Blue
        if mask_data:
            image_data[i+2] = mask_data[i]
        else:
            image_data[i+2] = mask_value

        # Alpha
        if roughness_data:
            roughness = roughness_data[i]
        else:
            roughness = roughness_value

        if props.smoothness_mapping == "SIR":
            smoothness = pow(1 - roughness, 2)
        elif props.smoothness_mapping == "IRS":
            smoothness = 1 - pow(roughness, 2)
        elif props.smoothness_mapping == "IRSR":
            smoothness = 1 - pow(roughness, 0.5)
        elif props.smoothness_mapping == "SRIR":
            smoothness = pow(1 - roughness, 0.5)
        elif props.smoothness_mapping == "SRIRS":
            smoothness = pow(1 - pow(roughness, 2), 0.5)
        else: # IR
            smoothness = 1 - roughness

        image_data[i+3] = smoothness

    image.pixels[:] = image_data
    image.update()
    image.save()


def combine_hdrp_detail_tex(nodes, source_mat, mat, detail_normal_node):

    detail_data = None
    if detail_normal_node:
        detail_data = detail_normal_node.image.pixels[:]
    else:
        return

    utils.log_info("Combining Unity HDRP Detail Texture...")

    map_suffix = "Detail"
    target_suffix = get_target_map_suffix(map_suffix)
    mat_name = utils.strip_name(mat.name)
    size = get_target_map_size(source_mat, map_suffix)
    image = make_image_target(nodes, mat_name + "_" + target_suffix, size, True, True)
    image_node = nodeutils.make_image_node(nodes, image)
    image_node.name = vars.BAKE_PREFIX + mat_name + "_" + map_suffix
    image_node.select = True
    nodes.active = image_node
    image_data = list(image.pixels)
    l = len(image_data)

    # Detail: R: 0.5, G: Micro-Normal.R, B: 0.5, A: Micro-Normal.G
    for i in range(0, l, 4):

        image_data[i+0] = 0.5
        image_data[i+2] = 0.5

        if detail_data:
            image_data[i+1] = detail_data[i+0]
            image_data[i+3] = detail_data[i+1]
        else:
            image_data[i+1] = 0.5
            image_data[i+3] = 0.5

    image.pixels[:] = image_data
    image.update()
    image.save()


def process_hdrp_subsurfaces_tex(sss_node, trans_node):

    if trans_node and trans_node.image:
        image = trans_node.image
        trans_data = list(image.pixels)
        l = len(trans_data)
        for i in range(0, l, 4):
            trans_data[i+0] = 1.0 - trans_data[i+0]
            trans_data[i+1] = 1.0 - trans_data[i+1]
            trans_data[i+2] = 1.0 - trans_data[i+2]

        image.pixels[:] = trans_data
        image.update()
        image.save()


def make_metallic_smoothness_tex(nodes, source_mat, mat, metallic_node, roughness_node):
    props = bpy.context.scene.CC3BakeProps

    metallic_data = None
    roughness_data = None

    if metallic_node and metallic_node.image:
        metallic_data = metallic_node.image.pixels[:]
    if roughness_node and roughness_node.image:
        roughness_data = roughness_node.image.pixels[:]

    if metallic_node is None and roughness_node is None:
        return

    utils.log_info("Create Unity URP/3D Metallic Alpha Texture from Metallic and Roughness...")

    bsdf_node = nodeutils.get_bsdf_node(nodes)
    roughness_value = nodeutils.get_node_input(bsdf_node, "Roughness", 0.5)
    metallic_value = nodeutils.get_node_input(bsdf_node, "Metallic", 0)

    map_suffix = "MetallicAlpha"
    target_suffix = get_target_map_suffix(map_suffix)
    mat_name = utils.strip_name(mat.name)
    size = get_target_map_size(source_mat, map_suffix)
    image = make_image_target(nodes, mat_name + "_" + target_suffix, size, True, True)
    image_node = nodeutils.make_image_node(nodes, image)
    image_node.name = vars.BAKE_PREFIX + mat_name + "_" + map_suffix
    image_node.select = True
    nodes.active = image_node
    image_data = list(image.pixels)
    l = len(image_data)

    # Mask: R: Metallic, G: AO, B: Micro-Normal Mask, A: Smoothness = 0.5 + 0.5*(1-Roughess)^2
    for i in range(0, l, 4):

        if roughness_data:
            roughness = roughness_data[i]
        else:
            roughness = roughness_value

        if metallic_data:
            metallic = metallic_data[i]
        else:
            metallic = metallic_value

        if props.smoothness_mapping == "SIR":
            smoothness = pow(1 - roughness, 2)
        elif props.smoothness_mapping == "IRS":
            smoothness = 1 - pow(roughness, 2)
        elif props.smoothness_mapping == "IRSR":
            smoothness = 1 - pow(roughness, 0.5)
        elif props.smoothness_mapping == "SRIR":
            smoothness = pow(1 - roughness, 0.5)
        elif props.smoothness_mapping == "SRIRS":
            smoothness = pow(1 - pow(roughness, 2), 0.5)
        else: # IR
            smoothness = 1 - roughness

        image_data[i+0] = metallic
        image_data[i+1] = metallic
        image_data[i+2] = metallic
        image_data[i+3] = smoothness

    image.pixels[:] = image_data
    image.update()
    image.save()


def combine_gltf(nodes, source_mat, mat, ao_node, roughness_node, metallic_node):
    props = bpy.context.scene.CC3BakeProps

    metallic_data = None
    ao_data = None
    roughness_data = None

    if metallic_node:
        metallic_data = metallic_node.image.pixels[:]
    if ao_node:
        ao_data = ao_node.image.pixels[:]
    if roughness_node:
        roughness_data = roughness_node.image.pixels[:]

    if metallic_node is None and ao_node is None and roughness_node is None:
        return

    utils.log_info("Combining GLTF texture pack...")

    bsdf_node = nodeutils.get_bsdf_node(nodes)
    metallic_value = nodeutils.get_node_input(bsdf_node, "Metallic", 0.0)
    roughness_value = nodeutils.get_node_input(bsdf_node, "Roughness", 0.0)
    ao_value = 1

    map_suffix = "GLTF"
    target_suffix = get_target_map_suffix(map_suffix)
    mat_name = utils.strip_name(mat.name)
    size = get_target_map_size(source_mat, map_suffix)
    image = make_image_target(nodes, mat_name + "_" + target_suffix, size, True, False)
    image_node = nodeutils.make_image_node(nodes, image)
    image_node.name = vars.BAKE_PREFIX + mat_name + "_" + map_suffix
    image_node.select = True
    nodes.active = image_node
    image_data = list(image.pixels)
    l = len(image_data)

    # GLTF: R: AO, G: Roughness, B: Metallic
    for i in range(0, l, 4):

        # Red
        if ao_data:
            image_data[i+0] = ao_data[i]
        else:
            image_data[i+0] = ao_value

        # Green
        if roughness_data:
            image_data[i+1] = roughness_data[i]
        else:
            image_data[i+1] = roughness_value

        # Blue
        if metallic_data:
            image_data[i+2] = metallic_data[i]
        else:
            image_data[i+2] = metallic_value

    image.pixels[:] = image_data
    image.update()
    image.save()


def reconnect_material(mat, ao_strength, sss_radius, bump_distance, normal_strength, micro_normal_strength, micro_normal_scale):
    props = bpy.context.scene.CC3BakeProps

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    shader_node = nodeutils.get_shader_node(nodes)
    bsdf_node = nodeutils.get_bsdf_node(nodes)
    output_node = nodeutils.find_node_by_type(nodes, "OUTPUT_MATERIAL")

    nodeutils.link_nodes(links, bsdf_node, "BSDF", output_node, "Surface")

    diffuse_node = None
    basemap_node = None
    ao_node = None
    sss_node = None
    thickness_node = None
    metallic_node = None
    specular_node = None
    roughness_node = None
    emission_node = None
    alpha_node = None
    transmission_node = None
    normal_node = None
    bump_node = None
    mix_node = None
    bump_map_node = None
    normal_map_node = None
    micronormal_node = None
    micronormalmask_node = None

    gltf_settings_node = None
    gltf_node = None
    split_node = None

    micro_mix_node = None
    micro_mapping_node = None
    micro_texcoord_node = None
    micro_mask_mult_node = None

    mask_node = None
    detail_node = None

    if shader_node:
        nodes.remove(shader_node)

    for node in nodes:
        if node != bsdf_node and node != output_node:
            if vars.BAKE_PREFIX in node.name:
                if node.name.endswith("_Diffuse"):
                    diffuse_node = node
                elif node.name.endswith("_AO"):
                    ao_node = node
                elif node.name.endswith("_BaseMap"):
                    basemap_node = node
                elif node.name.endswith("_Subsurface"):
                    sss_node = node
                elif node.name.endswith("_Thickness"):
                    thickness_node = node
                elif node.name.endswith("_Metallic"):
                    metallic_node = node
                elif node.name.endswith("_Specular"):
                    specular_node = node
                elif node.name.endswith("_Roughness"):
                    roughness_node = node
                elif node.name.endswith("_Emission"):
                    emission_node = node
                elif node.name.endswith("_Alpha"):
                    alpha_node = node
                elif node.name.endswith("_Transmission"):
                    transmission_node = node
                elif node.name.endswith("_Normal"):
                    normal_node = node
                elif node.name.endswith("_MicroNormal"):
                    micronormal_node = node
                elif node.name.endswith("_MicroNormalMask"):
                    micronormalmask_node = node
                elif node.name.endswith("_Bump"):
                    bump_node = node
                elif node.name.endswith("_GLTF"):
                    gltf_node = node
                elif node.name.endswith("_Mask"):
                    mask_node = node
                elif node.name.endswith("_Detail"):
                    detail_node = node
            else:
                nodes.remove(node)

    if props.target_mode == "GLTF" and props.pack_gltf:
        if diffuse_node:
            nodes.remove(diffuse_node)
            diffuse_node = None
        if ao_node:
            nodes.remove(ao_node)
            ao_node = None
        if roughness_node:
            nodes.remove(roughness_node)
            roughness_node = None
        if metallic_node:
            nodes.remove(metallic_node)
            metallic_node = None
        if basemap_node:
            nodeutils.link_nodes(links, basemap_node, "Color", bsdf_node, "Base Color")
            if alpha_node:
                nodeutils.link_nodes(links, basemap_node, "Alpha", bsdf_node, "Alpha")
                nodes.remove(alpha_node)
                alpha_node = None
        if gltf_node:
            gltf_settings_node = nodeutils.make_gltf_settings_node(nodes)
            split_node = nodeutils.make_shader_node(nodes, "ShaderNodeSeparateRGB")
            nodeutils.link_nodes(links, gltf_node, "Color", split_node, "Image")
            nodeutils.link_nodes(links, split_node, "R", gltf_settings_node, "Occlusion")
            nodeutils.link_nodes(links, split_node, "G", bsdf_node, "Roughness")
            nodeutils.link_nodes(links, split_node, "B", bsdf_node, "Metallic")

    if diffuse_node and ao_node:

        if props.target_mode == "GLTF":
            nodeutils.link_nodes(links, diffuse_node, "Color", bsdf_node, "Base Color")
            gltf_settings_node = nodeutils.make_gltf_settings_node(nodes)
            nodeutils.link_nodes(links, ao_node, "Color", gltf_settings_node, "Occlusion")
        else:
            mix_node = nodeutils.make_mixrgb_node(nodes, "MULTIPLY")
            nodeutils.set_node_input(mix_node, "Fac", ao_strength)
            nodeutils.link_nodes(links, diffuse_node, "Color", mix_node, "Color1")
            nodeutils.link_nodes(links, ao_node, "Color", mix_node, "Color2")
            nodeutils.link_nodes(links, mix_node, "Color", bsdf_node, "Base Color")

    elif diffuse_node:
        nodeutils.link_nodes(links, diffuse_node, "Color", bsdf_node, "Base Color")

    if sss_node:
        nodeutils.link_nodes(links, sss_node, "Color", bsdf_node, "Subsurface")
        nodeutils.set_node_input(bsdf_node, "Subsurface Radius", sss_radius)
        if mix_node:
            nodeutils.link_nodes(links, mix_node, "Color", bsdf_node, "Subsurface Color")
        else:
            nodeutils.link_nodes(links, diffuse_node, "Color", bsdf_node, "Subsurface Color")

    if metallic_node:
        nodeutils.link_nodes(links, metallic_node, "Color", bsdf_node, "Metallic")
    if specular_node:
        nodeutils.link_nodes(links, specular_node, "Color", bsdf_node, "Specular")
    if roughness_node:
        nodeutils.link_nodes(links, roughness_node, "Color", bsdf_node, "Roughness")
    if emission_node:
        nodeutils.link_nodes(links, emission_node, "Color", bsdf_node, "Emission")
    if alpha_node:
        nodeutils.link_nodes(links, alpha_node, "Color", bsdf_node, "Alpha")
    if transmission_node:
        nodeutils.link_nodes(links, transmission_node, "Color", bsdf_node, "Transmission")

    if normal_node:
        normal_map_node = nodeutils.make_shader_node(nodes, "ShaderNodeNormalMap")
        nodeutils.link_nodes(links, normal_node, "Color", normal_map_node, "Color")
        nodeutils.link_nodes(links, normal_map_node, "Normal", bsdf_node, "Normal")
        nodeutils.set_node_input(normal_map_node, "Strength", normal_strength)
    elif bump_node:
        bump_map_node = nodeutils.make_shader_node(nodes, "ShaderNodeBump")
        nodeutils.link_nodes(links, bump_node, "Color", bump_map_node, "Height")
        nodeutils.link_nodes(links, bump_map_node, "Normal", bsdf_node, "Normal")
        nodeutils.set_node_input(bump_map_node, "Distance", bump_distance)

    if micronormal_node:
        if normal_map_node is None:
            normal_map_node = nodeutils.make_shader_node(nodes, "ShaderNodeNormalMap")
            nodeutils.link_nodes(links, normal_map_node, "Normal", bsdf_node, "Normal")
        micro_mix_node = nodeutils.make_mixrgb_node(nodes, "OVERLAY")
        micro_mapping_node = nodeutils.make_shader_node(nodes, "ShaderNodeMapping")
        micro_texcoord_node = nodeutils.make_shader_node(nodes, "ShaderNodeTexCoord")
        nodeutils.set_node_input(micro_mix_node, "Fac", micro_normal_strength)
        nodeutils.link_nodes(links, micro_texcoord_node, "UV", micro_mapping_node, "Vector")
        nodeutils.link_nodes(links, micro_mapping_node, "Vector", micronormal_node, "Vector")
        nodeutils.set_node_input(micro_mapping_node, "Scale", micro_normal_scale)
        if micronormalmask_node:
            micro_mask_mult_node = nodeutils.make_math_node(nodes, "MULTIPLY", 1, micro_normal_strength)
            nodeutils.link_nodes(links, micronormalmask_node, "Color", micro_mask_mult_node, 0)
            nodeutils.link_nodes(links, micro_mask_mult_node, "Value", micro_mix_node, "Fac")
        if normal_node:
            nodeutils.link_nodes(links, normal_node, "Color", micro_mix_node, "Color1")
        nodeutils.link_nodes(links, micronormal_node, "Color", micro_mix_node, "Color2")
        nodeutils.link_nodes(links, micro_mix_node, "Color", normal_map_node, "Color")

    position(bsdf_node, (200, 400))
    position(output_node, (600, 400))

    position(diffuse_node, (-600, 600))
    position(ao_node, (-900, 600))
    position(mix_node, (-300, 600))

    if props.target_mode == "GLTF" and props.pack_gltf:
        position(basemap_node, (-600, 600))
        position(gltf_node, (-900, 0))
        position(split_node, (-600, 0))
        position(gltf_settings_node, (200, 500))
    else:
        position(gltf_settings_node, (-600, 700))
        position(basemap_node, (-1800, 600))
        position(mask_node, (-1800, 300))
        position(detail_node, (-1800, 0))

    position(sss_node, (-600, 300))
    position(thickness_node, (-900, 300))

    position(metallic_node, (-1200, 0))
    position(specular_node, (-900, 0))
    position(roughness_node, (-600, 0))

    position(transmission_node, (-1200, -300))
    position(emission_node, (-900, -300))
    position(alpha_node, (-600, -300))

    position(normal_node, (-900, -600))
    position(normal_map_node, (-300, -600))
    position(bump_node, (-900, -600))
    position(bump_map_node, (-300, -600))
    position(micronormalmask_node, (-1200, -600))
    position(micronormal_node, (-1500, -600))

    position(micro_mix_node, (-470,-690))
    position(micro_mapping_node, (-1710,-600))
    position(micro_texcoord_node, (-1890,-600))
    position(micro_mask_mult_node, (-640,-600))


def bake_selected_objects():
    props = bpy.context.scene.CC3BakeProps

    utils.log_info("")
    utils.log_info("Baking Selected Objects:")
    utils.log_info("")

    objects = bpy.context.selected_objects.copy()
    active = bpy.context.active_object

    # deselect everything
    bpy.ops.object.select_all(action='DESELECT')
    # first create the bake plane
    bpy.ops.mesh.primitive_plane_add(size=2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
    bake_surface = bpy.context.active_object
    # this creates a single quad baking surface, as none of the node setups
    # use mesh geometry this means we can bake the entirety of the textures with an even sampling.

    # go into wireframe mode:
    shading = bpy.context.space_data.shading.type
    bpy.context.space_data.shading.type = 'WIREFRAME'
    # set cycles bake
    engine = bpy.context.scene.render.engine
    bpy.context.scene.render.engine = 'CYCLES'

    materials_done = []
    obj : bpy.types.Object
    for obj in objects:
        if obj.type == "MESH":
            bake_object(obj, bake_surface, materials_done)
        elif obj.type == "ARMATURE":
            for child in obj.children:
                bake_object(child, bake_surface, materials_done)
    materials_done.clear()

    bpy.data.objects.remove(bake_surface)

    bpy.context.scene.render.engine = engine
    bpy.context.space_data.shading.type = shading

    # restore selection
    utils.try_select_objects(objects, True)
    utils.set_active_object(active)



def next_uid():
    props = bpy.context.scene.CC3BakeProps
    uid = props.auto_increment
    props.auto_increment += 1
    return uid


def get_target_map(suffix):
    props = bpy.context.scene.CC3BakeProps

    bake_maps = vars.get_bake_target_maps(props.target_mode)

    if suffix in bake_maps:
        return bake_maps[suffix]

    utils.log_error("No matching target map for suffix: " + suffix)
    return None


def get_target_map_suffix(suffix):
    target_map = get_target_map(suffix)
    if target_map:
        return target_map[0]

    utils.log_error("No matching target map suffix: " + suffix)
    return "None"


def get_int_prop_by_name(props, prop_name):
    scope = locals()
    prop_val = eval("props." + prop_name)
    return int(prop_val)


def get_largest_texture_to_node(node, shader_node, done):
    largest = 0
    for socket in node.inputs:
        size = get_largest_texture_to_socket(node, socket.name, shader_node, done)
        if size > largest:
            largest = size
    return largest


def get_largest_texture_to_socket(node, socket, shader_node, done = None):

    if done is None:
        done = []

    if socket[-3:] == ":AO":
        connected_node = nodeutils.get_node_connected_to_input(node, socket[:-3])
        if connected_node.type == "MIX_RGB" and connected_node.blend_type == "MULTIPLY":
            # TODO: Maybe filter for *.(ao|ambient|occlusion)
            return get_largest_texture_to_socket(connected_node, "Color2", shader_node, done)

    elif socket[-8:] == ":DIFFUSE":
        connected_node = nodeutils.get_node_connected_to_input(node, socket[:-8])
        if connected_node.type == "MIX_RGB" and connected_node.blend_type == "MULTIPLY":
            return get_largest_texture_to_socket(connected_node, "Color1", shader_node, done)

    elif socket[-5:] == ":BUMP":
        connected_node = nodeutils.get_node_connected_to_input(node, socket[:-5])
        if connected_node.type == "BUMP":
            return get_largest_texture_to_socket(connected_node, "Height", shader_node, done)

    elif socket[-7:] == ":NORMAL":
        connected_node = nodeutils.get_node_connected_to_input(node, socket[:-7])
        if connected_node.type == "BUMP":
            return get_largest_texture_to_socket(connected_node, "Normal", shader_node, done)

    else:
        connected_node = nodeutils.get_node_connected_to_input(node, socket)

    if connected_node is None or connected_node in done or connected_node == shader_node:
        return 0
    done.append(connected_node)

    if connected_node.type == "TEX_IMAGE":
        return utils.get_tex_image_size(connected_node)
    else:
        return get_largest_texture_to_node(connected_node, shader_node, done)


def get_max_texture_size(mat, tex_list, input_list):
    """
    Attempts to get the largest texture size from the given named texure nodes (CC3 materials),
    then falls back to finding the largest texture connected to the given list of inputs to the BSDF shader
    """
    if mat is None or mat.node_tree is None or mat.node_tree.nodes is None:
        return vars.NO_SIZE

    max_size = 0
    mat_cache = cc3.get_material_cache(mat)

    if mat_cache is not None and tex_list is not None:
        for t in tex_list:
            tex_node = nodeutils.find_shader_texture(mat.node_tree.nodes, t)
            if tex_node is not None:
                size = utils.get_tex_image_size(tex_node)
                utils.log_info("Found CC3 texture: " + t + " size: " + str(size))
                if size > max_size:
                    max_size = size

    elif input_list is not None and max_size == 0:
        shader_node = nodeutils.get_shader_node(mat.node_tree.nodes)
        bsdf_node = nodeutils.get_bsdf_node(mat.node_tree.nodes)
        max_size = 0
        for i in input_list:
            size = get_largest_texture_to_socket(bsdf_node, i, shader_node)
            utils.log_info("Found largest input texture: " + i + " size: " + str(size))
            if size > max_size:
                max_size = size

    # here we can override the result based on the mat_cache.material_type and the looked for tex_list
    if mat_cache is not None:
        if mat_cache.material_type in vars.TEX_SIZE_OVERRIDE:
            mat_overrides = vars.TEX_SIZE_OVERRIDE[mat_cache.material_type]
            for t in tex_list:
                if t in mat_overrides:
                    utils.log_info("Overriding size for material: " + mat.name + " texture: " + t + " size: " + str(mat_overrides[t]))
                    size = mat_overrides[t]
                    if size > max_size:
                        max_size = size

    if max_size == 0:
        max_size = vars.NO_SIZE

    return max_size


# suffix as defined in: vars.py *_MAPS
def detect_size_from_suffix(mat, suffix):
    props = bpy.context.scene.CC3BakeProps

    target_map = get_target_map(suffix)
    if target_map:
        target_size = target_map[1]
        if target_size in vars.TEX_SIZE_DETECT:
            tex_size_detect = vars.TEX_SIZE_DETECT[target_size]
            tex_list = tex_size_detect[0]
            input_list = tex_size_detect[1]
            return get_max_texture_size(mat, tex_list, input_list)

    # otherwise just return the default of 1024
    return vars.DEFAULT_SIZE




def get_target_map_size(mat, suffix, no_max_override = False):

    # get either the global default props or the material specific props if they exist...
    props = bpy.context.scene.CC3BakeProps
    p = get_material_settings(mat)
    if p is None:
        p = props

    # fetch the default size from the the existing textures if possible
    size = detect_size_from_suffix(mat, suffix)
    max_size = int(props.max_size)

    if no_max_override:
        return max_size

    # if overriding with custom max sizes:
    bake_maps = vars.get_bake_target_maps(props.target_mode)
    if props.custom_sizes:
        if suffix in bake_maps:
            max_size = get_int_prop_by_name(p, bake_maps[suffix][1])
            utils.log_info(suffix + " map " + props.target_mode + " maximum map size: " + str(size))

    if size > max_size:
        utils.log_info("Clamping map size to: " + str(max_size))
        size = max_size

    return size


def get_target_material_name(name, uid):
    props = bpy.context.scene.CC3BakeProps

    # Sketchfab recommends no spaces or symbols in the texture names...
    if props.target_mode == "SKETCHFAB":
        text = name.replace("_", "").replace("-", "").replace(".", "")
        text += "B" + str(uid)
    else:
        text = name + "_B" + str(uid)
    return text


def bake_object(obj, bake_surface, materials_done):
    props = bpy.context.scene.CC3BakeProps

    for slot in obj.material_slots:
        source_mat = slot.material
        bake_cache = get_bake_cache(source_mat)

        # in case we haven't reverted to the source materials get the real source_mat:
        if (bake_cache and
            bake_cache.source_material is not None and
            bake_cache.source_material != source_mat):
            utils.log_info("Using cached source material!")
            source_mat = bake_cache.source_material

        # if there is no BSDF node, don't process.
        bsdf_node = None
        if source_mat and source_mat.node_tree:
            bsdf_node = nodeutils.get_bsdf_node(source_mat.node_tree.nodes)
        if bsdf_node is None:
            continue

        # only process each material once:
        if source_mat not in materials_done:
            materials_done.append(source_mat)

            old_mat = None
            if bake_cache is None:
                uid = next_uid()
            else:
                uid = bake_cache.uid
                if bake_cache.baked_material:
                    old_mat = bake_cache.baked_material

            bake_mat_name = get_target_material_name(source_mat.name, uid)

            # copy the source material
            bake_mat = source_mat.copy()
            bake_mat.name = "TEMP_" + bake_mat_name

            # try to find any old baked material by name
            if old_mat is None:
                for m in bpy.data.materials:
                    if m.name == bake_mat_name:
                        old_mat = m

            # replace all of the old baked materials with the new copy:
            if old_mat:
                for o in bpy.context.scene.objects:
                    if o != obj and o.type == "MESH" and o.data.materials:
                        for s in o.material_slots:
                            if s.material == old_mat:
                                s.material = bake_mat
                # remove the old material once all copies of it have been replaced...
                bpy.data.materials.remove(old_mat)

            # give the new copy the correct name
            bake_mat.name = bake_mat_name

            # add/update the bake cache
            add_bake_cache(uid, source_mat, bake_mat)

            # attach the bake material to the bake surface plane
            if len(bake_surface.data.materials) == 0:
                bake_surface.data.materials.append(bake_mat)
            else:
                bake_surface.data.materials[0] = bake_mat

            #try:
            bake_material(bake_surface, bake_mat, source_mat)
            slot.material = bake_mat
            #except:
            #   utils.log_error("Something went horribly wrong!")

        else:
            # if the material has already been baked elsewhere, replace the material here
            if bake_cache and slot.material != bake_cache.baked_material:
                slot.material = bake_cache.baked_material


def context_material(context):
    try:
        return context.object.material_slots[context.object.active_material_index].material
    except:
        return None


def get_bake_cache(mat):
    props = bpy.context.scene.CC3BakeProps
    for bc in props.bake_cache:
        if bc.source_material == mat or bc.baked_material == mat:
            return bc
    return None


def add_bake_cache(uid, source_mat, bake_mat):
    props = bpy.context.scene.CC3BakeProps
    bc = get_bake_cache(source_mat)
    if bc is None:
        bc = props.bake_cache.add()
        bc.uid = uid
        bc.source_material = source_mat
    bc.baked_material = bake_mat
    return bc


def remove_bake_cache(mat):
    props = bpy.context.scene.CC3BakeProps
    bc = get_bake_cache(mat)
    if bc:
        utils.remove_collection(props.bake_cache, bc)


def get_material_settings(mat):
    props = bpy.context.scene.CC3BakeProps
    if mat:
        for ms in props.material_settings:
            if ms.material == mat:
                return ms
    return None


def add_material_settings(mat):
    props = bpy.context.scene.CC3BakeProps
    ms = get_material_settings(mat)
    if ms is None:
        ms = props.material_settings.add()
        ms.material = mat
        ms.diffuse_size = props.diffuse_size
        ms.ao_size = props.ao_size
        ms.sss_size = props.sss_size
        ms.thickness_size = props.thickness_size
        ms.transmission_size = props.transmission_size
        ms.metallic_size = props.metallic_size
        ms.specular_size = props.specular_size
        ms.roughness_size = props.roughness_size
        ms.emissive_size = props.emissive_size
        ms.alpha_size = props.alpha_size
        ms.normal_size = props.normal_size
        ms.bump_size = props.bump_size
        ms.mask_size = props.mask_size
        ms.detail_size = props.detail_size
    return ms


def remove_material_settings(mat):
    props = bpy.context.scene.CC3BakeProps
    for ms in props.material_settings:
        if ms.material == mat:
            utils.remove_collection(props.material_settings, ms)


def revert_materials(objects):
    for obj in objects:
        if obj.type == "MESH":
            for i in range(0, len(obj.data.materials)):
                mat = obj.data.materials[i]
                bc = get_bake_cache(mat)
                if bc and bc.baked_material == mat:
                    obj.data.materials[i] = bc.source_material


def restore_baked_materials(objects):
    for obj in objects:
        if obj.type == "MESH":
            for i in range(0, len(obj.data.materials)):
                mat = obj.data.materials[i]
                bc = get_bake_cache(mat)
                if bc and bc.source_material == mat:
                    obj.data.materials[i] = bc.baked_material


class CC3Baker(bpy.types.Operator):
    """Bake CC3 Character"""
    bl_idname = "cc3.baker"
    bl_label = "Baker"
    bl_options = {"REGISTER"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    def execute(self, context):

        utils.start_timer()

        if self.param == "BAKE":
            bake_selected_objects()

        utils.log_timer("Baking Completed!", "m")

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "BAKE":
            return "Bake Textures..."
        return ""


class CC3BakeSettings(bpy.types.Operator):
    """Bake Settings"""
    bl_idname = "cc3.bakesettings"
    bl_label = "Bake Settings"
    bl_options = {"REGISTER"}

    param: bpy.props.StringProperty(
            name = "param",
            default = "",
            options={"HIDDEN"}
        )

    def execute(self, context):

        obj = context.object
        mat = context_material(context)
        mat_settings = get_material_settings(mat)

        if obj and obj.type == "MESH" and mat:

            if self.param == "ADD":
                add_material_settings(mat)

            if self.param == "REMOVE":
                remove_material_settings(mat)

            if self.param == "SOURCE":
                revert_materials(context.selected_objects)

            if self.param == "BAKED":
                restore_baked_materials(context.selected_objects)

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):

        if properties.param == "ADD":
            return "Add custom bake settings for this material."
        if properties.param == "REMOVE":
            return "Remove custom bake settings for this material."
        if properties.param == "SOURCE":
            return "Revert to the source materials."
        if properties.param == "BAKED":
            return "Restore the baked materials."
        if properties.param == "DEFAULTS":
            return "Attempt to assign default settings to each material in the selected objects."
        return ""


JPEGIFY_FORMATS = [
    "BMP",
    "PNG",
    "TARGA",
    "TARGA_RAW",
    "TIFF",
]


class CC3Jpegify(bpy.types.Operator):
    """Jpegifyer"""
    bl_idname = "cc3.jpegify"
    bl_label = "Jpegify"
    bl_options = {"REGISTER"}

    def execute(self, context):
        props = bpy.context.scene.CC3BakeProps

        bake_path = get_bake_path()
        os.makedirs(bake_path, exist_ok=True)
        bpy.context.scene.render.image_settings.quality = props.jpeg_quality

        for img in bpy.data.images:

            try:
                if img and img.size[0] > 0 and img.size[1] > 0:
                    if img.file_format in JPEGIFY_FORMATS:
                        img.file_format = "JPEG"
                        dir, file = os.path.split(img.filepath)
                        root, ext = os.path.splitext(file)
                        new_path = os.path.join(bake_path, root + ".jpg")
                        img.filepath_raw = new_path
                        img.save()
                    else:
                        if not os.path.normcase(os.path.realpath(bake_path)) in os.path.normcase(os.path.realpath(img.filepath)):
                            dir, file = os.path.split(img.filepath)
                            new_path = os.path.join(bake_path, file)
                            img.filepath_raw = new_path
                            img.save()
                            img.reload()
            except:
                print("ERROR")

        return {"FINISHED"}

    @classmethod
    def description(cls, context, properties):
        return "Makes all suitable texture maps jpegs and puts them all in the bake folder."


class CC3BakePanel(bpy.types.Panel):
    bl_idname = "CC3_PT_Bake_Panel"
    bl_label = "Bake"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3 Bake"

    def draw_size_props(self, context, props, bake_maps, col_1, col_2):

        if props.target_mode == "UNITY_HDRP":
            col_1.label(text="Diffuse Size")
            col_2.prop(props, "diffuse_size", text="")
            col_1.label(text="Mask Size")
            col_2.prop(props, "mask_size", text="")
            col_1.label(text="Detail Size")
            col_2.prop(props, "detail_size", text="")
            col_1.label(text="Normal Size")
            col_2.prop(props, "normal_size", text="")
            col_1.separator()
            col_2.separator()
            col_1.label(text="Emission Size")
            col_2.prop(props, "emissive_size", text="")
            col_1.label(text="SSS Size")
            col_2.prop(props, "sss_size", text="")
            col_1.label(text="Transmission Size")
            col_2.prop(props, "thickness_size", text="")

        else:
            if "Diffuse" in bake_maps:
                col_1.label(text="Diffuse Size")
                col_2.prop(props, "diffuse_size", text="")
            if "AO" in bake_maps:
                col_1.label(text="AO Size")
                col_2.prop(props, "ao_size", text="")
            if "Subsurface" in bake_maps:
                col_1.label(text="SSS Size")
                col_2.prop(props, "sss_size", text="")
            if "Thickness" in bake_maps:
                col_1.label(text="Thickness Size")
                col_2.prop(props, "thickness_size", text="")
            if "Metallic" in bake_maps:
                col_1.label(text="Metallic Size")
                col_2.prop(props, "metallic_size", text="")
            if "Specular" in bake_maps:
                col_1.label(text="Specular Size")
                col_2.prop(props, "specular_size", text="")
            if "Roughness" in bake_maps:
                col_1.label(text="Roughness Size")
                col_2.prop(props, "roughness_size", text="")
            if "Emission" in bake_maps:
                col_1.label(text="Emission Size")
                col_2.prop(props, "emissive_size", text="")
            if "Alpha" in bake_maps:
                col_1.label(text="Alpha Size")
                col_2.prop(props, "alpha_size", text="")
            if "Transmission" in bake_maps:
                col_1.label(text="Transmission Size")
                col_2.prop(props, "transmission_size", text="")
            if "Normal" in bake_maps:
                col_1.label(text="Normal Size")
                col_2.prop(props, "normal_size", text="")
            if "Bump" in bake_maps:
                col_1.label(text="Bump Size")
                col_2.prop(props, "bump_size", text="")
            if "MicroNormal" in bake_maps:
                col_1.label(text="Micro Normal Size")
                col_2.prop(props, "micronormal_size", text="")
            if "MicroNormalMask" in bake_maps:
                col_1.label(text="Micro Normal Mask Size")
                col_2.prop(props, "micronormalmask_size", text="")

    def draw(self, context):
        props = bpy.context.scene.CC3BakeProps

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        addon_updater_ops.check_for_update_background()
        if addon_updater_ops.updater.update_ready == True:
            addon_updater_ops.update_notice_box_ui(self, context)

        box = layout.box()
        box.label(text=f"Bake Settings  ({vars.VERSION_STRING})", icon="TOOL_SETTINGS")

        bake_maps = vars.get_bake_target_maps(props.target_mode)

        split = layout.split(factor=0.5)
        col_1 = split.column()
        col_2 = split.column()
        col_1.label(text="Target")
        col_2.prop(props, "target_mode", text="", slider = True)
        col_1.label(text="Bake Samples")
        col_2.prop(props, "bake_samples", text="", slider = True)
        col_1.label(text="Format")
        col_2.prop(props, "target_format", text="", slider = True)
        if props.target_format == "JPEG":
            col_1.label(text="JPEG Quality")
            col_2.prop(props, "jpeg_quality", text="", slider = True)
        if props.target_format == "PNG":
            col_1.label(text="PNG Compression")
            col_2.prop(props, "png_compression", text="", slider = True)
        col_1.label(text="Max Size")
        col_2.prop(props, "max_size", text="")
        #col_1.label(text="Scale Maps")
        #col_2.prop(props, "scale_maps", text="")
        if "Bump" in bake_maps:
            col_1.label(text="Allow Bump Maps")
            col_2.prop(props, "allow_bump_maps", text="")
        if "AO" in bake_maps:
            col_1.label(text="AO in Diffuse")
            col_2.prop(props, "ao_in_diffuse", text="", slider = True)
        if props.target_mode == "UNITY_HDRP" or props.target_mode == "UNITY_URP":
            col_1.label(text="Smoothness Mapping")
            col_2.prop(props, "smoothness_mapping", text="")
        if props.target_mode == "GLTF":
            col_1.label(text="Pack GLTF")
            col_2.prop(props, "pack_gltf", text="")
        col_1.label(text="Bake Folder")
        col_2.prop(props, "bake_path", text="")
        col_1.separator()
        col_2.separator()

        col_1.label(text="Max Sizes By Type")
        col_2.prop(props, "custom_sizes", text="")

        obj = context.object
        mat = context_material(context)
        bake_cache = get_bake_cache(mat)

        if props.custom_sizes:

            layout.row().box().label(text = "Maximum Texture Sizes")

            split = layout.split(factor=0.5)
            col_1 = split.column()
            col_2 = split.column()

            self.draw_size_props(context, props, bake_maps, col_1, col_2)

            if obj is not None:
                row = layout.row()
                row.template_list("MATERIAL_UL_weightedmatslots", "", obj, "material_slots", obj, "active_material_index", rows=1)

            if bake_cache and bake_cache.source_material != mat:
                mat_settings = get_material_settings(bake_cache.source_material)
                row = layout.row()
                row.label(text = "(*Source Material Settings)")
            else:
                mat_settings = get_material_settings(mat)

            if mat_settings is not None:
                row = layout.row()
                row.operator("cc3.bakesettings", icon="REMOVE", text="Remove Material Settings").param = "REMOVE"

                split = layout.split(factor=0.5)
                col_1 = split.column()
                col_2 = split.column()

                self.draw_size_props(context, mat_settings, bake_maps, col_1, col_2)

            else:
                row = layout.row()
                row.operator("cc3.bakesettings", icon="ADD", text="Add Material Settings").param = "ADD"

        if bake_cache:
            if bake_cache.source_material == mat:
                row = layout.row()
                row.operator("cc3.bakesettings", icon="LOOP_FORWARDS", text="Restore Baked Materials").param = "BAKED"
            elif bake_cache.baked_material == mat:
                row = layout.row()
                row.operator("cc3.bakesettings", icon="LOOP_BACK", text="Revert Source Materials").param = "SOURCE"

        row = layout.row()
        row.scale_y = 2
        row.operator("cc3.baker", icon="PLAY", text="Bake").param = "BAKE"


class CC3BakeUtilityPanel(bpy.types.Panel):
    bl_idname = "CC3_PT_BakeUtility_Panel"
    bl_label = "Utilities"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "CC3 Bake"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        props = bpy.context.scene.CC3BakeProps

        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False

        row = layout.row()
        row.scale_y = 2
        row.operator("cc3.jpegify", icon="PLAY", text="Jpegify")


class CC3BakeCache(bpy.types.PropertyGroup):
    uid: bpy.props.IntProperty(default=0)
    object: bpy.props.PointerProperty(type=bpy.types.Object)
    source_material: bpy.props.PointerProperty(type=bpy.types.Material)
    baked_material: bpy.props.PointerProperty(type=bpy.types.Material)


class CC3BakeMaterialSettings(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(type=bpy.types.Material)
    max_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="4096")
    diffuse_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    ao_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    sss_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    transmission_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    thickness_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    metallic_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    specular_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    roughness_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    emissive_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    alpha_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    normal_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="4096")
    micronormal_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    micronormalmask_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    bump_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    mask_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    detail_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")


class CC3BakeProps(bpy.types.PropertyGroup):
    auto_increment: bpy.props.IntProperty(default=100)
    jpeg_quality: bpy.props.IntProperty(default=90, min=0, max=100)
    png_compression: bpy.props.IntProperty(default=15, min=0, max=100)

    target_mode: bpy.props.EnumProperty(items=vars.BAKE_TARGETS, default="BLENDER")

    target_format: bpy.props.EnumProperty(items=vars.TARGET_FORMATS, default="JPEG")

    bake_samples: bpy.props.IntProperty(default=5, min=1, max=64, description="The number of texture samples per pixel to bake. As there are no ray traced effects involved, 1 to 5 samples is usually enough.")
    ao_in_diffuse: bpy.props.FloatProperty(default=0, min=0, max=1, description="How much of the ambient occlusion to bake into the diffuse")

    smoothness_mapping: bpy.props.EnumProperty(items=vars.CONVERSION_FUNCTIONS, default="IR", description="Roughness to smoothness calculation")

    allow_bump_maps: bpy.props.BoolProperty(default=True, description="Allow separate Bump and Normal Maps")
    scale_maps: bpy.props.BoolProperty(default=False)
    pack_gltf: bpy.props.BoolProperty(default=True, description="Pack AO, Roughness and Metallic into a single Texture for GLTF")

    custom_sizes: bpy.props.BoolProperty(default=False)
    max_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="4096")
    diffuse_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    ao_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    sss_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    transmission_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    thickness_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    metallic_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    specular_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    roughness_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    emissive_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    alpha_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    normal_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="4096")
    micronormal_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    micronormalmask_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="1024")
    bump_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    mask_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")
    detail_size: bpy.props.EnumProperty(items=vars.TEX_LIST, default="2048")

    bake_path: bpy.props.StringProperty(default="Bake", subtype="DIR_PATH")
    material_settings: bpy.props.CollectionProperty(type=CC3BakeMaterialSettings)
    bake_cache: bpy.props.CollectionProperty(type=CC3BakeCache)


class MATERIAL_UL_weightedmatslots(bpy.types.UIList):
    def draw_item(self, _context, layout, _data, item, icon, _active_data, _active_propname, _index):
        slot = item
        ma = slot.material
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            if ma:
                layout.prop(ma, "name", text="", emboss=False, icon_value=icon)
            else:
                layout.label(text="", icon_value=icon)
        elif self.layout_type == 'GRID':
            layout.alignment = 'CENTER'
            layout.label(text="", icon_value=icon)

