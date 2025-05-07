# -*- coding: utf-8 -*-
{
    'name': 'Vehicle Purchase ',
    'category': 'Insurance',
    'summary': 'Manage Vehicle Purchase',
    'author': '',
    'version': '18.0.0.1',
    'depends': ['base', 'fleet', 'purchase', 'contacts', 'accountant', 'fleet_status', 'account', 'account_asset'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/vehicle_purchase_sequence.xml',
        'views/vehicle_purchase_view.xml',
        'wizard/payment_register.xml',
        'wizard/bulk_installment_payment_wizard.xml',
        'wizard/import_installments_wizard.xml',
        'views/vehicle_purchase_view.xml',
        'views/vehicle_purchase_quotation_view.xml',
        'views/fleet_vehicle_inherit_view.xml',
        'views/installment_board_views.xml',
        'views/bill_setting.xml',
        'views/bill.xml',
        'views/vehicle_purchase_order_view.xml',
        'views/vehicle_purchase_accounting.xml',

    ],
}
