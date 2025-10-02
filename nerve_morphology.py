import os
import csv

from cmlibs.maths.vectorops import magnitude_squared, sub


def find_trunk_morphology_file_for_segment(nerve_morphology_path, segment_name, trunk_group_name):
    """
    :param nerve_morphology_path: path to the folder containing nerve morphology csv files
    :param segment_name: name of the dataset segment (i.e. SR005-CL1)
    :param trunk_group_name: name of the trunk group used in that segment
    :return: path to the csv file with trunk morphology data for that segment
    """

    if os.path.isdir(nerve_morphology_path):
        morphology_file_path = None
        trunk_keywords = trunk_group_name.split()
        for rootpath, dirs, files in os.walk(nerve_morphology_path):
            for f in files:
                if all([trunk_keyword in f for trunk_keyword in trunk_keywords]) and (segment_name in f) and f.endswith('.csv'):
                    morphology_file_path = os.path.join(rootpath, f)
                    break
    return morphology_file_path


def process_trunk_morphology_file_radius(morphology_file_path, trunk_coordinates):
    """
    :param morphology_file_path: path to the csv morphology file
    :param trunk_coordinates: list of x, y, z coordinates for trunk group.
    :return:
        trunk_radius: List of values for radius, associated with trunk coordinates.
        avg_trunk_radius: Average value from trunk_radius. Used later for estimating average branch radius.
    """

    coords_data = []
    radius_data = []
    with open(morphology_file_path, 'r') as csvfile:
        plots = csv.reader(csvfile, delimiter=',')
        next(plots, None)  # skip headers
        for row in plots:
            # 0, 1, 2, 3, 4, 5, 6, 7, 8
            # index,area,perimeter,eq_diameter,center_x,center_y,major_axis,minor_axis,angle
            if row[1] != '':
                coords_data.append([float(row[4]), float(row[5]), float(row[0])])
                # radius_data.append(min(float(row[6]), float(row[7])) / 2)
                radius_data.append(float(row[3]) / 2)

    trunk_radius = []
    for index, trunk_coordinate in enumerate(trunk_coordinates):
        # find the nearest trunk point for each point in the morphology data
        min_dsq = float('inf')
        for i in range(len(coords_data)):
            morphology_trunk_node = coords_data[i]
            distance_squared = magnitude_squared(sub(morphology_trunk_node, trunk_coordinate))
            if distance_squared <= min_dsq:
                min_dsq = distance_squared
                closest_morphology_node_index = i

        trunk_radius.append(radius_data[closest_morphology_node_index])

    avg_trunk_radius = sum(trunk_radius)/len(trunk_radius)
    return trunk_radius, avg_trunk_radius


