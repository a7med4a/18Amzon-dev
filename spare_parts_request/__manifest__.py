# -*- coding: utf-8 -*-
{
    'name': 'Spare Parts ',
    'category': '',
    'summary': 'Manage Spare Parts Request',
    'author': '',
    'version': '18.0.0.1',
    'depends': ['base','mail', 'branches_management','stock', 'fleet_master_configuration'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/spare_parts_sequence.xml',
        'views/spare_parts_request_view.xml',
        'views/res_branch_inherit_view.xml',

    ],
}
