# -*- coding: utf-8 -*-

import ast
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MaintenanceWorkshop(models.Model):
    _name = 'maintenance.workshop'
    _description="Maintenance Workshop"


    name = fields.Char('Workshop Name', required=True)
    type=fields.Selection([('internal', 'Internal'), ('external', 'External')], string='Type', default="internal")
    repair_task_ids = fields.One2many('workshop.repair.task','maintenance_workshop_id')
    workshop_product_category_ids = fields.One2many('workshop.product.category','maintenance_workshop_id')


class WorkshopRepairTask(models.Model):
    _name = 'workshop.repair.task'
    _description="Workshop Repair Task"

    name = fields.Char('Repair Task', required=True)
    maintenance_workshop_id = fields.Many2one(
        comodel_name='maintenance.workshop',
        string='Maintenance_workshop_id',
        required=False)

class WorkshopProductCategory(models.Model):
    _name = 'workshop.product.category'
    _description="Workshop Product Category"

    product_category = fields.Many2one(
        comodel_name='product.category',
        string='Product Category',
        required=True)
    maintenance_workshop_id = fields.Many2one(
        comodel_name='maintenance.workshop',
        string='Maintenance_workshop_id',
        required=False)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_technical=fields.Boolean(default=False)
    cost_per_hour=fields.Float(string="Cost/Hour")
