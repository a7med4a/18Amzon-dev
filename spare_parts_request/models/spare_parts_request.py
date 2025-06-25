
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _

class SparePartsRequest(models.Model):
    _name = 'spare.parts.request'
    _description='Spare Parts Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name="name"

    name = fields.Char(string="Name",default=lambda self: _('New'),readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,readonly=True,
                                 default=lambda self: self.env.company)
    request_notes = fields.Text( string="Request Notes",required=False)
    request_date = fields.Datetime(string="Request Date", default=fields.Datetime.now, readonly=True)
    route_id = fields.Many2one('stock.route', string='Routes', readonly=True,tracking=True,domain=lambda self: [('id', 'in', self.env.branch.route_ids.ids)])
    location_src_id = fields.Many2one('stock.location', string='Source Location', readonly=True,compute="_compute_locations")
    location_dest_id = fields.Many2one('stock.location', string='Destination Location', readonly=True)
    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group', copy=False)
    transfer_ids = fields.One2many(comodel_name='stock.picking', inverse_name='spare_parts_request_id',
                                   string="Transfer")
    spare_parts_line_ids = fields.One2many(
        comodel_name='spare.parts.request.line',
        inverse_name='spare_parts_request_id',
        string='Spare Parts lines',
        required=False)
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),('in_progress', 'In Progress'), ('done', 'Done'),('cancelled', 'Cancelled'),],
        default='draft',copy=False,tracking=True )

    @api.depends('route_id')
    def _compute_locations(self):
        for rec in self:
            rec.location_src_id=False
            rec.location_dest_id=False
            if rec.route_id:
                rec.location_src_id = rec.route_id.rule_ids[0].location_src_id.id
                rec.location_dest_id = rec.route_id.rule_ids[-1].location_dest_id.id

    @api.model_create_multi
    def create(self, vals_list):
        print(self.env.branches, ">>>>>>>>>>>>>>>>>>>>>")
        for vals in vals_list:
            sequence = self.env['ir.sequence'].next_by_code('seq.spate.parts.request') or '/'
            print(sequence,">>>>>>>>>>>>>>>>>>>>>>>>")
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = sequence
        return super().create(vals_list)

    def action_in_progress(self):
        for rec in self:
            self.action_request_spare_parts()
            rec.state='in_progress'
    def action_done(self):
        for rec in self:
            if any(rec.spare_parts_line_ids.filtered(
                    lambda component: component.picking_status == 'in_progress')) or any(
                    rec.spare_parts_line_ids.filtered(lambda component: component.spart_part_request == 'pending')):
                raise ValidationError(_('Picking Status must be Done or Cancelled before closing Spare parts Request'))
            rec.state='done'
    def action_cancel(self):
        for rec in self:
            rec.state='cancelled'
    def action_reset_draft(self):
        for rec in self:
            rec.state='draft'

    def action_request_spare_parts(self):
        """
        Request spare parts  using Odoo's standard procurement system.
        This method creates procurement orders for each component that needs spare parts,
        utilizing warehouse routes and stock rules to generate proper stock movements.
        """
        for rec in self:
            if not rec.spare_parts_line_ids:
                raise ValidationError(_('No lines found to Request Spare Parts'))

            if rec.transfer_ids and all([component.spart_part_request != 'pending' for component in rec.spare_parts_line_ids]):
                raise ValidationError(_('You have already requested Spare Parts'))

            # Get the route from maintenance team
            route = rec.route_id
            if not route:
                raise ValidationError(_('No route defined for the maintenance team'))

            # Create or get procurement group
            if not rec.procurement_group_id:
                rec.procurement_group_id = self.env['procurement.group'].create({
                    'name': rec.name,
                    'move_type': 'direct',
                    'partner_id': self.env.company.partner_id.id,
                })

            procurement_group = rec.procurement_group_id

            # Get destination location from the route's last rule
            destination_location = False
            if route.rule_ids:
                destination_location = route.rule_ids[-1].location_dest_id

            if not destination_location:
                raise ValidationError(_('Could not determine destination location from route'))

            procurements = []
            errors = []

            # Create procurement values for each component
            for spare in rec.spare_parts_line_ids.filtered(lambda x: x.spart_part_request == 'pending'):
                # Get the product from product_id (product.template)
                product_variant = spare.product_id.product_variant_id
                if not product_variant:
                    errors.append(_('No product variant found for %s') % spare.product_id.name)
                    continue

                # Create procurement values - corrected format for Odoo 18
                values = {
                    'group_id': procurement_group,
                    'spare_parts_request_id': rec.id,
                    'date_planned': fields.Datetime.now(),
                    'product_id': product_variant,
                    'product_qty': spare.demand_qty,
                    'product_uom': spare.uom_id,
                    'location_id': destination_location,
                    'name': rec.name,
                    'origin': rec.name,
                    'company_id': rec.company_id or self.env.company,
                    'route_ids': route,  # Corrected format for many2many field
                }

                # Add to procurements list in the correct format for Odoo 18
                procurements.append(self.env['procurement.group'].Procurement(
                    product_variant,
                    spare.demand_qty,
                    spare.uom_id,
                    destination_location,
                    rec.name,
                    rec.name,
                    rec.company_id or self.env.company,
                    values
                ))


            # If there are errors, raise them
            if errors:
                raise ValidationError('\n'.join(errors))

            # Run procurements with the correct format
            if procurements:
                print(procurements,"Ali >>>>>>>>>>>>>>")
                self.env['procurement.group'].run(procurements)

                # Mark components as requested
                for spare in rec.spare_parts_line_ids.filtered(lambda x: x.spart_part_request == 'pending'):
                    spare.spart_part_request = 'done'

    def action_view_transfers(self):
        for rec in self :
            if rec.transfer_ids:
                return {
                    'name': 'Transfers',
                    'type': 'ir.actions.act_window',
                    'res_model': 'stock.picking',
                    'view_mode': 'list,form',
                    'domain': [('id', 'in', rec.transfer_ids.ids)],
                }
            else:
                raise ValidationError(_("No RFQ Created for this PR Request!"))
        return True


class SpareParstRequestLine(models.Model):
    _name = 'spare.parts.request.line'
    _description = "Spare Parst Request Line"

    spare_parts_request_id = fields.Many2one(comodel_name='spare.parts.request')
    product_category_id = fields.Many2one(comodel_name='product.category', string='Product Category', required=True)
    product_id = fields.Many2one(comodel_name='product.template', string='Product', required=True)
    uom_id = fields.Many2one("uom.uom", related='product_id.uom_id', string="Unit Of Measure",
                             export_string_translation=False)
    demand_qty = fields.Float(string="Demand")
    done_qty = fields.Float(string="Done Quantity",compute="_compute_picking_status")
    spart_part_request = fields.Selection(string='Spart part Request',
                                          selection=[('pending', 'Pending'), ('done', 'Done'), ], required=False,
                                          default="pending")
    picking_status = fields.Selection(string='Picking Status',
                                      selection=[('in_progress', 'In Progress'), ('done', 'Done'),
                                                 ('cancelled', 'Cancelled'), ], required=False, default="in_progress",compute="_compute_picking_status")
    product_category_domain = fields.Binary(string="Product Category domain",
                                            help="Dynamic domain used for Product Category",)


    def _compute_picking_status(self):
        for component in self:
            picking_moves = component.spare_parts_request_id.transfer_ids
            print("picking_moves ===> ",picking_moves)
            if picking_moves:
                move_lines= picking_moves[-1].move_line_ids
                done_qty = sum(move_lines.mapped('qty_done'))
                if all([move.state == 'done' for move in picking_moves]):
                    component.picking_status = 'done'
                    component.done_qty = done_qty

                elif all([move.state == 'cancel' for move in picking_moves]):
                    component.picking_status = 'cancelled'
                    component.done_qty = 0

                else:
                    component.picking_status = 'in_progress'
                    component.done_qty = 0
            else:
                component.picking_status = 'in_progress'
                component.done_qty = 0


    def unlink(self):
        if self.spart_part_request == 'done':
            raise ValidationError(
                _("You can't delete line which is already spare part requests"))
        return super().unlink()



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    spare_parts_request_id = fields.Many2one(comodel_name='spare.parts.request')


class StockMove(models.Model):
    _inherit = 'stock.move'

    spare_parts_request_id = fields.Many2one(comodel_name='spare.parts.request')

    def _get_new_picking_values(self):
        """Override to add maintenance fields to new pickings"""
        vals = super(StockMove, self)._get_new_picking_values()

        # Check if this move is related to a maintenance job order
        if self.group_id and self.group_id.name:
            # Try to find the maintenance job order
            spare_parts_request = self.env['spare.parts.request'].search([
                ('procurement_group_id', '=', self.group_id.id)
            ], limit=1)

            if spare_parts_request:
                vals.update({
                    'spare_parts_request_id': spare_parts_request.id,
                    'origin': spare_parts_request.name,
                })

        return vals


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def _run_scheduler_tasks(self, use_new_cursor=False, company_id=False):
        """Override to properly link stock moves to spare parts request"""
        res = super(ProcurementGroup, self)._run_scheduler_tasks(use_new_cursor=use_new_cursor, company_id=company_id)

        # Link stock moves to job order components
        if use_new_cursor:
            self.env.cr.commit()

        return res

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id,
                               values):
        """Override to add maintenance fields to stock moves"""
        move_values = super(ProcurementGroup, self)._get_stock_move_values(
            product_id, product_qty, product_uom, location_id, name, origin, company_id, values)

        # Add job order component if present in values
        if values.get('spare_parts_request_id'):
            move_values['spare_parts_request_id'] = values['spare_parts_request_id']

        return move_values
