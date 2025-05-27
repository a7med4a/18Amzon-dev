# -*- coding: utf-8 -*-
{
    'name': "Fleet Manufacturer Custom",

    'summary': "",

    'description': """""",

    'author': "",
    'version': '0.1',
    'depends': ['base', 'fleet', 'mail', 'branches_management'],

    'data': [
        'security/ir.model.access.csv',
        'data/cron.xml',
        'views/fleet_manufacturer_inherit.xml',
        'views/fleet_manufacturer_cron_inherit.xml',
        'views/fleet_vehicle_model_detail.xml',
    ],
}
