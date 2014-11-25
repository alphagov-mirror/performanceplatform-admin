from unittest import TestCase
from admin.forms import convert_to_dashboard_form
from hamcrest import assert_that, equal_to
from mock import Mock, patch
import os
import json
from admin.dashboards import build_dict_for_post


class DashboardTestCase(TestCase):
    @patch('admin.forms.ModuleTypes.get_section_type',
           return_value={'id': 'module-type-uuid', 'name': 'section'})
    def test_convert_to_dashboard_form_returns_correct_dashboard_form(
            self, mock_get_section_type):
        with open(os.path.join(
                  os.path.dirname(__file__),
                  '../fixtures/example-dashboard.json')) as file:
            dashboard_json = file.read()
        dashboard_dict = json.loads(dashboard_json)
        mock_admin_client = Mock()
        mock_admin_client.list_organisations = Mock(
            return_value=[{'id': '', 'name': ''}])
        dashboard_form = convert_to_dashboard_form(dashboard_dict,
                                                   mock_admin_client)
        dict_for_post = build_dict_for_post(dashboard_form)
        assert_that(
            dict_for_post['description'],
            equal_to(dashboard_dict['description']))
        assert_that(
            dict_for_post['dashboard-type'],
            equal_to(dashboard_dict['dashboard_type']))
        assert_that(
            dict_for_post['modules'][0]['type_id'],
            equal_to(dashboard_dict['modules'][0]['type']['id']))
        assert_that(
            dict_for_post['modules'][0]['data_group'],
            equal_to(dashboard_dict['modules'][0]['data_group']))
        assert_that(
            dict_for_post['modules'][0]['data_type'],
            equal_to(dashboard_dict['modules'][0]['data_type']))
        assert_that(
            dict_for_post['modules'][0]['id'],
            equal_to(dashboard_dict['modules'][0]['id']))
        assert_that(
            dict_for_post['modules'][0]['description'],
            equal_to(dashboard_dict['modules'][0]['description']))
        assert_that(
            dict_for_post['links'], equal_to(dashboard_dict['links']))
        assert_that(
            dict_for_post['published'], equal_to(dashboard_dict['published']))
