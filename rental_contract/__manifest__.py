# -*- coding: utf-8 -*-
{
    'name': "Rental Contract Management",
    'summary': """Rental Contract Management""",
    'description': """Rental Contract Management""",
    'author': "M.Deep",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['rental_customization', 'customer_info', 'vehicle_info', 'additional_and_supplementary_services', 'fleet_manufacturer_custom', 'fleet_status', 'fleet_accident', 'fleet_damage'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        'security/record_rule.xml',
        # Data views
        'data/rental_contract_sequence.xml',
        'data/contract_server_action.xml',
        'data/cron.xml',
        # Wizard views
        'wizard/payment_register.xml',
        'wizard/fines_discount_wiz.xml',
        # Model views
        'views/res_company.xml',
        'views/vehicle_model_details.xml',
        'views/contract_fines_discount_config.xml',
        'views/additional_supplementary_services.xml',
        'views/rental_contract_lines.xml',
        'views/rental_setting.xml',
        'views/account_move.xml',
        'views/contract_schedular_invoice_log.xml',
        'views/fleet_accident.xml',
        'views/fleet_damage.xml',
        'views/rental_contract.xml',
        'views/contract_source.xml',

    ],
}
