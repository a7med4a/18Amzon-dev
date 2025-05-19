# -*- coding: utf-8 -*-
{
    'name': 'Fleet Insurance ',
    'category': 'Insurance',
    'summary': 'Manage Fleet Insurance Policies and Accidents',
    'author': '',
    'version': '18.0.0.1',
    'depends': ['base','fleet','account','contacts','accountant'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/insurance_sequence.xml',
        'data/server_action.xml',
        'views/menu_view.xml',
        'views/policy_line_view.xml',
        'views/insurance_policy_view.xml',
        'views/insurance_policy_wizard.xml',
        'views/configration_view.xml',
        'views/fleet_vehicle_inherit_view.xml',
        'views/insurance_company_data.xml',
        'views/termination_log_view.xml',
        'views/res_partner_inherit_view.xml',
        'views/account_move_inherit.xml',
        'views/financial_info_view.xml',
    ],
}


