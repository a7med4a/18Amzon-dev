# -*- coding: utf-8 -*-
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta



class PreventiveMaintenanceConfig(models.Model):
    _name = 'preventive.maintenance.config'
    _description="Preventive Maintenance Config"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    model_id = fields.Many2one(comodel_name='fleet.vehicle.model',required=True,tracking=True)
    preventive_maintenance_line_ids=fields.One2many('preventive.maintenance.config.line','preventive_maintenance_id')

    def preventive_maintenance_cron(self):
        configs=self.env['preventive.maintenance.config'].search([])
        for config in configs:
            vehicles_related=self.env['fleet.vehicle'].search([('model_id','=',config.model_id.id)])
            print(vehicles_related,"vehicles_related")
            for line in config.preventive_maintenance_line_ids:
                if line.odometer>0 and not line.is_notified:
                    print(line.odometer,"line.odometer")
                    for vehicle in vehicles_related:
                        print(vehicle.odometer,"vehicle.odometer")
                        if vehicle.odometer>line.odometer:
                            self.env['preventive.maintenance.notification'].create({
                                'vehicle_id':vehicle.id,
                                'name':vehicle.display_name,
                                'model_id':vehicle.model_id.id,
                                'vin_sn':vehicle.vin_sn,
                                'license_plate':vehicle.license_plate,
                                'description':line.name
                            })
                            for use in line.assign_user_ids:
                                self.env['bus.bus']._sendone(
                                    use.partner_id,
                                    'simple_notification',
                                    {
                                        'title': _("Preventive Maintenance Notification"),
                                        'message': _("Vehicle %s is under preventive maintenance. Reason: %s") % (
                                            vehicle.display_name,
                                            line.name
                                        ),
                                        'type': 'warning',
                                        'sticky': True
                                    }
                                )
                            line.is_notified=True



class PreventiveMaintenanceConfigLine(models.Model):
    _name = 'preventive.maintenance.config.line'
    _description="Preventive Maintenance Config line"

    name=fields.Char(string="Description",required=True)
    odometer=fields.Integer(required=True)
    assign_user_ids=fields.Many2many('res.users',string="Assign Users",required=True)
    preventive_maintenance_id = fields.Many2one(comodel_name='preventive.maintenance.config',required=True)
    is_notified=fields.Boolean(string="Is Notified",default=False)

class PreventiveMaintenanceNotification(models.Model):
    _name = 'preventive.maintenance.notification'
    _description="Preventive Maintenance Notification"

    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle')
    name=fields.Char(related='vehicle_id.display_name',string="Name")
    model_id = fields.Many2one(comodel_name='fleet.vehicle.model',
                               string="Model", related='vehicle_id.model_id', store=True)
    vin_sn = fields.Char(string="Chassis Number",related='vehicle_id.vin_sn', store=True)
    license_plate = fields.Char(string="License Plate",related='vehicle_id.license_plate', store=True)
    description=fields.Char(string="Description")
