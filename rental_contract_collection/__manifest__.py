# -*- coding: utf-8 -*-
{
    'name': "Rental Contract Collection",
    'summary': "Rental Contract Collection",
    'description': """Rental Contract Collection""",
    'author': "M.Deeb",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['rental_contract'],
    'data': [
        'security/ir.model.access.csv',
        'security/record_rule.xml',

        'data/rental_contract_sequence.xml',

        'wizard/collection_action_wiz.xml',
        'wizard/payment_grace_agreement_wiz.xml',

        'views/collection_setting.xml',
        'views/rental_contract.xml',
        'views/collection_report.xml',
        'views/payment_grace_agreement_report.xml',
        'views/menus.xml',
    ]
}
