# -*- coding: utf-8 -*-
{
    'name': "Branch Routs",
    'summary': "Add Branch Routs Cycle To Product",
    'description': """Add Branch Routs Cycle To Product""",
    'author': "M.Deep",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['fleet_master_configuration', 'hr_fleet', 'vehicle_info', 'fleet_status'],
    'data': [
        'security/ir.model.access.csv',
        'security/rule.xml',
        'data/branch_routs_sequence.xml',
        'views/res_partner.xml',
        'views/hr_employee.xml',
        'views/fleet_vehicle.xml',
        'views/vehicle_routes.xml',
        'views/fleet_status.xml',
        'views/branch_routs.xml',
        'views/menu_items.xml',
    ],
}
