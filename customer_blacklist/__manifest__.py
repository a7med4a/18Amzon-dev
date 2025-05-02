# -*- coding: utf-8 -*-

{
    'name': 'Customer Blacklist',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Enhanced customer blacklist management for Odoo 18',
    'description': """
        This module enhances customer blacklist functionality by adding status management,
        history tracking, and contract restrictions for blacklisted customers.
    """,
    'depends': ['base', 'rental_customization','customer_info','rental_contract'],
    'data': [
        'security/blacklist_security.xml',
        'security/ir.model.access.csv',
        'views/blacklist_action_wizard_views.xml',
        'views/blacklist_unblock_wizard_views.xml',
        'views/blacklist_history_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': False,
}
