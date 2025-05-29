from odoo.exceptions import ValidationError
from markupsafe import Markup
from datetime import date
from odoo import api, fields, models


class VehicleModelDetail(models.Model):
    _name = 'fleet.vehicle.model.detail'
    _description = 'Vehicle Model Detail'
    _inherit = ['mail.thread', 'mail.activity.mixin',]

    name = fields.Char(tracking=True)
    vehicle_model_brand_id = fields.Many2one(
        comodel_name='fleet.vehicle.model.brand',
        string='Vehicle Model Brand',
        required=True)
    fleet_vehicle_model_id = fields.Many2one(
        comodel_name='fleet.vehicle.model',
        string='Vehicle Model',
        required=True)
    model_ids = fields.One2many(
        comodel_name='fleet.vehicle.model',
        related='vehicle_model_brand_id.model_ids',
        string='Models',
        required=False)
    free_kilometers = fields.Float(
        string='Free Kilometers',
        required=True, tracking=True)
    extra_kilometers_cost = fields.Float(
        string='Extra kilometers cost',
        required=True)
    number_delay_hours_allowed = fields.Float(required=True)
    min_normal_day_price = fields.Float(required=True)
    min_weekly_day_price = fields.Float(required=True)
    min_monthly_day_price = fields.Float(required=True)
    max_normal_day_price = fields.Float(required=True)
    max_weekly_day_price = fields.Float(required=True)
    max_monthly_day_price = fields.Float(required=True)
    min_customer_age = fields.Float('Min Customer Age', required=True)
    max_customer_age = fields.Float('Max Customer Age', required=True)
    full_tank_cost = fields.Float(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date()
    # branch = fields.Char(tracking=True)
    branch_ids = fields.Many2many(
        comodel_name='res.branch',
        relation='fleet_vehicle_model_detail_res_branch_rel',
        column1='model_detail_id',
        column2='branch_id',
        string='Branch', tracking=True
    )
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'), ('running', 'Running'),
                   ('expired', 'Expired')],
        default='draft', readonly=True)

    def action_confirm(self):
        for rec in self:
            if rec.state != 'running':
                self.message_post_body("Running")
                rec.state = 'running'

    def action_expire(self):
        for rec in self:
            if rec.state != 'expired':
                self.message_post_body("Expired")
                rec.state = 'expired'

    def action_set_draft(self):
        for rec in self:
            if rec.state != 'draft':
                self.message_post_body("Draft")
                rec.state = 'draft'

    def _update_expired_state(self):
        today = date.today()
        expired_records = self.search(
            [('end_date', '<', today), ('state', '!=', 'expired'), ('state', '!=', 'running')])
        expired_records.write({'state': 'expired'})

    def message_post_body(self, new_state):
        self.vehicle_model_brand_id.message_post(
            body=Markup(
                f"<b>Vehicle Details Updated</b>:<br/> State changed changed from {self.state} to <i>{new_state}<i>"),
            subtype_xmlid="mail.mt_comment")

    def _check_duplicate_and_overlap(self):
        """ تحقق من عدم وجود تداخل زمني مع نفس الموديل والفرع """

        print("**** _check_duplicate_and_overlap")
        for rec in self:
            for branch_id in rec.branch_ids:
                domain = [
                    ('fleet_vehicle_model_id', '=', rec.fleet_vehicle_model_id.id),
                    ('branch_ids', 'in', [branch_id.id]),
                    ('state', 'in', ('draft', 'running')),  # فقط السجلات النشطة
                    ('id', '!=', rec.id),  # استثناء السجل الحالي عند التعديل
                ]

                overlapping_ids = self.search(domain)
                print("**** overlapping_ids ==>", overlapping_ids)
                overlapping = False
                print("**** rec.start_date ==>", rec.start_date)
                print("**** rec.end_date ==>", rec.end_date)
                for line in overlapping_ids:
                    if not line.end_date and not rec.end_date:
                        overlapping = True
                        break
                    if rec.end_date and rec.end_date >= line.start_date and not line.end_date:
                        overlapping = True
                        break
                    elif line.end_date and not rec.end_date and rec.start_date <= line.end_date:
                        overlapping = True
                        break
                    elif line.end_date and rec.end_date:
                        if (line.start_date <= rec.start_date <= line.end_date) or (line.start_date <= rec.end_date <= line.end_date):
                            overlapping = True
                            break
                        elif (line.start_date > rec.start_date <= line.end_date) or (line.start_date <= rec.end_date <= line.end_date):
                            overlapping = True
                            break

                if overlapping:
                    raise ValidationError(
                        f"There is a time overlap for the same model '{rec.fleet_vehicle_model_id.name}' and branch '{branch_id.name}'.")

    @api.model_create_multi
    def create(self, vals):
        record = super(VehicleModelDetail, self).create(vals)
        record._check_duplicate_and_overlap()
        return record

    def write(self, vals):
        result = super(VehicleModelDetail, self).write(vals)
        self._check_duplicate_and_overlap()
        return result

    @api.model
    def schedular_update_state(self):
        today_date = fields.Date.today()
        draft_pricing_ids = self.search(
            [('state', '=', 'draft'), ('start_date', '<=', today_date)])
        running_pricing_ids = self.search(
            [('state', '=', 'running'), ('start_date', '<=', today_date)])
        draft_pricing_ids.write({'state': 'running'})
        running_pricing_ids.filtered(
            lambda p: p.end_date and p.end_date < today_date).write({'state': 'expired'})
