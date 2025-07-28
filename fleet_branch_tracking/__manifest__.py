# -*- coding: utf-8 -*-
{
    'name': "Fleet Branch Tracking",
    'summary': "Fleet Branch Tracking",
    'description': """Fleet Branch Tracking""",
    'author': "M.Deeb",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['rental_contract', 'branch_routs'],
    'data': [
        'security/ir.model.access.csv',
        'views/fleet_branch_tracking.xml',
        'views/fleet_vehicle.xml',
    ],
}
