# -*- coding: utf-8 -*-
{
    'name': "Customer Info",
    'summary': "this addon for Customer Info",
    'category': 'Base',
    'author': 'Ahmed Amen',
    "license": 'OPL-1',
    'depends': ['base','rental_customization'],
    'data': [
        'views/individual_customers_views.xml',
        'views/menus.xml',
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
}
