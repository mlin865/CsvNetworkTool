import os
import pandas as pd


def load_approved_vagus_marker_terms():
    vagus_marker_terms = {
        # anatomical landmarks
        "level of superior border of jugular foramen on the vagus nerve": "ILX:0794617",
        "right level of superior border of jugular foramen on the vagus nerve": "ILX:0794618",
        "left level of superior border of jugular foramen on the vagus nerve": "ILX:0794619",
        "level of inferior border of jugular foramen on the vagus nerve": "ILX:0794620",
        "right level of inferior border of jugular foramen on the vagus nerve": "ILX:0794621",
        "left level of inferior border of jugular foramen on the vagus nerve": "ILX:0794622",
        "level of inferior border of cranium on the vagus nerve": "ILX:0794623",
        "right level of inferior border of cranium on the vagus nerve": "ILX:0794624",
        "left level of inferior border of cranium on the vagus nerve": "ILX:0794625",
        "level of C1 transverse process on the vagus nerve": "ILX:0794626",
        "right level of C1 transverse process on the vagus nerve": "ILX:0794627",
        "left level of C1 transverse process on the vagus nerve": "ILX:0794628",
        "level of greater horn of hyoid on the vagus nerve": "ILX:0794629",
        "right level of greater horn of hyoid on the vagus nerve": "ILX:0794630",
        "left level of greater horn of hyoid on the vagus nerve": "ILX:0794631",
        "level of laryngeal prominence on the vagus nerve": "ILX:0794632",
        "right level of laryngeal prominence on the vagus nerve": "ILX:0794633",
        "left level of laryngeal prominence on the vagus nerve": "ILX:0794634",
        "level of angle of the mandible on the vagus nerve": "ILX:0794635",
        "right level of angle of the mandible on the vagus nerve": "ILX:0794636",
        "left level of angle of the mandible on the vagus nerve": "ILX:0794637",
        "level of carotid bifurcation on the vagus nerve": "ILX:0794638",
        "right level of carotid bifurcation on the vagus nerve": "ILX:0794639",
        "left level of carotid bifurcation on the vagus nerve": "ILX:0794640",
        "level of superior border of the clavicle on the vagus nerve": "ILX:0794641",
        "right level of superior border of the clavicle on the vagus nerve": "ILX:0794642",
        "left level of superior border of the clavicle on the vagus nerve": "ILX:0794643",
        "level of jugular notch on the vagus nerve": "ILX:0794644",
        "right level of jugular notch on the vagus nerve": "ILX:0794645",
        "left level of jugular notch on the vagus nerve": "ILX:0794646",
        "level of sternal angle on the vagus nerve": "ILX:0794647",
        "right level of sternal angle on the vagus nerve": "ILX:0794648",
        "left level of sternal angle on the vagus nerve": "ILX:0794649",
        "level of 1 cm superior to start of esophageal plexus on the vagus nerve": "ILX:0794650",
        "right level of 1 cm superior to start of esophageal plexus on the vagus nerve": "ILX:0794651",
        "left level of 1 cm superior to start of esophageal plexus on the vagus nerve": "ILX:0794652",
        "level of esophageal hiatus on the vagus nerve": "ILX:0794653",
        "right level of esophageal hiatus on the vagus nerve": "ILX:0794654",
        "left level of esophageal hiatus on the vagus nerve": "ILX:0794655",
        "level of aortic hiatus on the vagus nerve": "ILX:0794656",
        "right level of aortic hiatus on the vagus nerve": "ILX:0794657",
        "left level of aortic hiatus on the vagus nerve": "ILX:0794658"
    }

    return vagus_marker_terms


def find_anatomy_spreadsheet(anatomy_path):
    """
    :param anatomy_path: path to the folder that contains anatomy data
    :return: path to the file with anatomy data
    """
    if os.path.isdir(anatomy_path):
        file_exists = False
        for file in os.listdir(anatomy_path):
            if file.endswith('.xlsx') and all([keyword in file for keyword in ['Vagus', 'Pattern']]):
                file_exists = True
                anatomy_file = os.path.join(anatomy_path, file)
        if not file_exists:
            anatomy_file = None
    else:
        anatomy_file = None
    return anatomy_file


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
