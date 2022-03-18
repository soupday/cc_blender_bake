import bpy
from . import utils, vars

NODE_PREFIX = "cc3iid_"

def get_bsdf_node(nodes):
    for n in nodes:
        if n.type == "BSDF_PRINCIPLED":
            return n
    return None


def get_shader_node(nodes):
    for n in nodes:
        if n.type == "GROUP" and "(rl_" in n.name and "_shader)" in n.name:
            name = n.node_tree.name
            if NODE_PREFIX in name and "_rl_" in name and "_shader_" in name:
                return n
    return None


def get_shader_input(nodes, input):
    shader = get_shader_node(nodes)
    if shader and input in shader.inputs:
        socket = shader.inputs[input]

    return None


def is_connected(node : bpy.types.Node, socket):
    if node and socket in node.inputs:
        return node.inputs[socket].is_linked


def is_mixer_connected(node : bpy.types.Node, socket):
    mixer = get_node_connected_to_input(node, socket)
    if mixer and mixer.type == "GROUP":
        if NODE_PREFIX in mixer.name and "rl_mixer" in mixer.name:
            return True
    return False


def get_sockets_connected_to_output(node, socket):
    try:
        sockets = []
        for link in node.outputs[socket].links:
            sockets.append(link.to_socket.name)
        return sockets
    except:
        return None

def get_socket_connected_to_input(node, socket):
    try:
        return node.inputs[socket].links[0].from_socket.name
    except:
        return None

def get_nodes_connected_to_output(node, socket):
    try:
        nodes = []
        for link in node.outputs[socket].links:
            nodes.append(link.to_node)
        return nodes
    except:
        return None

def get_node_connected_to_input(node, socket):
    try:
        return node.inputs[socket].links[0].from_node
    except:
        return None

def get_node_by_id(nodes, id):
    id = NODE_PREFIX + id
    for node in nodes:
        if id in node.name:
            return node
    return None


def get_default_shader_input(mat, input):
    if mat.node_tree is not None:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                if input in n.inputs:
                    return n.inputs[input].default_value
    return 0.0


def find_node_by_keywords(nodes, *keywords):
    for node in nodes:
        match = True
        for keyword in keywords:
            if not keyword in node.name:
                match = False
        if match:
            return node
    return None

def find_node_by_type(nodes, type):
    for n in nodes:
        if n.type == type:
            return n


def get_node_input(node, input, default):
    if node is not None:
        try:
            return node.inputs[input].default_value
        except:
            return default
    return default

def get_node_output(node, output, default):
    if node is not None:
        try:
            return node.outputs[output].default_value
        except:
            return default
    return default

def set_node_input(node, socket, value):
    if node is not None:
        try:
            node.inputs[socket].default_value = value
        except:
            utils.log_info("Unable to set input: " + node.name + "[" + str(socket) + "]")

def set_node_output(node, socket, value):
    if node is not None:
        try:
            node.outputs[socket].default_value = value
        except:
            utils.log_info("Unable to set output: " + node.name + "[" + str(socket) + "]")

def link_nodes(links, from_node, from_socket, to_node, to_socket):
    if from_node is not None and to_node is not None:
        try:
            links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])
        except:
            utils.log_info("Unable to link: " + from_node.name + "[" + str(from_socket) + "] to " +
                  to_node.name + "[" + str(to_socket) + "]")

def unlink_node(links, node, socket):
    if node is not None:
        try:
            socket_links = node.inputs[socket].links
            for link in socket_links:
                if link is not None:
                    links.remove(link)
        except:
            utils.log_info("Unable to remove links from: " + node.name + "[" + str(socket) + "]")


def make_shader_node(nodes, type):
    shader_node = nodes.new(type)
    return shader_node

def make_mixrgb_node(nodes, blend_type):
    mix_node = make_shader_node(nodes, "ShaderNodeMixRGB")
    mix_node.blend_type = blend_type
    return mix_node

def make_math_node(nodes, operation, value1 = 0.5, value2 = 0.5):
    math_node = make_shader_node(nodes, "ShaderNodeMath")
    math_node.operation = operation
    math_node.inputs[0].default_value = value1
    math_node.inputs[1].default_value = value2
    return math_node

def make_node_group_node(nodes, group, label, name):
    group_node = make_shader_node(nodes, "ShaderNodeGroup")
    group_node.node_tree = group
    group_node.label = label
    group_node.width = 240
    group_node.name = name
    return group_node

def find_image_node(nodes, name_search, file_search):
    for node in nodes:
        if node.type == "TEX_IMAGE":
            if name_search == "" and file_search != "" and file_search in node.image.filepath:
                return node
            elif file_search == "" and name_search != "" and name_search in node.name:
                return node
            elif file_search != "" and name_search != "" and name_search in node.name and file_search in node.image.filepath:
                return node
    return None

def find_shader_texture(nodes, texture_type):
    id = "(" + texture_type + ")"
    for node in nodes:
        if node.type == "TEX_IMAGE" and NODE_PREFIX in node.name and id in node.name:
            return node
    return None

## color_space: Non-Color, sRGB
def make_image_node(nodes, image):
    if image is None:
        return None
    image_node = make_shader_node(nodes, "ShaderNodeTexImage")
    image_node.image = image
    return image_node


def make_gltf_settings_node(nodes):
    gltf_group : bpy.types.NodeGroup = None
    for group in bpy.data.node_groups:
        if group.name == "glTF Settings":
            gltf_group = group
    if not gltf_group:
        gltf_group = bpy.data.node_groups.new("glTF Settings", "ShaderNodeTree")
        gltf_group.inputs.new("NodeSocketColor", "Occlusion")
    return make_node_group_node(nodes, gltf_group, "glTF Settings", "glTF Settings")


# class to show node coords in shader editor...
class CC3NodeCoord(bpy.types.Panel):
    bl_label = "Node Coordinates panel"
    bl_idname = "CC3I_PT_NodeCoord"
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"

    def draw(self, context):
        if context.active_node is not None:
            layout = self.layout
            layout.separator()
            row = layout.box().row()
            coords = context.active_node.location
            row.label(text=str(int(coords.x/10)*10) + ", " + str(int(coords.y/10)*10))
            row.label(text=str(int(coords.x)) + ", " + str(int(coords.y)))