# -*- coding: utf-8 -*-
{
    'name': 'Vehicle Accessories ',
    'category': 'Insurance',
    'summary': 'Manage Vehicle Accessories',
    'author': '',
    'version': '18.0.0.1',
    'depends': ['base','fleet'],
    'data': [
        'security/ir.model.access.csv',
        # 'data/cron.xml',
        'views/vehicle_accessories_type_view.xml',
        'views/vehicle_accessories_view.xml',
        'views/fleet_vehicle_inherit_view.xml',
    ],
}


