from odoo import fields, models

class BlacklistActionWizard(models.TransientModel):
    _name = 'blacklist.action.wizard'
    _description = 'Blacklist Action Wizard'


    type = fields.Selection(string="Blacklist Status", selection=[("warning", "Warning"),("blocked", "Blocked")], required=True)
    reason = fields.Text(string='Reason', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', default=lambda self: self._context.get('active_id'))

    def action_apply(self):
        self.ensure_one()
        self.partner_id.write({
            'blacklist_status': self.type,
            'blacklist_reason': self.reason
        })
        self.env['res.partner.blacklist.history'].create({
            'partner_id': self.partner_id.id,
            'type': self.type ,
            'action': 'blocked' ,
            'reason': self.reason
        })
