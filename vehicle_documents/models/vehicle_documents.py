
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta


class VehicleDocuments(models.Model):
    _name = 'vehicle.documents'
    _description='Vehicle Documents'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    vehicle_id = fields.Many2one('fleet.vehicle', required=True)
    license_plate=fields.Char(related='vehicle_id.license_plate')
    description = fields.Text( string="Description",required=False)
    vehicle_document_type_id =fields.Many2one('vehicle.documents.type', required=True)
    active = fields.Boolean(default=True)
    assign_date = fields.Boolean(related="vehicle_document_type_id.assign_date")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    attachment_ids=fields.Many2many('ir.attachment', 'vehicle_attachment_rel', 'vehicle_id', 'attachment_id', string="Attachments",required=True)
    document_status = fields.Selection(
        string='Document Status',
        selection=[('running', 'Running'),('expired', 'Expired')],
        default='running',copy=False,readonly=True)

    @api.model
    def _cron_check_document_status(self):
        records = self.search([])
        for rec in records :
            if rec.end_date :
                expire_date = rec.end_date + timedelta(days=1)
                if expire_date <= date.today() :
                    rec.document_status = 'expired'

    def notified_users_before(self):
        records = self.search([]).filtered('end_date')
        for rec in records:
            if rec.vehicle_document_type_id and rec.vehicle_document_type_id.reminder_users and rec.vehicle_document_type_id.notified_user_ids :
                for user in rec.vehicle_document_type_id.notified_user_ids:
                    notify_date = rec.end_date - timedelta(days=10)
                    if notify_date <=  date.today():
                        message = _("Dear %s, End date of your Vehicle document is at %s . Please renew it.") % (user.name,rec.end_date)
                        user.partner_id.sudo().message_post(body=message, message_type='notification',subtype_xmlid='mail.mt_note')
                        self.env['bus.bus']._sendone(
                            user.partner_id,
                            'simple_notification', {
                                'title': _('Warning'),
                                'type': 'danger',
                                'message': message,
                                'sticky': True,
                            }
                        )