{
    'name': "Long Term Rental",
    'summary': "this addon for Long Term Rental Management",
    'category': 'Rental',
    'author': 'Ahmed Amen',
    "license": 'OPL-1',
    'depends': ['base', 'account', 'rental_contract', 'customer_info'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'views/long_term_contract_views.xml',
        'views/long_term_customers_views.xml',
        'views/long_term_pricing_request_views.xml',
        'views/long_term_rental_contract.xml',
        'wizard/payment_register.xml',
        'views/payment.xml',
        'views/menus.xml',
    ],
    "application": True,
    "installable": True,
    "auto_install": False,
}
# -*- coding: utf-8 -*-
