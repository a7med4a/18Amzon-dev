# -*- coding: utf-8 -*-
{
    'name': "Rental Customization",
    'summary': "this addon for Rental Management",
    'category': 'Rental',
    'author': 'Ahmed Amen',
    "license": 'OPL-1',
    'depends': ['base','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/individual_customers_views.xml',
        'views/menus.xml',
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
}
