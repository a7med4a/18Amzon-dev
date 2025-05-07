# -*- coding: utf-8 -*-
{
    'name': 'Fleet Tracking Device',
    'category': 'Insurance',
    'summary': 'Manage Fleet Tracking Device',
    'author': '',
    'version': '18.0.0.1',
    'depends': ['base', 'fleet', 'purchase', 'product', 'stock', 'stock_account'],
    'data': [
        'security/ir.model.access.csv',
        'data/purchase_type.xml',
        'views/purchase_type.xml',
        'views/models.xml',
        'views/vehicle_tracking_device.xml',
        'views/fleet_vehicle.xml',
    ],
}
