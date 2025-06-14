# -*- coding: utf-8 -*-
{
    'name': 'STA Integration',
    'version': '18.0.1.0.0',
    'category': 'Rental',
    'summary': 'Integration with Saudi Transport Authority (STA) for rental contracts',
    'description': """
        This module provides integration with the Saudi Transport Authority (STA) 
        for managing rental contracts. It allows synchronization of rental contracts,
        branches, and rental policies between Odoo and STA systems.
        
        Features:
        - Create and manage STA rental contracts
        - Synchronize branches with STA
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
        'data/sta_data.xml',
        'views/sta_config_settings_views.xml',
        'views/sta_contract_views.xml',
        'views/sta_branch_views.xml',
        'views/sta_rent_policy_views.xml',
        # 'wizards/sta_send_otp_wizard_views.xml',
        # 'wizards/sta_cancel_contract_wizard_views.xml',
        # 'wizards/sta_suspend_contract_wizard_views.xml',
        # 'wizards/sta_close_contract_wizard_views.xml',
        'views/menuitems.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

