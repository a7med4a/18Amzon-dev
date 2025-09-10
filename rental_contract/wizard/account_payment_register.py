from odoo import Command, models, fields, api, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        payment_vals.update(
            {'payment_type_selection': 'compensation' if self.line_ids[0].move_id.is_accident else ''})
        return payment_vals
