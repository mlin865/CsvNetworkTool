import os
import re
import csv

from cmlibs.maths.vectorops import magnitude_squared, sub

from annotations import load_approved_vagus_marker_terms


trunk_keywords = ['left cervical trunk', 'right cervical trunk', 'left thoracic trunk', 'right thoracic trunk',
                  'left vagus nerve', 'right vagus nerve']
branch_keywords = ['branch', 'nerve']
non_vagus_branches_keywords = [
    'carotid sinus nerve',
    'glossopharyngeal nerve',
    'hypoglossal nerve',
    'spinal accessory nerve',
    'superior root of ansa cervicalis',
    'cervical sympathetic trunk'
]


def find_tracing_csv_files(microct_path):
    """
    :param microct_path: path to the folder with csv segmentation files
    :return: Dict mapping segment name to list of csv files paths
    """

    segment_files = {}
    if os.path.isdir(microct_path):
        # find csv segmentation files in the supplied folder
        segment_paths = [f.path for f in os.scandir(microct_path) if f.is_dir()]
        for segment_path in segment_paths:
            segment_name = os.path.basename(os.path.normpath(segment_path))

            # find all csv files in a given segment
            csv_files = []
            for rootpath, dirs, files in os.walk(segment_path):
                files_to_add = [os.path.join(rootpath, f) for f in files if f.endswith('.csv')]
                csv_files.extend(files_to_add)

            if len(csv_files) > 0:
                segment_files[segment_name] = csv_files

    return segment_files


def branch_is_non_vagal(group_name, side_label):
    """
    :param group_name: name of the branch.
    :param side_label: left or right
    :return: True if the branch is non vagus structure, False otherwise (is part of vagus)
    """

    branch_name = group_name.replace(side_label + ' ', '', 1)

    for keyword in non_vagus_branches_keywords:
        if branch_name == keyword:
            # exact match -> not vagus
            return True

        if re.search(rf'branch[A-Z a-z]* of {re.escape(keyword)}', branch_name):
            # "branch X of <keyword>" -> not vagus
            return True

        if re.search(rf'branch (of [^ ]+ )?to {re.escape(keyword)}', branch_name):
            # "branch to <keyword>" or "branch of ... to <keyword>" -> vagus
            return False

    return False


def suggest_parent_name(branch_name, side_label, trunk_group_name):
    """
    :param branch_name: name of branch.
    :param side_label: left or right.
    :param trunk_group_name: name of trunk.
    :return string extracted from branch_name that could potentially indicate parent branch.
    """

    match = re.search(r'branch', branch_name)
    if match:
        index = match.end()
        remaining_text = branch_name[index:].strip()
        # print('  ', remaining_text)

        if re.search(r'[A-Z a-z]*to [A-Z a-z]*branch[A-Z a-z]* of', remaining_text):
            # "branch X to branch of other branch"
            try_parent_name = trunk_group_name
        elif re.search(r'^[A-Z a-z]{0,2}of', remaining_text):
            # "branch X of other branch"
            try_parent_name = re.sub(r'.*?branch[A-Z a-z]* of', '', branch_name).strip()
        elif re.search(r'.*?[A-Z a-z]*to', remaining_text):
            # "branch to destination"
            try_parent_name = trunk_group_name
        else:
            # "branch X" or "some branch" or similar
            try_parent_name = trunk_group_name
    else:
        # no "branch" keyword
        try_parent_name = trunk_group_name

    if not try_parent_name.startswith(side_label):
        try_parent_name = side_label + ' ' + try_parent_name

    return try_parent_name


def read_segment_csv_files(csv_files):
    """
    :param csv_files: List with paths to csv files.
    :return:
        marker_data: Dict mapping marker name to marker x, y, z coordinate.
        trunk_group_name: Name used for trunk group.
        trunk_coordinates: List of x, y, z coordinates for trunk group.
        branch_coordinates_data: Dict mapping branch name to list of branch x, y, z coordinates.
    """

    marker_data = {}
    trunk_group_name = None
    branch_group_names = []
    trunk_coordinates = []
    branch_coordinates_data = {}

    side_label = 'left' if 'CL' in csv_files[0] or 'TL' in csv_files[0] else 'right'
        
    vagus_marker_terms = load_approved_vagus_marker_terms()

    # read data from all csv files 
    for csv_file in csv_files:
        group_name = csv_file.split('-')[-1].split('.')[0].replace('_', ' ')
        
        if group_name == 'vagal levels':
            # read markers file
            with open(csv_file, 'r') as csvfile:
                plots = csv.reader(csvfile, delimiter=',')
                next(plots, None)  # skip the headers
                for row in plots: 
                    marker_name = row[0]
                    if marker_name not in vagus_marker_terms.keys(): 
                        # correct marker name
                        marker_name = marker_name + ' on the vagus nerve'
                        if marker_name not in vagus_marker_terms.keys():
                            # ignore marker if not in the list
                            continue
                    marker_point = [float(row[3]), float(row[2]), float(row[1])]
                    marker_data[marker_name] = marker_point
        else:
            # read trunk / branches file
            coordinates = []       
            with open(csv_file, 'r') as csvfile:
                plots = csv.reader(csvfile, delimiter=',')
                next(plots, None)  # skip headers
                for row in plots:
                    # read z, y, x coordinates
                    coordinates.append([float(row[3]), float(row[2]), float(row[1])])

            if any(keyword in group_name.lower() for keyword in trunk_keywords) and 'branch' not in group_name.lower():
                trunk_group_name = group_name
                trunk_coordinates = coordinates[:]

            # remove this condition to consider all branches (vagus/non-vagus)
            if any(keyword in group_name.lower() for keyword in branch_keywords) and group_name != trunk_group_name:
                # check if branch is a part of vagus
                if branch_is_non_vagal(group_name, side_label):
                    # ignore non vagus structures for now
                    print('Ignored non-vagal branch:', group_name)
                else:
                    branch_group_names.append(group_name)
                    branch_coordinates_data[group_name] = coordinates[:]
    
    return marker_data, trunk_group_name, trunk_coordinates, branch_coordinates_data
    

def process_segment_csv_files(csv_files, minimal_distance_allowed):
    """
    :param
        csv_files: List with paths to csv files.
        minimal_distance_allowed: tolerance used for branch stitching
    :return:
        marker_data: Dict mapping marker name to marker x, y, z coordinate.
        trunk_group_name: Name used for trunk group.
        trunk_coordinates: List of x, y, z coordinates for trunk group.
        branches_names_sorted: list with names of the branches, sorted from first level to second level, etc.
        branch_coordinates_data: dictionary mapping branch name to list with x, y, z branch coordinates
        branch_parent_indices: dictionary mapping branch name to
            (parent branch name, index of parent coordinate where branch links to the parent)
    """

    side_label = 'left' if 'CL' in csv_files[0] or 'TL' in csv_files[0] else 'right'
    marker_data, trunk_group_name, trunk_coordinates, branch_coordinates_data = read_segment_csv_files(csv_files)

    # sort branches (first level, followed by second level branches)
    second_level_branch_pattern = r'.*?branch[A-Z a-z]* of'
    first_level_branches = [branch_name for branch_name in branch_coordinates_data.keys()
                            if not re.search(second_level_branch_pattern, branch_name.lower())]
    second_level_branches = [branch_name for branch_name in branch_coordinates_data.keys()
                             if re.search(second_level_branch_pattern, branch_name.lower())]
    branches_names_sorted = first_level_branches + second_level_branches

    # find parent (trunk or other branch) and parent point closest to branch
    branch_parent_indices = {}
    for branch_name in branches_names_sorted:
        branch_coordinates = branch_coordinates_data[branch_name]

        # assumes that branches coordinates are recorded from start to end
        # ignores first branch point near trunk
        branch_start_point = branch_coordinates[1]
        branch_end_point = branch_coordinates[-1]

        # find parent branch
        try_parent_name = suggest_parent_name(branch_name, side_label, trunk_group_name)

        if try_parent_name != branch_name and try_parent_name in branch_coordinates_data.keys():
            parent_name = try_parent_name
            parent_coordinates = branch_coordinates_data[parent_name][:]
        else:
            # if parent is not a branch, use trunk as default parent
            parent_name = trunk_group_name
            parent_coordinates = trunk_coordinates[:]

        # find closest to branch distance, branch start, group node closest to the branch
        min_dsq = float('inf')
        for bi in [branch_start_point, branch_end_point]:
            for i in range(len(parent_coordinates)):
                parent_node = parent_coordinates[i]
                distance_squared = magnitude_squared(sub(parent_node, bi))
                if distance_squared <= min_dsq:
                    min_dsq = distance_squared
                    closest_branch_point = bi
                    closest_parent_index = i

        if min_dsq < minimal_distance_allowed:
            # print('  ', branch_name, '->', parent_name, closest_parent_index, min_dsq)

            # remove first branch node near trunk
            branch_coordinates.pop(0)
            # remember closest parent node index
            branch_parent_indices[branch_name] = (parent_name, closest_parent_index)

            if closest_branch_point == branch_end_point:
                # reverse list of coordinates if necessary so that the data always starts from parent
                print('  branch reversed')
                branch_coordinates.reverse()
            branch_coordinates_data[branch_name] = branch_coordinates

        else:
            # branch is too far away to be stitched
            print('  ', branch_name, 'has no parent, potentially looked at', parent_name, ', min_dsq =', str(min_dsq))
            branch_parent_indices[branch_name] = (None, None)

    return marker_data, trunk_group_name, trunk_coordinates, \
        branches_names_sorted, branch_coordinates_data, branch_parent_indices
