# -*- coding: utf-8 -*-
{
    'name': "Legal Department",
    'summary': "Legal Department",
    'description': """Legal Department""",
    'author': "M.Deep",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['rental_contract', 'maintenance_custom'],
    'data': [

        # Data Files
        'data/rental_contract_sequence.xml',
        'data/ir_module_category_data.xml',

        # Security Files
        'security/groups.xml',
        'security/ir.model.access.csv',

        # View Files
        'views/police_alert.xml',
        'views/police_alert_popup.xml',
        'views/rental_contract.xml',
        'views/fleet_vehicle.xml',
        'views/menu_item.xml'
    ],
}
