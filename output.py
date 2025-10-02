from cmlibs.zinc.context import Context
from cmlibs.zinc.field import Field, FieldGroup
from cmlibs.zinc.node import Node
from cmlibs.zinc.element import Element, Elementbasis, Elementfieldtemplate

from cmlibs.utils.zinc.field import findOrCreateFieldCoordinates, findOrCreateFieldStoredString, findOrCreateFieldGroup, \
    find_or_create_field_finite_element
from cmlibs.utils.zinc.group import group_add_group_local_contents


def write_exf(output_file, marker_data, trunk_group_name, trunk_coordinates, trunk_radius,
              branch_names, branch_coordinates_data, branch_parent_indices, avg_branch_radius,
              orientation_markers, vagus_terms, fascicles_region_path):
    """
    :param output_file: location of the output file
    :param marker_data: dict mapping marker names to marker coordinates
    :param trunk_group_name: name used for trunk group
    :param trunk_coordinates: list with x, y, z trunk coordinates
    :param branch_names: list with names of the branches, sorted from first level to second level, etc.
    :param branch_coordinates_data: dictionary mapping branch name to list with x, y, z branch coordinates
    :param branch_parent_indices: dictionary mapping branch name to
        (parent branch name, index of parent coordinate where branch links to the parent)
    :param orientation_markers: dictionary mapping 8 orientations to list of x, y, z coordinates used for orientation
    :param vagus_terms: dictionary mapping branch name to annotation term
    :param fascicles_region_path: path to file with Zinc region with nodes and elements from fascicle group
    """

    # writing out data as a single exf file
    # set up zinc region
    context = Context("data_region")
    data_region = context.getDefaultRegion()
    fieldmodule = data_region.getFieldmodule()
    fieldcache = fieldmodule.createFieldcache()

    # set up and templates
    nodes = fieldmodule.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
    datapoints = fieldmodule.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_DATAPOINTS)

    coordinates = findOrCreateFieldCoordinates(fieldmodule).castFiniteElement()
    marker_names = findOrCreateFieldStoredString(fieldmodule, name="marker_name")

    dnodetemplate = datapoints.createNodetemplate()
    dnodetemplate.defineField(coordinates)
    dnodetemplate.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_VALUE, 1)
    dnodetemplate.defineField(marker_names)

    nodetemplate = nodes.createNodetemplate()
    nodetemplate.defineField(coordinates)
    nodetemplate.setValueNumberOfVersions(coordinates, -1, Node.VALUE_LABEL_VALUE, 1)

    mesh1d = fieldmodule.findMeshByDimension(1)
    linear_basis = fieldmodule.createElementbasis(1, Elementbasis.FUNCTION_TYPE_LINEAR_LAGRANGE)
    eft = mesh1d.createElementfieldtemplate(linear_basis)
    elementtemplate = mesh1d.createElementtemplate()
    elementtemplate.setElementShapeType(Element.SHAPE_TYPE_LINE)
    elementtemplate.defineField(coordinates, -1, eft)

    if len(trunk_radius) > 0:
        radius = find_or_create_field_finite_element(fieldmodule, "radius", 1, managed=True)
        nodetemplate.defineField(radius)
        nodetemplate.setValueNumberOfVersions(radius, -1, Node.VALUE_LABEL_VALUE, 1)
        elementtemplate.defineField(radius, -1, eft)

    # add markers to zinc region
    marker_fieldgroup = findOrCreateFieldGroup(fieldmodule, 'marker')
    marker_nodesetgroup = marker_fieldgroup.createNodesetGroup(datapoints)

    marker_node_identifier = 1
    for marker_name, marker_point in marker_data.items():
        node = datapoints.createNode(marker_node_identifier, dnodetemplate)
        fieldcache.setNode(node)
        coordinates.setNodeParameters(fieldcache, -1, Node.VALUE_LABEL_VALUE, 1, marker_point)
        marker_names.assignString(fieldcache, marker_name)
        marker_nodesetgroup.addNode(node)
        marker_node_identifier += 1

    # add nodes to zinc region
    node_identifier = 1
    element_identifier = 1

    # rename trunk group - temporarily
    # if 'left' in trunk_group_name:
    #     trunk_group_name = 'left vagus nerve'
    # else:
    #     trunk_group_name = 'right vagus nerve'

    # add trunk nodes
    trunk_field_group = findOrCreateFieldGroup(fieldmodule, trunk_group_name)
    trunk_field_group.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)
    trunk_mesh_group = trunk_field_group.getOrCreateMeshGroup(mesh1d)

    group_start_nodes = dict()
    group_start_nodes[trunk_group_name] = node_identifier
    for index, trunk_point in enumerate(trunk_coordinates):
        node = nodes.createNode(node_identifier, nodetemplate)
        fieldcache.setNode(node)
        coordinates.setNodeParameters(fieldcache, -1, Node.VALUE_LABEL_VALUE, 1, trunk_point)
        if len(trunk_radius) > 0:
            radius.setNodeParameters(fieldcache, -1, Node.VALUE_LABEL_VALUE, 1, trunk_radius[index])

        if index > 0:
            element = mesh1d.createElement(element_identifier, elementtemplate)
            element.setNodesByIdentifier(eft, [node_identifier - 1, node_identifier])
            trunk_mesh_group.addElement(element)
            element_identifier += 1
        node_identifier += 1

    if vagus_terms and trunk_group_name in vagus_terms.keys():
        trunk_term_group = findOrCreateFieldGroup(fieldmodule, vagus_terms[trunk_group_name])
        group_add_group_local_contents(trunk_term_group, trunk_field_group)

    # add branch nodes
    for branch_name in branch_names:
        branch_coordinates = branch_coordinates_data[branch_name]

        branch_field_group = findOrCreateFieldGroup(fieldmodule, branch_name)
        branch_field_group.setSubelementHandlingMode(FieldGroup.SUBELEMENT_HANDLING_MODE_FULL)
        branch_mesh_group = branch_field_group.getOrCreateMeshGroup(mesh1d)

        # used for temporary stitching
        group_start_nodes[branch_name] = node_identifier
        parent_name, parent_index = branch_parent_indices[branch_name]

        for index, branch_point in enumerate(branch_coordinates):
            node = nodes.createNode(node_identifier, nodetemplate)
            fieldcache.setNode(node)
            coordinates.setNodeParameters(fieldcache, -1, Node.VALUE_LABEL_VALUE, 1, branch_point)
            if avg_branch_radius:
                radius.setNodeParameters(fieldcache, -1, Node.VALUE_LABEL_VALUE, 1, avg_branch_radius)

            nids = None
            if parent_index is not None:
                if index == 0:
                    # get parent node id to add to branch group
                    parent_node_id = group_start_nodes[parent_name] + parent_index
                    if parent_index > 1:
                        # trunk is not a parent group
                        parent_node_id -= 1

                    # print(branch_name, '->', parent_name, group_start_nodes[parent_name], parent_index)
                    nids = [parent_node_id, node_identifier]
                else:
                    nids = [node_identifier - 1, node_identifier]
            else:
                if index > 0:
                    nids = [node_identifier - 1, node_identifier]

            if nids:
                element = mesh1d.createElement(element_identifier, elementtemplate)
                element.setNodesByIdentifier(eft, nids)
                branch_mesh_group.addElement(element)
                element_identifier += 1
            node_identifier += 1

        if vagus_terms and branch_name in vagus_terms.keys():
            branch_term_group = findOrCreateFieldGroup(fieldmodule, vagus_terms[branch_name])
            group_add_group_local_contents(branch_term_group, branch_field_group)

    # add orientation markers
    if orientation_markers:
        for orientation_marker, orientation_points in orientation_markers.items():
            orientation_fieldgroup = findOrCreateFieldGroup(fieldmodule, orientation_marker)
            orientation_nodesetgroup = orientation_fieldgroup.createNodesetGroup(nodes)

            for orientation_point in orientation_points:
                node = nodes.createNode(node_identifier, nodetemplate)
                fieldcache.setNode(node)
                coordinates.setNodeParameters(fieldcache, -1, Node.VALUE_LABEL_VALUE, 1, orientation_point)
                orientation_nodesetgroup.addNode(node)
                node_identifier += 1

    # add fascicles data
    if fascicles_region_path:
        data_region.readFile(fascicles_region_path)

    # write all data in one exf file
    sir = data_region.createStreaminformationRegion()
    srf = sir.createStreamresourceFile(output_file)
    result = data_region.write(sir)
