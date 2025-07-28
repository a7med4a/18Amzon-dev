from email.policy import default

from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from datetime import date
import io
import xlsxwriter
import base64
from datetime import datetime, date, timedelta


class FleetDamage(models.Model):
    _name = 'fleet.damage'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "name"

    name = fields.Char(string="Reference",
                       copy=False, readonly=True, default="New")
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',  string='License Plate', required=True, tracking=True)
    model_id = fields.Many2one(comodel_name='fleet.vehicle.model',
                               string="Model", related='vehicle_id.model_id', store=True)
    category_id = fields.Many2one(comodel_name='fleet.vehicle.model.category',
                                  string="category", related='vehicle_id.category_id', store=True)
    customer_id = fields.Many2one(comodel_name='res.partner', string="Customer", domain=[(
        "company_type", "=", 'person'), ('create_from_rental', '=', True)], store=True, required=True, tracking=True)
    id_no = fields.Char(related="customer_id.id_no", readonly=True)
    evaluation_type = fields.Selection([('internal', "Internal"), (
        'external', "External")], string="Evaluation Type", default='internal', tracking=True)
    evaluation_party_id = fields.Many2one(
        comodel_name='fleet.accident.evaluation.party', string="Evaluation Party", tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', default=lambda self: self.env.company.id, domain=lambda self: [
                                 ('id', 'in', self.env.user.company_ids.ids)], string='Company', required=False, tracking=True)
    evaluation_report_ids = fields.One2many(
        'damage.evaluation.report', 'damage_id', string='Evaluation Report')
    confirmed_evaluation_report_id = fields.Many2one(
        'damage.evaluation.report', string='Confirmed Evaluation')
    evaluation_ids = fields.One2many(
        comodel_name='fleet.evaluation', inverse_name='fleet_damage_id', string='Evaluations', related="confirmed_evaluation_report_id.evaluation_ids")
    evaluation_count = fields.Integer(
        'Payment Count', compute='_compute_evaluation_count', store=True)
    total_without_tax = fields.Float(
        string='Total Without Tax', compute="_compute_total_amount")
    total_tax = fields.Float(
        string='Total Tax', compute="_compute_total_amount")
    total_include_tax = fields.Float(
        string='Total Include Tax', compute="_compute_total_amount")
    note = fields.Html(string='Note', required=False)
    invoice_id = fields.Many2one(
        comodel_name='account.move', string='Invoice_id', required=False)
    source = fields.Selection(
        [('rental', "Rental"), ('none', "None")], string="Source", default='none')
    state = fields.Selection([('draft', "Draft"), ('waiting_evaluation', "Waiting Evaluation"), (
        'charged', "Charged"), ('cancelled', "Cancelled")], string="State", default='draft', tracking=True)
    state_color = fields.Integer(compute="_compute_state_color")
    invoice_fleet_damage = fields.Selection([
        ('invoiced', 'Invoiced'),
        ('none', 'None')], string='Invoice Damage', readonly=True, compute="_compute_invoice_fleet_damage")

    @api.depends('state')
    def _compute_state_color(self):
        """Assign colors to states for the badge widget"""
        color_mapping = {
            'draft': 1,
            'waiting_evaluation': 1,
            'charged': 10,
            'cancelled': 5
        }
        for record in self:
            record.state_color = color_mapping.get(record.state, 'secondary')

    @api.depends('invoice_id', 'invoice_id.state')
    def _compute_invoice_fleet_damage(self):
        for record in self:
            if record.invoice_id and record.invoice_id.state == 'posted':
                record.invoice_fleet_damage = 'invoiced'
            else:
                record.invoice_fleet_damage = ''

    @api.depends('evaluation_report_ids')
    def _compute_evaluation_count(self):
        for record in self:
            record.evaluation_count = len(record.evaluation_report_ids)

    def action_reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_waiting_evaluation(self):
        for rec in self:
            rec.state = 'waiting_evaluation'

    def action_charge(self):
        for rec in self:
            if not rec.evaluation_ids:
                raise ValidationError(_(
                    "Please Add at least one evaluation line to charge invoice !"
                ))
            invoice = self.action_create_invoice()
            if invoice:
                invoice.action_post()
            rec.state = 'charged'

    def action_create_invoice(self):
        account_move_obj = self.env['account.move']
        invoice = False
        for damage in self:
            config = self.env["damage.config.settings"].search(
                [('company_id', '=', self.env.company.id)], order="id desc", limit=1)
            if not damage.invoice_id:
                invoice_line = self.prepare_invoice_line(config)
                invoice_vals = {
                    'move_type': 'out_invoice',
                    'is_damage_invoice': True,
                    'damage_id': damage.id,
                    'partner_id': damage.customer_id.id,
                    'journal_id': config.journal_id.id,
                    'company_id': damage.company_id.id,
                    'invoice_line_ids': invoice_line,
                    'currency_id': damage.company_id.currency_id.id,
                }
                invoice = account_move_obj.sudo().create(invoice_vals)
                if invoice:
                    damage.invoice_id = invoice.id
                    damage.message_post(
                        body=f"Invoice : {invoice.name} created Successfully", subtype_xmlid="mail.mt_comment")
                    invoice = invoice
                else:
                    raise ValidationError(_(
                        " Can't create invoice for this Damage!"
                    ))
            else:
                raise ValidationError(_(
                    f"Damage Already have invoice number{damage.invoice_id.name}!"
                ))
        return invoice

    def prepare_invoice_line(self, config):
        analytic_data = {self.vehicle_id.analytic_account_id.id: 100}
        return [(0, 0, {
            'name': config.description,
            'account_id': config.damage_account_id.id if config else False,
            'quantity': 1,
            'price_unit': eval.amount_without_tax,
            'tax_ids': [(6, 0, eval.tax_ids.ids)],
            'analytic_distribution': analytic_data,
        }) for eval in self.evaluation_ids]

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'

    def action_view_invoices(self):
        for rec in self:
            if rec.invoice_id:
                return {
                    'name': 'Invoice',
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.move',
                    'res_id': rec.invoice_id.id,
                    'view_mode': 'form',
                }
            else:
                raise ValidationError(_("No Invoice Created for this Damage!"))

    @api.depends("evaluation_ids", "evaluation_ids.amount_without_tax", "evaluation_ids.amount_include_tax")
    def _compute_total_amount(self):
        for damage in self:
            damage.total_without_tax = sum(
                damage.evaluation_ids.mapped('amount_without_tax'))
            damage.total_include_tax = sum(
                damage.evaluation_ids.mapped('amount_include_tax'))
            damage.total_tax = damage.total_include_tax - damage.total_without_tax

    @api.model_create_multi
    def create(self, values):
        for vals in values:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'fleet.damage.seq')
        res = super().create(values)
        res.vehicle_id.state_id = self.env.ref(
            'fleet_status.fleet_vehicle_state_damaged').id
        return res

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(
                    "Can't delete Fleet Damage which is not in draft state !")
            elif rec.source == 'rental':
                raise ValidationError(
                    "Can't delete Fleet Damage which is related to rental contract!")
        return super().unlink(),

    def button_add_evaluation(self):
        self.ensure_one()
        view_id = self.env.ref(
            'fleet_damage.add_damage_evaluation_report_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Evaluation'),
            'res_model': 'damage.evaluation.report',
            'target': 'new',
            'view_mode': 'form',
            'context': {'default_damage_id': self.id},
            'views': [[view_id, 'form']]
        }

    def view_related_evaluation(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Evaluations'),
            'res_model': 'damage.evaluation.report',
            'view_mode': 'list,form',
            'domain': [('damage_id', '=', self.id)],
            'context': {'create': 0}
        }


class FleetEvaluation(models.Model):
    _name = 'fleet.evaluation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def default_get(self, fields_list):
        result = super().default_get(fields_list)
        config = self.env["damage.config.settings"].sudo().search(
            [('company_id', '=', self.env.company.id)], order="id desc", limit=1)
        if config:
            result['tax_ids'] = [(6, 0, config.tax_ids.ids)]
        return result

    fleet_damage_id = fields.Many2one(
        comodel_name='fleet.damage', string='Fleet_damage_id', required=False)
    evaluation_item_id = fields.Many2one(
        comodel_name='fleet.accident.evaluation.item', string='Evaluation Items', required=True)  # related with model sabry
    amount_without_tax = fields.Float(
        string='Amount Without Tax', compute="_compute_amount_without_tax", store=True)
    amount_include_tax = fields.Float(
        string='Amount Include Tax', required=True)
    tax_ids = fields.Many2many('account.tax', string="Taxes", domain=[
                               ("type_tax_use", "=", "sale")])
    evaluation_report_id = fields.Many2one(
        'damage.evaluation.report', string='Damage Evaluation Report')

    @api.depends("amount_include_tax", "tax_ids")
    def _compute_amount_without_tax(self):
        for rec in self:
            if rec.tax_ids:
                total_tax_ratio = sum(rec.tax_ids.mapped('amount'))
                rec.amount_without_tax = rec.amount_include_tax / \
                    (1+total_tax_ratio/100)
            else:
                rec.amount_without_tax = rec.amount_include_tax
