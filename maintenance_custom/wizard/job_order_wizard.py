# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MaintenanceJobOrderWizard(models.TransientModel):
    _name = 'maintenance.job.order.wizard'
    _description = 'Job Order Wizard'

    maintenance_request_id = fields.Many2one(comodel_name='maintenance.request',string='Maintenance Request Number',required=True)
    maintenance_workshop_id = fields.Many2one(comodel_name='maintenance.workshop',string='Maintenance Workshop',required=True)
    repair_task_ids = fields.Many2many('workshop.repair.task',string="Repair Tasks")
    technicians_ids = fields.Many2many('hr.employee',required=True)
    job_order_type = fields.Selection(
        string='Job_order_type',
        selection=[('internal', 'Internal'),
                   ('external', 'External'), ],
        required=True,default='internal' )


    def action_create_job_order(self):
        for rec in self :
            vals = {'maintenance_request_id': rec.maintenance_request_id.id,'maintenance_workshop_id': rec.maintenance_workshop_id.id, 'repair_task_ids': rec.repair_task_ids.ids,
                    'technicians_ids': rec.technicians_ids.ids, 'job_order_creation_date': fields.Datetime.now()}
            if rec.job_order_type == 'internal' :
                self.env['maintenance.job.order'].create(vals)
            if rec.job_order_type == 'external' :
                self.env['maintenance.external.job.order'].create(vals)

    @api.onchange('maintenance_workshop_id')
    def _remove_repairs_technician_related(self):
        for job in self:
            job.repair_task_ids=[(5,0,0)]
            job.technicians_ids=[(5,0,0)]
