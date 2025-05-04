from odoo import models, api ,_
from odoo.exceptions import UserError

class RentalContract(models.Model):
    _inherit = 'rental.contract'

    @api.constrains('partner_id')
    def _check_blacklist_status(self):
        for contract in self:
            if contract.partner_id.blacklist_status == 'blocked':
                raise UserError(
                    _("Cannot create rental contract for customer %s. Reason: %s") % (
                        contract.partner_id.name,
                        contract.partner_id.blacklist_reason or 'Blocked'
                    )
                )


    @api.onchange('partner_id')
    def _onchange_partner_id_blacklist(self):
        if self.partner_id.blacklist_status == 'warning':
            self.env['bus.bus']._sendone(
                self.env.user.partner_id,
                'simple_notification', {
                    'title': _('Warning'),
                    'type': 'danger',
                    'message':_("Customer %s is under warning. Reason: %s") % (
                        self.partner_id.name,
                        self.partner_id.blacklist_reason or 'N/A'
                    ),
                    'sticky': True,
                }
            )

