import os
import pandas as pd


def read_vagus_branching_pattern_spreadsheet(vagus_branching_pattern_file):
    """
    :param vagus_branching_pattern_file: Path to the spreadsheet with vagus branching pattern data
    :return: Dict mapping branch_name to branch_orientation label.
    """

    if not os.path.exists(vagus_branching_pattern_file):
        return {}, {}

    columns_to_read = ['Right or Left',
                       'Internal Termlist Name',
                       'Interlex ID',
                       'Branch (BR) or Subbranch (SB)',
                       'Branch point on vagus',
                       # 'Branch Target',
                       # 'Branch Direction Leaving Vagus'
                       ]

    df = pd.read_excel(vagus_branching_pattern_file, skiprows=1)
    df.columns = df.columns.str.strip()
    df['Branch point on vagus'] = df['Branch point on vagus'].apply(
        lambda x: x.lower().strip() if isinstance(x, str) else x)
    df['Branch (BR) or Subbranch (SB)'] = df['Branch (BR) or Subbranch (SB)'].apply(
        lambda x: x.capitalize().strip() if isinstance(x, str) else x)

    # filter useful columns
    filtered_df = df[columns_to_read]

    vagus_branch_terms = {k: v for k, v in zip(filtered_df['Internal Termlist Name'],
                                               filtered_df['Interlex ID']) if pd.notna(v)}

    # only use branches, not subbranches, for orientation data
    filtered_df = filtered_df.loc[(filtered_df['Branch (BR) or Subbranch (SB)'] == 'Br') |
                                  (filtered_df['Branch (BR) or Subbranch (SB)'] == 'Branch')]
    filtered_df = filtered_df.reset_index()

    vagus_orientations = {k: v for k, v in zip(filtered_df['Internal Termlist Name'],
                                 filtered_df['Branch point on vagus']) if pd.notna(v)}

    return vagus_orientations, vagus_branch_terms


def relabel_orientation(side, branch_orientation_label):
    """
    :param side: Left or right.
    :param branch_orientation_label:  One of the 8 orientation keywords.
    :return: Approved name for branch orientation level.
    """

    if branch_orientation_label == 'anterior':
        label_on_vagus = 'orientation anterior'

    elif branch_orientation_label == 'posterior':
        label_on_vagus = 'orientation posterior'

    elif branch_orientation_label == 'medial':
        if side == 'left':
            label_on_vagus = 'orientation right'
        elif side == 'right':
            label_on_vagus = 'orientation left'

    elif branch_orientation_label == 'lateral':
        if side == 'left':
            label_on_vagus = 'orientation left'
        elif side == 'right':
            label_on_vagus = 'orientation right'

    elif branch_orientation_label == 'anteromedial':
        if side == 'left':
            label_on_vagus = 'orientation right anterior'
        elif side == 'right':
            label_on_vagus = 'orientation left anterior'

    elif branch_orientation_label == 'anterolateral':
        if side == 'left':
            label_on_vagus = 'orientation left anterior'
        elif side == 'right':
            label_on_vagus = 'orientation right anterior'

    elif branch_orientation_label == 'posteromedial':
        if side == 'left':
            label_on_vagus = 'orientation right posterior'
        elif side == 'right':
            label_on_vagus = 'orientation left posterior'

    elif branch_orientation_label == 'posterolateral':
        if side == 'left':
            label_on_vagus = 'orientation left posterior'
        elif side == 'right':
            label_on_vagus = 'orientation right posterior'
    else:
        label_on_vagus = ''

    return label_on_vagus


def create_orientation_markers(branch_coordinates_data, vagus_orientations):
    """
    :param branch_coordinates_data: Dict mapping branch_name to branch_coordinates (list of XYZ points)
    :param vagus_orientations: Dict mapping branch_name to branch_orientation (str label from spreadsheet)
    :return: Dict mapping orientation_label to its X, Y, Z coordinate.
    """

    orientation_markers = {}
    for branch_name, branch_orientation in vagus_orientations.items():
        if branch_name in branch_coordinates_data.keys():
            side = 'left' if 'left' in branch_name else 'right'
            label_on_vagus = relabel_orientation(side, branch_orientation)

            branch_coordinates = branch_coordinates_data[branch_name]

            if label_on_vagus != '':
                d = 200.0  # chosen distance away from the first branch & trunk point
                marker_coordinate = branch_coordinates[0]
                if label_on_vagus in orientation_markers.keys():
                    orientation_markers[label_on_vagus].append(marker_coordinate)
                else:
                    orientation_markers[label_on_vagus] = [marker_coordinate]

    return orientation_markers
