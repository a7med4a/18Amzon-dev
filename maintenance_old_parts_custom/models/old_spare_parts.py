# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class StockMove(models.Model):
    _inherit = 'stock.move'
    _description = "Stock Moves"

    old_spare_parts_id=fields.Many2one(
        comodel_name='old.spare.parts',
        string='Old Spare Parts'
    )
    maintenance_job_order_id = fields.Many2one(
        comodel_name='maintenance.job.order',
        string='Job Order'
    )
    maintenance_external_job_order_id = fields.Many2one(
        comodel_name='maintenance.external.job.order',
        string='External Job Order'
    )


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _description = "Stock Picking"

    is_old_spare_parts = fields.Boolean(string='Is Old Spare Parts', default=False)

class OldSpareParts(models.Model):
    _name = 'old.spare.parts'
    _description = "Old Spare Parts"

    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Product',
        required=True,
        domain="[('usage_type', '=', 'copy')]"
    )
    maintenance_job_order_id = fields.Many2one(
        comodel_name='maintenance.job.order',
        string='Job Order'
    )
    maintenance_external_job_order_id = fields.Many2one(
        comodel_name='maintenance.external.job.order',
        string='External Job Order'
    )
    maintenance_request_id = fields.Many2one(
        comodel_name='maintenance.request',
        string='Maintenance Request',
        required=True
    )
    spare_part_type = fields.Selection(
        selection=[('reusable', 'Reusable'), ('disposable', 'Disposable')],
        string='Spare Part Type',
        required=True
    )
    count = fields.Integer(string='Count', default=0)
    name = fields.Char(string='Description')


    def action_apply_all(self):
        """Create a stock transfer for selected spare parts."""
        if not self:
            raise ValidationError(_('No spare parts selected.'))

        if any(line.count <= 0 for line in self):
            raise ValidationError(_('Count must be greater than 0 for all spare parts.'))

        first_line = self[0]
        maintenance_request = first_line.maintenance_request_id
        if not maintenance_request:
            raise ValidationError(_('No maintenance request specified.'))

        picking_type = maintenance_request.maintenance_team_id.old_spare_parts_operation_type_id
        if not picking_type:
            raise ValidationError(_('No picking type configured for the maintenance team: %s.') % maintenance_request.maintenance_team_id.name)

        picking_vals = {
            'picking_type_id': picking_type.id,
            'maintenance_request_id': maintenance_request.id,
            'is_old_spare_parts': True,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'state': 'draft',
            'origin': maintenance_request.name,
            'company_id': self.env.company.id,
        }

        picking = self.env['stock.picking'].create(picking_vals)
        for line in self:
            if not line.product_id:
                raise ValidationError(_('No product specified for spare part: %s') % (line.name or 'Unnamed'))
            move_vals = {
                'picking_id': picking.id,
                'old_spare_parts_id': line.id,
                'product_id': line.product_id.id,
                'product_uom_qty': line.count,
                'maintenance_job_order_id': line.maintenance_job_order_id.id,
                'maintenance_external_job_order_id': line.maintenance_external_job_order_id.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'name': line.name or line.product_id.name,
                'state': 'draft',
            }
            self.env['stock.move'].create(move_vals)

        return {
            'name': _('Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': picking.id,
            'target': 'current',
        }