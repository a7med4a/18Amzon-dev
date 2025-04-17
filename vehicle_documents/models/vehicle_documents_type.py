from email.policy import default

from odoo.exceptions import ValidationError
from odoo import models, fields, api, _



class VehicleDocumentsType(models.Model):
    _name = 'vehicle.documents.type'
    _description='Vehicle Document Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name="name"

    name = fields.Char(string="Name",tracking=True)
    reminder_users = fields.Boolean( string='Reminder Users',default=True,tracking=True)
    send_notification_before=fields.Integer()
    notified_user_ids = fields.Many2many('res.users', string='Notified Users')
    assign_date = fields.Boolean(string="Assign Dates",default=True,tracking=True)

