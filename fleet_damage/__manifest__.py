# -*- coding: utf-8 -*-
{
    'name': 'Fleet Damage ',
    'category': 'Insurance',
    'summary': 'Manage Fleet Damage',
    'author': '',
    'version': '18.0.0.1',
    'depends': ['base', 'fleet', 'account', 'contacts', 'accountant', 'customer_info', 'fleet_status', 'fleet_accident'],
    'data': [
        'security/ir.model.access.csv',
        'data/fleet_status.xml',
        'views/evaluation_report.xml',
        'views/fleet_damage_view.xml',
        'views/set_default_damage_view.xml',
    ],
}
