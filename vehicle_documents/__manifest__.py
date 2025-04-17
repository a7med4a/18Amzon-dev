# -*- coding: utf-8 -*-
{
    'name': 'Vehicle Documents ',
    'category': 'Insurance',
    'summary': 'Manage Vehicle Documents',
    'author': '',
    'version': '18.0.0.1',
    'depends': ['base','fleet'],
    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/vehicle_documents_type_view.xml',
        'views/vehicle_documents_view.xml',
    ],
}


