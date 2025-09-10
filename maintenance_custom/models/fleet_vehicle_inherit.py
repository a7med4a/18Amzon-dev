# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from lxml import etree

class FleetVehicleInherit(models.Model):
    _inherit = 'fleet.vehicle'

    def action_view_maintenance_request(self):
        return {
            'name': 'Maintenance',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'maintenance.request',
            'type': 'ir.actions.act_window',
            'domain': [('vehicle_id', '=', self.id)]
        }

    def action_view_quick_maintenance_request(self):
        return {
            'name': 'Quick Maintenance',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'quick.maintenance.request',
            'type': 'ir.actions.act_window',
            'domain': [('vehicle_id', '=', self.id)]
        }

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id, view_type, **options)
        if (view_type == 'kanban' or view_type == 'list') and options.get('action_id') == self.env.ref('maintenance_custom.maintenance_request_fleet_vehicle_action').id:
            doc = etree.XML(res['arch'])
            list_view = doc.xpath("//list")
            kanban_view = doc.xpath("//kanban")
            if list_view:
                list_view[0].set("create", "0")
            if kanban_view:
                kanban_view[0].set("create", "0")
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
