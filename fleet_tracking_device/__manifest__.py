# -*- coding: utf-8 -*-
{
    'name': 'Fleet Tracking Device',
    'category': 'Insurance',
    'summary': 'Manage Fleet Tracking Device',
    'author': '',
    'version': '18.0.0.1',
    'depends': ['base','fleet','purchase','product','stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_type.xml',
        'views/models.xml',
        'views/vehicle_tracking_device.xml',
    ],
}


