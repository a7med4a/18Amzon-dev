# -*- coding: utf-8 -*-
{
    'name': "Fleet Accident",
    'summary': "Add Fleet Accident TO Product",
    'description': """Add Fleet Accident TO Product""",
    'author': "M.Deeb",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['fleet', 'customer_info', 'fleet_insurance', 'fleet_status'],
    'data': [
        'security/ir.model.access.csv',
        'views/evaluation_party.xml',
        'views/evaluation_item.xml',
        'views/default_accident_item.xml',
        'views/account_move.xml',
        'views/fleet_accident.xml',
        'views/menu_item.xml',
    ]
}
