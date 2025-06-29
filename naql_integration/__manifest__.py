# -*- coding: utf-8 -*-
{
    'name': 'Naql Integration',
    'version': '18.0.1.0.0',
    'category': 'Rental',
    'summary': 'Integration with Naql for rental contracts',
    'description': """
        This module provides integration with Naql 
        for managing rental contracts. It allows synchronization of rental contracts,
        branches, and rental policies between Odoo and Naql systems.
        
        Features:
        - Create and manage Naql rental contracts
        - Synchronize branches with Naql
        - Manage rental policies
        - Send OTP for contract verification
        - Cancel, suspend, and close contracts
        - Real-time status updates
    """,
    'author': 'Ahmed Amen',
    'website': '',
    'depends': [
        'base',
        'rental_contract',
        'branches_management',
        'customer_info',
        'vehicle_info',
        'fleet_status',
        'rental_customization',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/naql_data.xml',
        'views/naql_config_settings_views.xml',
        'views/naql_contract_views.xml',
        'views/naql_branch_views.xml',
        'views/naql_rent_policy_views.xml',
        # 'wizards/naql_send_otp_wizard_views.xml',
        # 'wizards/naql_cancel_contract_wizard_views.xml',
        # 'wizards/naql_suspend_contract_wizard_views.xml',
        # 'wizards/naql_close_contract_wizard_views.xml',
        'views/menuitems.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}



