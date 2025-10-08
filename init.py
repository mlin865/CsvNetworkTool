import os

from csv_processing import find_tracing_csv_files, process_segment_csv_files
from fascicles import find_trunk_fascicle_file_for_segment, read_fascicle_file_into_region
from nerve_morphology import find_trunk_morphology_file_for_segment, process_trunk_morphology_file_radius
from anatomy import read_vagus_branching_pattern_spreadsheet, create_orientation_markers
from annotations import add_trunk_annotation_terms
from output import write_exf


def main(anatomy_file_path, microct_path, nerve_morphology_path, fascicle_path, output_directory,
         stitching_tolerance):
    """
    :param anatomy_file_path: path to the folder that contains anatomy data
    :param microct_path: path to the folder with csv segmentation files
    :param nerve_morphology_path: path to the folder with csv morphology files
    :param fascicle_path: path to the folder with graphml fascicle files
    :param output_root_path: path to the folder where to save the output results
    :param stitching_tolerance: tolerance used for branch stitching
    :return:
    """

    # read anatomy data (vagus branching pattern spreadsheet) with orientations and annotations
    if anatomy_file_path:
        vagus_orientations, vagus_branch_terms = read_vagus_branching_pattern_spreadsheet(anatomy_file_path)
    else:
        print('Warning: no anatomy file found.')
        vagus_orientations = None
        vagus_branch_terms = {None: None}

    # add trunk annotation groups in case they aren't in vagus terms
    vagus_branch_terms.update(add_trunk_annotation_terms())

    # read micro ct data
    segment_files = find_tracing_csv_files(microct_path)
    output_files = []
    if len(segment_files) > 0:
        for segment_name in segment_files.keys():
            print(segment_name)
            segment_csv_files = segment_files[segment_name]
            if len(segment_csv_files) > 0:
                marker_data, trunk_group_name, trunk_coordinates, branch_names, \
                    branch_coordinates_data, branch_parent_indices = process_segment_csv_files(segment_csv_files,
                                                                                               stitching_tolerance)

                # find vagus terms used for annotating the segment data
                vagus_terms = dict()
                if vagus_branch_terms:
                    vagus_terms[trunk_group_name] = vagus_branch_terms[trunk_group_name]
                    for branch_name in branch_coordinates_data.keys():
                        if branch_name in vagus_branch_terms.keys():
                            vagus_terms[branch_name] = vagus_branch_terms[branch_name]

                # calculate orientation markers
                orientation_markers = None
                if vagus_orientations:
                    orientation_markers = create_orientation_markers(branch_coordinates_data, vagus_orientations)

                # find morphology file corresponding to the segment to add the radius data
                trunk_radius = []
                avg_branch_radius = None
                if nerve_morphology_path:
                    morphology_file_path = find_trunk_morphology_file_for_segment(nerve_morphology_path,
                                                                                  segment_name, trunk_group_name)
                    print(segment_name, trunk_group_name, morphology_file_path)
                    if morphology_file_path:
                        trunk_radius, avg_trunk_radius = process_trunk_morphology_file_radius(morphology_file_path, trunk_coordinates)
                        avg_branch_radius = avg_trunk_radius / 2

                # find fascicles file corresponding to the segment
                fascicles_region_path = None
                if fascicle_path:
                    fascicle_input_path = find_trunk_fascicle_file_for_segment(fascicle_path, segment_name, trunk_group_name)
                    print(segment_name, trunk_group_name, fascicle_input_path)
                    if fascicle_input_path:
                        fascicles_region_path = read_fascicle_file_into_region(fascicle_input_path, segment_name, output_directory)

                # write output file
                output_filename = segment_name + ".exf"
                output_file = os.path.join(output_directory, output_filename)
                output_files.append(output_file)
                write_exf(output_file, marker_data, trunk_group_name, trunk_coordinates, trunk_radius, branch_names,
                          branch_coordinates_data, branch_parent_indices, avg_branch_radius, orientation_markers,
                          vagus_terms, fascicles_region_path)
            else:
                print('Warning: no microct files found for segment', segment_name)
    else:
        print('Warning: no microct files found.')

    return output_files


if __name__ == "__main__":

    input_directory = r"Z:\Pennsieve datasets\426 - Scaffold map - Human vagus nerve\in preparation\derivative\sub-SR042\L"
    anatomy_path = os.path.join(input_directory, "SR042-Vagus-Branching-Pattern.xlsx")
    microct_path = os.path.join(input_directory, "MicroCT")
    nerve_morphology_path = os.path.join(input_directory, "NerveMorphology")
    fascicle_path = os.path.join(input_directory, "FascicleMorphology")

    output_directory = r"Z:\Pennsieve datasets\426 - Scaffold map - Human vagus nerve\in preparation\derivative\sub-SR042\L\010-data-preparation"

    stitching_tolerance = 110000.0
    main(anatomy_path,
         microct_path, nerve_morphology_path, fascicle_path,
         output_directory, stitching_tolerance)
