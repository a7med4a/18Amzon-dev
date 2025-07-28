# -*- coding: utf-8 -*-
{
    'name': 'STA Integration - Saudi Transport Authority',
    'version': '18.0.1.0.0',
    'category': 'Integration/Transport',
    'summary': 'Complete integration with Saudi Transport Authority (STA) for vehicle rental management',
    'description': """
Saudi Transport Authority Integration
=====================================

This module provides comprehensive integration with the Saudi Transport Authority (STA) 
for managing vehicle rental contracts in compliance with Saudi regulations.

Key Features:
=============
• Complete Contract Management: Create, save, suspend, cancel, and close rental contracts
• Real-time Synchronization: Automatic sync with STA systems for branches and policies  
• OTP Verification: Secure contract verification using OTP system
• API Lookup Tool: Advanced testing and monitoring tool for STA endpoints
• Multi-environment Support: Works with both staging and production STA environments
• Comprehensive Logging: Detailed logs for all API interactions and responses
• Error Handling: Robust error handling with user-friendly notifications
• Security: Multi-layer authentication and secure data transmission

Supported Operations:
====================
✓ Contract Creation and Management
✓ OTP Generation and Verification  
✓ Branch Synchronization
✓ Rental Policy Management
✓ Contract Status Tracking
✓ Real-time API Testing
✓ Comprehensive Reporting

Technical Features:
==================
• RESTful API Integration
• JSON Data Processing
• HTTPS/SSL Security
• Timeout Management
• Connection Pooling
• Response Caching
• Multi-language Support (Arabic/English)

Requirements:
============
This module requires active STA API credentials and internet connectivity.
Contact Saudi Transport Authority for API access and credentials.
    """,
    'author': 'Ahmed Amen',
    'website': 'https://sta.gov.sa',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'base_setup',
        'web',
        'rental_contract',
        'branches_management',
        'customer_info',
        'vehicle_info',
        'fleet_status',
        'rental_customization',
    ],
    'external_dependencies': {
        'python': ['requests', 'json', 'datetime'],
    },
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/security.xml',

        # Data
        'data/sta_data.xml',

        # Views
        'views/sta_config_settings_views.xml',
        'views/sta_contract_views.xml',
        'views/sta_branch_views.xml',
        'views/sta_rent_policy_views.xml',
        'views/menuitems.xml',
        'views/res_country_view.xml',

        # Wizards
        'wizards/response_viewer.xml',
        'wizards/api_lookup_view.xml',
        'wizards/sta_wizards_views.xml',
    ],
    'demo': [
        # 'demo/sta_demo_data.xml',  # يمكن إضافة بيانات تجريبية لاحقاً
    ],
    'images': [
        'static/description/icon.png',
    ],
    'assets': {
        'web.assets_backend': [
            # 'sta_integration/static/src/css/sta_styles.css',  # يمكن إضافة CSS مخصص
            # 'sta_integration/static/src/js/sta_widgets.js',   # يمكن إضافة JS مخصص
        ],
    },
    'installable': True,
    'application': True,  # تغيير إلى True لأنه مديول مستقل
    'auto_install': False,
    'sequence': 100,
    'price': 0.0,  # إضافة السعر
    'currency': 'USD',
    'live_test_url': '',  # يمكن إضافة رابط للتجربة
    'support': 'ahmed.amen@example.com',  # يمكن إضافة إيميل الدعم

    # Technical Information
    'maintainers': ['Ahmed Amen'],
    'contributors': [
        'Ahmed Amen - Lead Developer',
        # يمكن إضافة المساهمين الآخرين
    ],

    # Module Information
    'development_status': 'Production/Stable',
    'maturity': 'Stable',

    # Documentation
    'documentation': '''
For detailed documentation, please visit:
- Installation Guide: See INSTALL.md
- User Manual: See README.md  
- API Documentation: Available in module
- Support: Contact ahmed.amen@example.com
    ''',

    # Post-install message
    'post_init_hook': None,  # يمكن إضافة hook للتشغيل بعد التثبيت
    'uninstall_hook': None,  # يمكن إضافة hook للتشغيل قبل الحذف

    # Compatibility
    'odoo_version': '18.0',
    'python_requires': '>=3.8',

    # Additional metadata
    'cloc_exclude': [
        'static/**/*',
        'demo/**/*',
        'tests/**/*',
    ],
}