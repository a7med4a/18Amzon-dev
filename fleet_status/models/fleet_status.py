# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VehicleStatus(models.Model):
    _inherit = 'fleet.vehicle.state'
    
    type = fields.Selection([
        ('rented', 'Rented'),
        ('ready_to_rent', 'Ready To Rent'),
        ('under_maintenance', 'Under Maintenance'),
        ('accident_or_damage', 'Accident'),
        ('in_transfer', 'In Transfer'),
        ('stopped', 'Stopped'),
        ('damaged', 'Damaged'),
        ('in_service', 'In Service'),
        ('reserved', 'Reserved'),
        ('stolen', 'Stolen'),
        ('for_sale', 'For Sale'),
        ('for_sale', 'For Sale'),
        ('total_loss', 'Total Loss'),
        ('sold', 'Sold'),
        ('under_preparation', 'Under Preparation'),
        ('job_task', 'Job Task'),
    ], string='Type')
    
    @api.constrains('type')
    def _check_type(self):
        current_type_list = self.mapped('type')
        exist_type_list = self.env['fleet.vehicle.state'].search([('id', 'not in', self.ids)]).mapped('type')
        for type in current_type_list:
            if type in exist_type_list:
                raise ValidationError(_(f'{type} already exists'))
            

