# -*- coding: utf-8 -*-
{
    'name': "Fleet Status",
    'summary': """Add Customization to fleet status""",
    'description': """Add Customization to fleet status""",
    'author': "M.Deep",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['fleet', 'branches_management', 'vehicle_info'],
    'data': [
        'data/fleet_status.xml',
        'data/cron.xml',
        'security/ir.model.access.csv',
        'views/fleet_status.xml',
        'views/fleet_status_log.xml',
        'views/fleet_vehicle.xml',
    ],
    'pre_init_hook': 'pre_init_hook',
}
