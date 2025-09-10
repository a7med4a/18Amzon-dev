{
    'name': 'Fleet Limousine',
    'category': 'Amazon/Limousine',
    'summary': 'Manage fleet limousine and driver',
    'author': 'Hazem Essam El-DIN',
    'version': '18.0.0.0.1',
    'depends': [
        'base',
        'fleet',
        'sign',

        'vehicle_info',
        'customer_info',
        'fleet_status',
        'fleet_master_configuration',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        'data/ir_cron_data.xml',

        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rules.xml',

        'views/fleet_vehicle_views.xml',
        'views/res_partner_views.xml',
        'views/res_config_settings_views.xml',
        'views/limousine_pricing_views.xml',
        'views/limousine_fines_config_views.xml',
        'views/limousine_contract_views.xml',
        'views/limousine_contract_timesheet_views.xml',

        'wizard/payment_register.xml',
    ],
}
