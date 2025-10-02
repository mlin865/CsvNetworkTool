import os
import unittest

from cmlibs.utils.zinc.field import get_group_list
from cmlibs.utils.zinc.group import groups_have_same_local_contents
from cmlibs.zinc.context import Context
from cmlibs.zinc.field import Field
from cmlibs.zinc.result import RESULT_OK

from init import find_orientation_spreadsheet, find_tracing_csv_files, main
from annotations import read_case_vagus_termslist
from anatomy import read_vagus_branching_pattern_spreadsheet
from csv_processing import branch_is_non_vagal, suggest_parent_name

here = os.path.abspath(os.path.dirname(__file__))


class VagusMergeTestCase(unittest.TestCase):

    def test_read_terms(self):
        terms_path = os.path.join(here, "resources", "terms.xlsx")
        _, vagus_branch_terms = read_case_vagus_termslist(terms_path)
        self.assertNotEqual(vagus_branch_terms, {})
        self.assertTrue('left vagus nerve' in vagus_branch_terms.keys())
        self.assertEqual(vagus_branch_terms['left vagus nerve'], 'http://uri.interlex.org/base/ilx_0785628')
        self.assertEqual(vagus_branch_terms['right branch to carotid bifurcation'], 'http://uri.interlex.org/base/ilx_0794089')
        # check branch with NEW id is not in the terms
        self.assertFalse('right branch to carotid bifurcation E' in vagus_branch_terms.keys())
        # check non-vagal branch is not in the terms
        self.assertFalse('right hypoglossal nerve' in vagus_branch_terms.keys())

    def test_read_anatomy(self):
        root_path = os.path.join(here, "resources", "sub-SR000")
        anatomy_path = os.path.join(root_path, "Anatomy")
        anatomy_file = find_orientation_spreadsheet(anatomy_path)
        vagus_orientations = read_vagus_branching_pattern_spreadsheet(anatomy_file)
        self.assertNotEqual(vagus_orientations, {})
        self.assertTrue('right branch to C2 spinal nerve' in vagus_orientations)
        self.assertEqual(vagus_orientations['right branch to C2 spinal nerve'], 'posterior')

    def test_read_tracing(self):
        root_path = os.path.join(here, "resources", "sub-SR000")
        microct_path = os.path.join(root_path, "MicroCT")
        segment_files = find_tracing_csv_files(microct_path)
        self.assertTrue(len(segment_files), 5)
        self.assertTrue('sam-SR000-CR1' in segment_files.keys())
        self.assertTrue(len(segment_files['sam-SR000-CR1']), 8)
        self.assertTrue(
            any(['CR1-right_cervical_trunk' in segment_file for segment_file in segment_files['sam-SR000-CR1']]))
        self.assertEqual(segment_files['sam-SR000-TR2'], [])

    def test_non_vagus_filtering(self):

        branch_name = 'left hypoglossal nerve'
        self.assertEqual(branch_is_non_vagal(branch_name, 'left'), True)
        branch_name = 'branch of left hypoglossal nerve'
        self.assertEqual(branch_is_non_vagal(branch_name, 'left'), True)
        branch_name = 'branch A of left hypoglossal nerve'
        self.assertEqual(branch_is_non_vagal(branch_name, 'left'), True)
        branch_name = 'branch to left hypoglossal nerve'
        self.assertEqual(branch_is_non_vagal(branch_name, 'left'), False)
        branch_name = 'branch of superior nerve to left hypoglossal nerve'
        self.assertEqual(branch_is_non_vagal(branch_name, 'left'), False)
        branch_name = 'right pulmonary branch A'
        self.assertEqual(branch_is_non_vagal(branch_name, 'right'), False)

    def test_find_branch_parent_name(self):

        trunk_group_name = 'left vagus nerve'
        side = 'left'

        branch_name = 'left pulmonary branch A'
        self.assertEqual(suggest_parent_name(branch_name, side, trunk_group_name), trunk_group_name)
        branch_name = 'left recurrent laryngeal nerve'
        self.assertEqual(suggest_parent_name(branch_name, side, trunk_group_name), trunk_group_name)
        branch_name = 'left branch to cervical ganglion'
        self.assertEqual(suggest_parent_name(branch_name, side, trunk_group_name), trunk_group_name)
        branch_name = 'left branch of recurrent laryngeal nerve'
        self.assertEqual(suggest_parent_name(branch_name, side, trunk_group_name),
                         'left recurrent laryngeal nerve')
        branch_name = 'left A branch of recurrent laryngeal nerve'
        self.assertEqual(suggest_parent_name(branch_name, side, trunk_group_name),
                         'left recurrent laryngeal nerve')
        branch_name = 'branch A of left recurrent laryngeal nerve'
        self.assertEqual(suggest_parent_name(branch_name, side, trunk_group_name),
                         'left recurrent laryngeal nerve')
        branch_name = 'external branch of recurrent laryngeal nerve'
        self.assertEqual(suggest_parent_name(branch_name, side, trunk_group_name),
                         'left recurrent laryngeal nerve')
        branch_name = 'branch to external branch of recurrent laryngeal nerve'
        self.assertEqual(suggest_parent_name(branch_name, side, trunk_group_name), trunk_group_name)
        branch_name = 'branch of left pulmonary branch H'
        self.assertEqual(suggest_parent_name(branch_name, side, trunk_group_name),
                         'left pulmonary branch H')

        branch_name = 'branch A of right glossopharyngeal nerve'
        self.assertEqual(suggest_parent_name(branch_name, 'right', trunk_group_name),
                         'right glossopharyngeal nerve')
        branch_name = 'sub branch A of left glossopharyngeal nerve'
        self.assertEqual(suggest_parent_name(branch_name, 'left', trunk_group_name),
                         'left glossopharyngeal nerve')



    def test_vagus_merge_output(self):
        """
        Test of vagus csv merger
        """

        terms_path = os.path.join(here, "resources", "terms.xlsx")
        root_path = os.path.join(here, "resources", "sub-SR000")
        anatomy_path = os.path.join(root_path, "Anatomy")
        microct_path = os.path.join(root_path, "MicroCT")
        output_root_path = os.path.join(here, "resources", "output")

        output_files = main(terms_path, anatomy_path, microct_path, output_root_path)
        self.assertEqual(len(output_files), 4)
        cl2_output_file = output_files[0]

        context = Context("CL2 Segment Data Test")
        base_region = context.getDefaultRegion()
        region = base_region.createChild('data')
        result = region.readFile(cl2_output_file)
        assert result == RESULT_OK

        field_module = region.getFieldmodule()
        field_cache = field_module.createFieldcache()

        nodes = field_module.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_NODES)
        datapoints = field_module.findNodesetByFieldDomainType(Field.DOMAIN_TYPE_DATAPOINTS)
        coordinates = field_module.findFieldByName("coordinates").castFiniteElement()

        group_list = get_group_list(field_module)
        group_map = {}
        for group in group_list:
            group_name = group.getName().strip()
            group_map[group_name] = group
        self.assertTrue('left vagus nerve' in group_map.keys())
        self.assertTrue(groups_have_same_local_contents(group_map['left vagus nerve'],
                                                        group_map['http://uri.interlex.org/base/ilx_0785628']))
        trunk_nodeset_group = group_map['left vagus nerve'].getNodesetGroup(nodes)
        self.assertTrue(trunk_nodeset_group.getSize(), 7676)

        self.assertTrue('marker' in group_map.keys())
        marker_group = field_module.findFieldByName("marker").castGroup()
        marker_names = field_module.findFieldByName("marker_name")
        marker_datapoints = marker_group.getNodesetGroup(datapoints)
        self.assertTrue(marker_datapoints.getSize(), 1)
        marker_node_iter = marker_datapoints.createNodeiterator()
        marker_node = marker_node_iter.next()
        field_cache.setNode(marker_node)
        marker_name = marker_names.evaluateString(field_cache).strip()
        self.assertEqual(marker_name, 'left level of laryngeal prominence on the vagus nerve')
        _, marker_xyz = coordinates.evaluateReal(field_cache, 3)
        self.assertAlmostEqual(marker_xyz, [1645.693578601415, 967.3220804195869, 1091.709343097647], delta=1e-8)

        self.assertTrue('orientation left' in group_map.keys())
        orientation_nodes = group_map['orientation left'].getNodesetGroup(nodes)
        self.assertTrue(orientation_nodes.getSize(), 2)


if __name__ == "__main__":
    unittest.main()