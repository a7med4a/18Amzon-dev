# -*- coding: utf-8 -*-
{
    'name': 'Vehicle Purchase ',
    'category': 'Insurance',
    'summary': 'Manage Vehicle Purchase',
    'author': '',
    'version': '18.0.0.1',
    'depends': ['base','fleet','purchase','contacts','accountant'],
    'data': [
        'security/ir.model.access.csv',
        'data/vehicle_purchase_sequence.xml',
        'views/vehicle_purchase_view.xml',
        'views/vehicle_purchase_quotation_view.xml',
        'views/vehicle_purchase_order_view.xml',
        'wizard/payment_register.xml',
    ],
}


