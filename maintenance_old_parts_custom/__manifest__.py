# -*- coding: utf-8 -*-

{
    'name': 'Maintenance Old Parts',
    'version': '1.0',
    'sequence': 100,
    'author': 'Ahmed Amen',
    'category': 'Manufacturing/Maintenance',
    'description': """Track old parts""",
    'depends': ['base','mail','fleet_tracking_device','product','maintenance','maintenance_custom'],
    'summary': 'Track old parts',
    'data': [
        'security/ir.model.access.csv',
        'views/product_inherit.xml',
        'views/old_spare_parts_views.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
