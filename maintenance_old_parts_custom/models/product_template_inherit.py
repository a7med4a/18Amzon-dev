# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class JobOrderInherit(models.Model):
    _inherit = 'maintenance.job.order'

    old_spare_parts_ids = fields.One2many(comodel_name='old.spare.parts', inverse_name='maintenance_job_order_id',
                                   string="Old Spare Parts")

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'


    related_model_id = fields.Many2one('fleet.vehicle.model', string='Related Model')
    usage_type = fields.Selection(
        string='Usage Type',
        selection=[('original', 'Original'), ('copy', 'Copy'), ],
        required=False, )
    is_spare_part = fields.Boolean('Is Spare Part', default=False,compute='compute_is_spare_part',store=True)

    @api.depends('categ_id')
    def compute_is_spare_part(self):
        for rec in self:
            if rec.categ_id.purchase_type_id == self.env.ref('fleet_tracking_device.purchase_type_spare_parts'):
                rec.is_spare_part = True
            else:
                rec.is_spare_part = False

