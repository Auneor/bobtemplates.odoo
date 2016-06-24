# -*- coding: utf-8 -*-
# Copyright © 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import ast
import os
import re

from mrbob.bobexceptions import ValidationError
from mrbob.hooks import show_message


def _dotted_to_camelcased(dotted):
    return ''.join([s.capitalize() for s in dotted.split('.')])


def _dotted_to_underscored(dotted):
    return dotted.replace('.', '_')


def _dotted_to_camelwords(dotted):
    return ' '.join([s.capitalize() for s in dotted.split('.')])


def _underscored_to_camelcased(underscored):
    return ''.join([s.capitalize() for s in underscored.split('_')])


def _underscored_to_camelwords(underscored):
    return ' '.join([s.capitalize() for s in underscored.split('_')])


def _delete_file(configurator, path):
    """ remove file and remove it's directories if empty """
    path = os.path.join(configurator.target_directory, path)
    os.remove(path)
    try:
        os.removedirs(os.path.dirname(path))
    except OSError:
        pass


def _open_manifest(configurator, mode='r'):
    manifest_path = os.path.join(configurator.target_directory,
                                 '__openerp__.py')
    if not os.path.exists(manifest_path):
        raise ValidationError("{} not found".format(manifest_path))
    return open(manifest_path, mode)


def _load_manifest(configurator):
    with _open_manifest(configurator) as f:
        return ast.literal_eval(f.read())


def _insert_manifest_item(configurator, key, item):
    """ Insert an item in the list of an existing manifest key """
    with _open_manifest(configurator) as f:
        manifest = f.read()
    pattern = """(["']{}["']:\\s*\\[)""".format(key)
    repl = """\\1\n        '{}',""".format(item)
    manifest = re.sub(pattern, repl, manifest, re.MULTILINE)
    with _open_manifest(configurator, 'w') as f:
        f.write(manifest)


def _add_local_import(configurator, package, module):
    init_path = os.path.join(configurator.target_directory,
                             package, '__init__.py')
    import_string = 'from . import {}'.format(module)
    if os.path.exists(init_path):
        init = open(init_path).read()
    else:
        init = ''
    if import_string not in init:
        open(init_path, 'a').write(import_string + '\n')


def _rm_suffix(suffix, configurator, path):
    path = os.path.join(configurator.target_directory, path)
    assert path.endswith(suffix)
    os.rename(path, path[:-len(suffix)])


#
# model hooks
#

def pre_render_model(configurator):
    _load_manifest(configurator)  # check manifest is present
    variables = configurator.variables
    variables['model.name_underscored'] = \
        _dotted_to_underscored(variables['model.name_dotted'])
    variables['model.name_camelcased'] = \
        _dotted_to_camelcased(variables['model.name_dotted'])
    variables['model.name_camelwords'] = \
        _dotted_to_camelwords(variables['model.name_dotted'])
    variables['addon.name'] = \
        os.path.basename(os.path.normpath(configurator.target_directory))


def post_render_model(configurator):
    variables = configurator.variables
    # make sure the models package is imported from the addon root
    _add_local_import(configurator, '',
                      'models')
    # add new model import in __init__.py
    _add_local_import(configurator, 'models',
                      variables['model.name_underscored'])
    # views
    view_path = 'views/{}.xml'.format(variables['model.name_underscored'])
    _insert_manifest_item(configurator, 'data', view_path)
    # ACL
    acl_path = 'security/{}.xml'.format(variables['model.name_underscored'])
    if variables['model.acl']:
        _insert_manifest_item(configurator, 'data', acl_path)
    else:
        _delete_file(configurator, acl_path)
    # demo data
    demo_path = 'demo/{}.xml'.format(variables['model.name_underscored'])
    if variables['model.demo_data']:
        _insert_manifest_item(configurator, 'demo', demo_path)
    else:
        _delete_file(configurator, demo_path)
    # show message if any
    show_message(configurator)


#
# addon hooks
#


def pre_render_addon(configurator):
    variables = configurator.variables
    variables['addon.name_camelwords'] = \
        _underscored_to_camelwords(variables['addon.name'])


def post_render_addon(configurator):
    variables = configurator.variables
    if variables['addon.oca']:
        _rm_suffix('.oca', configurator, variables['addon.name'] +
                   '/README.rst.oca')
        _rm_suffix('.oca', configurator, variables['addon.name'] +
                   '/static/description/icon.svg.oca')
    else:
        _delete_file(configurator, variables['addon.name'] +
                     '/README.rst.oca')
        _delete_file(configurator, variables['addon.name'] +
                     '/static/description/icon.svg.oca')
    # show message if any
    show_message(configurator)


#
# test hooks
#


def pre_render_test(configurator):
    _load_manifest(configurator)  # check manifest is present
    variables = configurator.variables
    variables['test.name_camelcased'] = \
        _underscored_to_camelcased(variables['test.name_underscored'])


def post_render_test(configurator):
    # add new test import in __init__.py
    _add_local_import(configurator, 'tests',
                      configurator.variables['test.name_underscored'])
    # show message if any
    show_message(configurator)


#
# wizard hooks
#

def pre_render_wizard(configurator):
    _load_manifest(configurator)  # check manifest is present
    variables = configurator.variables
    variables['model.name_underscored'] = \
        _dotted_to_underscored(variables['model.name_dotted'])
    variables['model.name_camelcased'] = \
        _dotted_to_camelcased(variables['model.name_dotted'])
    variables['model.name_camelwords'] = \
        _dotted_to_camelwords(variables['model.name_dotted'])
    variables['addon.name'] = \
        os.path.basename(os.path.normpath(configurator.target_directory))


def post_render_wizard(configurator):
    variables = configurator.variables
    # make sure the models package is imported from the addon root
    _add_local_import(configurator, '',
                      'wizards')
    # add new model import in __init__.py
    _add_local_import(configurator, 'wizards',
                      variables['model.name_underscored'])
    # views
    wizard_path = 'wizards/{}.xml'.format(variables['model.name_underscored'])
    _insert_manifest_item(configurator, 'data', wizard_path)
    # show message if any
    show_message(configurator)
