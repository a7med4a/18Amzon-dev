# -*- coding: utf-8 -*-
{
    'name': "Rental Contract Management",
    'summary': """Rental Contract Management""",
    'description': """Rental Contract Management""",
    'author': "M.Deep",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['rental_customization', 'customer_info', 'vehicle_info', 'additional_and_supplementary_services', 'fleet_manufacturer_custom'],
    'data': [
        'security/ir.model.access.csv',
        'views/vehicle_model_details.xml',
        'views/rental_contract.xml',
        'wizard/payment_register.xml',
    ],
}
