# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class JobOrderInherit(models.Model):
    _inherit = 'maintenance.job.order'

    old_spare_parts_ids = fields.One2many(comodel_name='old.spare.parts', inverse_name='maintenance_job_order_id',
                                   string="Old Spare Parts")
    transfer_old_spare_parts_count=fields.Integer(compute="_compute_transfer_old_spare_parts_count")

    @api.depends('old_spare_parts_ids')
    def _compute_transfer_old_spare_parts_count(self):
        for job in self:
            job.transfer_old_spare_parts_count=len(job.old_spare_parts_ids.ids)

class ExternalJobOrderInherit(models.Model):
    _inherit = 'maintenance.external.job.order'

    old_spare_parts_ids = fields.One2many(comodel_name='old.spare.parts', inverse_name='maintenance_external_job_order_id',
                                   string="Old Spare Parts")
    transfer_old_spare_parts_count=fields.Integer(compute="_compute_transfer_old_spare_parts_count")

    @api.depends('old_spare_parts_ids')
    def _compute_transfer_old_spare_parts_count(self):
        for job in self:
            job.transfer_old_spare_parts_count=len(job.old_spare_parts_ids.ids)

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'


    related_model_ids = fields.Many2many('fleet.vehicle.model', string='Related Models')
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

