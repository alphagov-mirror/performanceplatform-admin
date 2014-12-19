from admin import app
from admin.fields.json_textarea import JSONTextAreaField
from wtforms import (FieldList, Form, FormField, TextAreaField, TextField,
                     SelectField, HiddenField, validators)
from performanceplatform.client import AdminAPI
import requests
from os import getenv
import json


def convert_to_dashboard_form(dashboard_dict, admin_client):
    for module in dashboard_dict['modules']:
        module['info'] = json.dumps(module['info'])
        if module['query_parameters'] is not None:
            module['query_parameters'] = json.dumps(module['query_parameters'])
        module['options'] = json.dumps(module['options'])
        module['module_type'] = module['type']['id']
        module['uuid'] = module['id']
    transaction_link = [link for link
                        in dashboard_dict['links']
                        if link['type'] == 'transaction']
    if len(transaction_link) > 1:
        raise ValueError('Dashboards cannot have more than 1 transaction link')
    elif len(transaction_link) == 1:
        dashboard_dict['transaction_link'] = transaction_link[0]['url']
        dashboard_dict['transaction_title'] = transaction_link[0]['title']
    if dashboard_dict['organisation'] is not None:
        organisation_id = dashboard_dict['organisation']['id']
    else:
        organisation_id = None
    dashboard_dict['owning_organisation'] = organisation_id
    return DashboardCreationForm(admin_client, data=dashboard_dict)


def get_module_choices():
    choices = [('', '')]

    if not getenv('TESTING', False):
        try:
            # Create an unauthenticated client
            admin_client = AdminAPI(app.config['STAGECRAFT_HOST'], None)
            module_types = admin_client.list_module_types()
            choices += [
                (module['id'], module['name']) for module in module_types]
        except requests.ConnectionError:
            if not app.config['DEBUG']:
                raise
    return choices


class ModuleForm(Form):
    id = HiddenField('UUID')
    module_type = SelectField('Module type', choices=get_module_choices())

    data_group = TextField('Data group')
    data_type = TextField('Data type')

    slug = TextField('Module URL')
    title = TextField('Title')
    description = TextField('Description')
    info = TextField('Info')

    query_parameters = JSONTextAreaField('Query parameters', default='{}')
    options = JSONTextAreaField('Visualisation settings', default='{}')


def get_organisation_choices(admin_client):
    choices = [('', '')]

    try:
        organisations = admin_client.list_organisations()
        choices += [
            (org['id'], org['name']) for org in organisations]
        choices.sort(key=lambda tup: tup[1])
    except requests.ConnectionError:
        if not app.config['DEBUG']:
            raise
    return choices


class DashboardCreationForm(Form):
    def __init__(self, admin_client, *args, **kwargs):
        super(DashboardCreationForm, self).__init__(*args, **kwargs)
        self.owning_organisation.choices = get_organisation_choices(
            admin_client)

    dashboard_type = SelectField('Dashboard type', choices=[
        ('transaction', 'Transaction'),
        ('high-volume-transaction', 'High volume transaction'),
        ('service-group', 'Service group'),
        ('agency', 'Agency'),
        ('department', 'Department'),
        ('content', 'Content'),
        ('other', 'Other'),
    ])
    strapline = SelectField('Strapline', choices=[
        ('Dashboard', 'Dashboard'),
        ('Service dashboard', 'Service dashboard'),
        ('Content dashboard', 'Content dashboard'),
        ('Performance', 'Performance'),
        ('Policy dashboard', 'Policy dashboard'),
        ('Public sector purchasing dashboard',
         'Public sector purchasing dashboard'),
    ])
    slug = TextField('Dashboard URL')
    title = TextField('Dashboard title')
    description = TextField('Description')
    owning_organisation = SelectField(
        'Owning organisation',
        [validators.Required(message='This field cannot be blank.')]
    )
    customer_type = SelectField('Customer type', choices=[
        ('', ''),
        ('Business', 'Business'),
        ('Individuals', 'Individuals'),
    ])
    business_model = SelectField('Business model', choices=[
        ('', ''),
        ('Department budget', 'Department budget'),
        ('Fees and charges', 'Fees and charges'),
        ('Taxpayers', 'Taxpayers'),
        ('Fees and charges, and taxpayers', 'Fees and charges, and taxpayers'),
    ])
    costs = TextAreaField('Notes on costs')
    other_notes = TextAreaField('Other notes')

    transaction_title = TextField('Transaction action')
    transaction_link = TextField('Transaction link')

    modules = FieldList(FormField(ModuleForm), min_entries=0)
    published = HiddenField('published', default=False)
