from admin import app
from admin.forms import DashboardCreationForm
from admin.helpers import (
    base_template_context,
    requires_authentication,
    requires_permission,
)
from flask import (
    flash, redirect, render_template, request,
    session, url_for
)
from admin.forms import convert_to_dashboard_form

import json
import requests


DASHBOARD_ROUTE = '/administer-dashboards'


@app.route('{0}'.format(DASHBOARD_ROUTE), methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_admin_index(admin_client):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })

    dashboards_url = '{0}/dashboards'.format(app.config['STAGECRAFT_HOST'])
    access_token = session['oauth_token']['access_token']
    headers = {
        'Authorization': 'Bearer {0}'.format(access_token),
    }

    dashboard_response = requests.get(dashboards_url, headers=headers)

    if dashboard_response.status_code == 200:
        dashboards = dashboard_response.json()['dashboards']
        if len(dashboards) == 0:
            flash('No dashboards stored', 'info')
    else:
        flash('Could not retrieve the list of dashboards', 'danger')
        dashboards = None

    return render_template('dashboards/index.html',
                           dashboards=dashboards,
                           **template_context)


@app.route('{0}/new'.format(DASHBOARD_ROUTE), methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_admin_create(admin_client):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
    })

    if 'pending_dashboard' in session:
        form = DashboardCreationForm(data=session['pending_dashboard'])
    else:
        form = DashboardCreationForm(request.form)

    if request.args.get('modules'):
        total_modules = int(request.args.get('modules'))
        modules_required = total_modules - len(form.modules)
        for i in range(modules_required):
            form.modules.append_entry()

    return render_template('dashboards/create.html',
                           form=form,
                           **template_context)


@app.route('{0}'.format(DASHBOARD_ROUTE), methods=['POST'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_admin_create_post(admin_client):
    form = DashboardCreationForm(request.form)
    session['pending_dashboard'] = form.data

    result = move_or_remove(request.form, session, 'dashboard_admin_create')
    if result is not None:
        return result

    try:
        dict_for_post = build_dict_for_post(form)
        admin_client.create_dashboard(dict_for_post)
        if 'pending_dashboard' in session:
            del session['pending_dashboard']
        flash('Created the {} dashboard'.format(form.slug.data), 'success')
        return redirect(url_for('dashboard_admin_index'))
    except requests.HTTPError as e:
        formatted_error = 'Error creating the {} dashboard: {}'.format(
            form.slug.data, e.response.json()['message'])
        flash(formatted_error, 'danger')
        return redirect(url_for('dashboard_admin_create'))
    except ValueError as e:
        formatted_error = 'Error validating the {} dashboard: {}'.format(
            form.slug.data, e.message)
        flash(formatted_error, 'danger')
        return redirect(url_for('dashboard_admin_create'))


@app.route('{0}/<uuid>'.format(DASHBOARD_ROUTE), methods=['GET'])
@requires_authentication
@requires_permission('dashboard')
def edit_dashboard(admin_client, uuid):
    template_context = base_template_context()
    template_context.update({
        'user': session['oauth_user'],
        'uuid': uuid
    })
    if session.get('pending_dashboard', {}).get('uuid') == uuid:
        form = DashboardCreationForm(data=session['pending_dashboard'])
    else:
        dashboard_dict = admin_client.get_dashboard(uuid)
        form = convert_to_dashboard_form(dashboard_dict)

    if request.args.get('modules'):
        total_modules = int(request.args.get('modules'))
        modules_required = total_modules - len(form.modules)
        for i in range(modules_required):
            form.modules.append_entry()

    return render_template('dashboards/create.html',
                           form=form,
                           **template_context)


@app.route('{0}/<uuid>'.format(DASHBOARD_ROUTE), methods=['POST'])
@requires_authentication
@requires_permission('dashboard')
def dashboard_admin_update_put(admin_client, uuid):
    form = DashboardCreationForm(request.form)
    session['pending_dashboard'] = form.data
    session['pending_dashboard']['uuid'] = uuid

    result = move_or_remove(request.form, session, 'edit_dashboard', uuid=uuid)
    if result is not None:
        return result

    try:
        dict_for_post = build_dict_for_post(form)
        admin_client.update_dashboard(uuid, dict_for_post)
        if 'pending_dashboard' in session:
            del session['pending_dashboard']
        flash('Updated the {} dashboard'.format(form.slug.data), 'success')
        return redirect(url_for('dashboard_admin_index'))
    except requests.HTTPError as e:
        formatted_error = 'Error updating the {} dashboard: {}'.format(
            form.slug.data, e.response.json()['message'])
        flash(formatted_error, 'danger')
        return redirect(url_for('edit_dashboard', uuid=uuid))
    except ValueError as e:
        formatted_error = 'Error validating the {} dashboard: {}'.format(
            form.slug.data, e.message)
        flash(formatted_error, 'danger')
        return redirect(url_for('edit_dashboard', uuid=uuid))


def build_dict_for_post(form):
    parsed_modules = []

    for (index, module) in enumerate(form.modules.entries, start=1):
        if module.info.data.strip():
            info = json.loads(module.info.data)
        else:
            info = []
        if not isinstance(info, list):
            raise ValueError("Info must be a list")
        for item in info:
            if not isinstance(item, basestring):
                raise ValueError("Info must all be strings")
        parsed_modules.append({
            # module.id ends up being the id of the subform, so we cant use the
            # magic method
            'id': module.data['id'],
            'type_id': module.module_type.data,
            'data_group': module.data_group.data,
            'data_type': module.data_type.data,
            'slug': module.slug.data,
            'title': module.title.data,
            'description': module.data['description'],
            'info': info,
            'options': json.loads(module.options.data),
            'query_parameters': json.loads(module.query_parameters.data),
            'order': index,
        })
    return {
        'published': form.published.data,
        'page-type': 'dashboard',
        'dashboard-type': form.dashboard_type.data,
        'slug': form.slug.data,
        'title': form.title.data,
        'description': form.description.data,
        'customer_type': form.customer_type.data,
        'business_model': form.business_model.data,
        'strapline': form.strapline.data,
        'links': [{
            'title': form.transaction_title.data,
            'url': form.transaction_link.data,
            'type': 'transaction',
        }],
        'modules': parsed_modules,
    }


def move_or_remove(request_form, session, action, **kwargs):
    def get_module_index(field_prefix, form):
        for field in form.keys():
            if field.startswith(field_prefix):
                return int(field.replace(field_prefix, ''))

        return None

    # Add a new empty module
    if 'add_module' in request.form:
        current_modules = len(
            DashboardCreationForm(
                data=session['pending_dashboard']).modules)
        kwargs['modules'] = current_modules + 1
        return redirect(url_for(action,
                                **kwargs))

    # Remove a module from the list
    index = get_module_index('remove_module_', request.form)
    if index is not None:
        session['pending_dashboard']['modules'].pop(index)
        return redirect(url_for(action, **kwargs))

    # Move a module down in the list (increment it's index number)
    index = get_module_index('move_module_down_', request.form)
    if index is not None:
        modules = session['pending_dashboard']['modules']
        if index < len(modules) - 1:
            modules[index], modules[index+1] = modules[index+1], modules[index]
            session['pending_dashboard']['modules'] = modules
        return redirect(url_for(action, **kwargs))

    # Move a module up in the list (decrement it's index number)
    index = get_module_index('move_module_up_', request.form)
    if index is not None:
        modules = session['pending_dashboard']['modules']
        if index > 0:
            modules[index], modules[index-1] = modules[index-1], modules[index]
            session['pending_dashboard']['modules'] = modules
        return redirect(url_for(action, **kwargs))
