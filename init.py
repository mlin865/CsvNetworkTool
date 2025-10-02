import os

from csv_processing import find_tracing_csv_files, process_segment_csv_files
from fascicles import find_trunk_fascicle_file_for_segment, read_fascicle_file_into_region
from nerve_morphology import find_trunk_morphology_file_for_segment, process_trunk_morphology_file_radius
from anatomy import find_anatomy_spreadsheet, read_vagus_branching_pattern_spreadsheet, create_orientation_markers
from output import write_exf


def main(stitching_tolerance, anatomy_path, microct_path, nerve_morphology_path, fascicle_path,
         output_root_path):
    """
    :param stitching_tolerance: tolerance used for branch stitching
    :param terms_path: path to the xlsx that maps names to the annotation terms
    :param anatomy_path: path to the folder that contains anatomy data
    :param microct_path: path to the folder with csv segmentation files
    :param nerve_morphology_path: path to the folder with csv morphology files
    :param fascicle_path: path to the folder with graphml fascicle files
    :param output_root_path: path to the folder where to save the output results
    :return:
    """

    # read vagus termlist
    # vagus_branch_terms = read_case_vagus_termslist(terms_path)
    # if not vagus_branch_terms:
    #     print('Warning: no term list found.')

    # read anatomy data (vagus branching pattern spreadsheet) with orientations and annotations
    anatomy_file = find_anatomy_spreadsheet(anatomy_path)
    if anatomy_file:
        vagus_orientations, vagus_branch_terms = read_vagus_branching_pattern_spreadsheet(os.path.join(anatomy_path, anatomy_file))
    else:
        print('Warning: no anatomy file found.')
        vagus_orientations = None
        vagus_branch_terms = None

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
                    if morphology_file_path:
                        trunk_radius, avg_trunk_radius = process_trunk_morphology_file_radius(morphology_file_path, trunk_coordinates)
                        avg_branch_radius = avg_trunk_radius / 2

                # find fascicles file corresponding to the segment
                fascicles_region_path = None
                if fascicle_path:
                    fascicle_input_path = find_trunk_fascicle_file_for_segment(fascicle_path, segment_name, trunk_group_name)
                    if fascicle_input_path:
                        fascicles_region_path = read_fascicle_file_into_region(fascicle_input_path, segment_name, output_root_path)

                # write output file
                output_filename = segment_name + ".exf"
                output_file = os.path.join(output_root_path, output_filename)
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

    root_path = r"Z:\Pennsieve datasets\426 - Scaffold map - Human vagus nerve\in preparation\derivative\sub-SR042\R"
    anatomy_path = root_path # os.path.join(root_path, "Anatomy")
    microct_path = os.path.join(root_path, "MicroCT")
    subject_id = root_path.split('-')[-1]

    derivative_path = r"C:\MicroCT_derivative"
    nerve_morphology_path = os.path.join(derivative_path, subject_id, "NerveMorphology")
    fascicle_path = None #os.path.join(derivative_path, subject_id, "FascicleMorphology")

    output_root_folder = r"C:\MAP\input\CASE_datasets_limited"
    output_root_path = os.path.join(output_root_folder, subject_id)

    stitching_tolerance = 110000.0
    main(stitching_tolerance,
         anatomy_path, microct_path,
         nerve_morphology_path, fascicle_path,
         output_root_path)
