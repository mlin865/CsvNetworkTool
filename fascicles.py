import os
import networkx as nx

from cmlibs.zinc.context import Context
from cmlibs.zinc.field import Field, FieldGroup
from cmlibs.zinc.node import Node
from cmlibs.zinc.element import Element, Elementbasis

from cmlibs.utils.zinc.field import find_or_create_field_coordinates, findOrCreateFieldGroup, find_or_create_field_finite_element


def find_trunk_fascicle_file_for_segment(fascicle_path, segment_name, trunk_group_name):
    """
    :param fascicle_path: path to the folder containing fascicles graphml files
    :param segment_name: name of the dataset segment (i.e. SR005-CL1)
    :param trunk_group_name: name of the trunk group used in that segment
    :return: path to the graphml file with trunk fascicle data for that segment
    """

    fascicle_file_path = None
    if os.path.isdir(fascicle_path):
        fascicle_file_path = None
        trunk_keywords = trunk_group_name.split()
        for rootpath, dirs, files in os.walk(fascicle_path):
            for f in files:
                if all([trunk_keyword in f for trunk_keyword in trunk_keywords]) and (segment_name in f) and f.endswith('.graphml'):
                    fascicle_file_path = os.path.join(rootpath, f)
                    break
    return fascicle_file_path


def read_fascicle_file_into_region(fascicle_path, segment_name, output_path):
    """
    :param fascicle_path: path to the graphml file with trunk fascicle data for that segment
    :param segment_name: name of the dataset segment (i.e. SR005-CL1)
    :param output_path: path to the folder where to save the output results
    :return: path to file with Zinc region with nodes and elements from fascicle group.
    """

    G = nx.read_graphml(fascicle_path)

    labels = []
    internal_labels = []
    x_nodes = []
    y_nodes = []
    z_nodes = []

    x_node_coords = nx.get_node_attributes(G, "centroid-0")
    y_node_coords = nx.get_node_attributes(G, "centroid-1")
    z_node_coords = nx.get_node_attributes(G, "frame")

    for node in G.nodes(data=True):
        labels.append(node[0]) # node id
        internal_labels.append(node[1]['label'])
        x_nodes.append(node[1]['centroid-0'])
        y_nodes.append(node[1]['centroid-1'])
        z_nodes.append(node[1]['frame'])

    # need to fill these with x, y, z coordinates
    x_edges = []
    y_edges = []
    z_edges = []

    for edge in G.edges(data=True):
        # format: [beginning, ending, None]
        x_coords = [x_node_coords[edge[0]], x_node_coords[edge[1]], None]
        x_edges += x_coords

        y_coords = [y_node_coords[edge[0]], y_node_coords[edge[1]], None]
        y_edges += y_coords

        z_coords = [z_node_coords[edge[0]], z_node_coords[edge[1]], None]
        z_edges += z_coords

    # create region containing fascicles data
    context = Context("fascicles")
    fascicles_region = context.getDefaultRegion()
    fieldmodule = fascicles_region.getFieldmodule()
    fieldcache = fieldmodule.createFieldcache()

    # add nodes to zinc region
    nodes = fieldmodule.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
    coordinates = find_or_create_field_coordinates(fieldmodule)
    radius = find_or_create_field_finite_element(fieldmodule, "radius", 1, managed=True)

    nodetemplate = nodes.createNodetemplate()
    nodetemplate.defineField(coordinates)
    nodetemplate.defineField(radius)
    nodetemplate.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_VALUE, 1)
    nodetemplate.setValueNumberOfVersions(radius, -1, Node.VALUE_LABEL_VALUE, 1)

    mesh1d = fieldmodule.findMeshByDimension(1)
    linear_basis = fieldmodule.createElementbasis(1, Elementbasis.FUNCTION_TYPE_LINEAR_LAGRANGE)
    eft = mesh1d.createElementfieldtemplate(linear_basis)
    elementtemplate = mesh1d.createElementtemplate()
    elementtemplate.setElementShapeType(Element.SHAPE_TYPE_LINE)
    elementtemplate.defineField(coordinates, -1, eft)
    elementtemplate.defineField(radius, -1, eft)

    graph_node_to_node_map = {}

    node_identifier = 500000
    for node in G.nodes(data=True):
        label = node[0]
        graph_node_to_node_map[label] = node_identifier

        point = [
            node[1]['centroid-0'],
            node[1]['centroid-1'],
            node[1]['frame']]
        point_radius = node[1]['equivalent_diameter'] / 2

        node = nodes.createNode(node_identifier, nodetemplate)
        fieldcache.setNode(node)
        coordinates.setNodeParameters(fieldcache, -1, Node.VALUE_LABEL_VALUE, 1, point)
        radius.setNodeParameters(fieldcache, -1, Node.VALUE_LABEL_VALUE, 1, point_radius)
        node_identifier += 1

    fascicle_field_group = findOrCreateFieldGroup(fieldmodule, 'fascicle')
    fascicle_field_group.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)
    fascicle_mesh_group = fascicle_field_group.getOrCreateMeshGroup(mesh1d)

    element_identifier = 500000
    for edge in G.edges(data=True):
        nids = [
            graph_node_to_node_map[edge[0]],
            graph_node_to_node_map[edge[1]]]

        element = mesh1d.createElement(element_identifier, elementtemplate)
        element.setNodesByIdentifier(eft, nids)
        fascicle_mesh_group.addElement(element)
        element_identifier += 1

    fascicle_output_path = os.path.join(output_path, 'fascicles-' + segment_name + '.exf')
    fascicles_region.writeFile(fascicle_output_path)

    return fascicle_output_path


