from odoo import fields, models

class BlacklistUnblockWizard(models.TransientModel):
    _name = 'blacklist.unblock.wizard'
    _description = 'Blacklist Unblock Wizard'

    reason = fields.Text(string='Reason for Unblock', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', default=lambda self: self._context.get('active_id'))

    def action_unblock(self):
        self.ensure_one()
        self.partner_id.write({
            'blacklist_status': 'running',
            'blacklist_reason': False
        })
        self.env['res.partner.blacklist.history'].create({
            'partner_id': self.partner_id.id,
            'action': 'unblocked',
            'type': 'unblocked',
            'reason': self.reason
        })
