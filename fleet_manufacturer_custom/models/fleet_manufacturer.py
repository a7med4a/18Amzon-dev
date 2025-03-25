
from odoo import api, fields, models
from markupsafe import Markup
from odoo.exceptions import ValidationError
from datetime import datetime


class ManufacturerInherit(models.Model):
    _name='fleet.vehicle.model.brand'
    _inherit = ['fleet.vehicle.model.brand','mail.thread','mail.activity.mixin']

    vehicle_detail_ids = fields.One2many(
        comodel_name='fleet.vehicle.model.detail',
        inverse_name='vehicle_model_brand_id',
        string='Vehicle Details')


    last_update = fields.Datetime(string="Last Update", tracking=True, compute="_compute_last_update", store=True)
    last_changes = fields.Text(string="Last Changes", tracking=True)

    @api.depends('vehicle_detail_ids')
    def _compute_last_update(self):
        for record in self:
            record.last_update = fields.Datetime.now()

    def update_header(self, changes):
        changes_text = "\n".join(changes) if changes else "No changes recorded."
        self.write({
            'last_update': fields.Datetime.now(),
            'last_changes': changes_text
        })

    # def create(self, vals):
    #     if vals.get('vehicle_detail_ids'):
    #         details = []
    #         print('Creating details',vals['vehicle_detail_ids'])
    #         for detail in vals['vehicle_detail_ids']:
    #             branch = detail[2].get('branch')
    #             vehicle_model = detail[2].get('vehicle_model_id')
    #             state=detail[2].get('vehicle_model_id')
    #             start_date = detail[2].get('start_date')
    #             end_date = detail[2].get('end_date')
    #
    #             for existing_detail in details:
    #                 if (existing_detail['branch'] == branch
    #                     and existing_detail['vehicle_model'] == vehicle_model
    #                     and state != 'expire'):
    #                     if (not existing_detail['end_date']
    #                         and start_date >= existing_detail['start_date']):
    #                         raise ValidationError(f"The start date falls after start  date of existing branch")
    #                     elif (start_date >= existing_detail['start_date']
    #                           and start_date <= existing_detail['end_date']):
    #                         raise ValidationError(f"The start date  falls between the start and end date of branch of existing branch")
    #
    #             details.append({
    #                 'branch': branch,
    #                 'vehicle_model': vehicle_model,
    #                 'start_date': start_date,
    #                 'end_date': end_date
    #             })
    #     return super().create(vals)
    #
    # def write(self, vals):
    #     for record in self:
    #         existing_details = record.vehicle_detail_ids
    #         print('Creating details', vals['vehicle_detail_ids'])
    #         for detail in vals.get('vehicle_detail_ids', []):
    #             if detail[0]==0:
    #                 branch = detail[2].get('branch')
    #                 vehicle_model = detail[2].get('fleet_vehicle_model_id')
    #                 start_date = detail[2].get('start_date')
    #                 if not branch or not vehicle_model or not start_date:
    #                     continue
    #                 for existing_detail in existing_details:
    #                     if (existing_detail.branch == branch
    #                         and existing_detail.fleet_vehicle_model_id.id == vehicle_model
    #                         and existing_detail.state != 'expire'):
    #                         start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    #                         if (not existing_detail.end_date
    #                             and start_date >= existing_detail.start_date):
    #                             raise ValidationError(f"The start date of '{branch}' falls after the start date of branch {existing_detail.branch}.")
    #                         elif (start_date >= existing_detail.start_date and start_date <= existing_detail.end_date):
    #                             raise ValidationError(f"The start date of '{branch}' falls between the start and end date of branch {existing_detail.branch}.")
    #     old_details = {}
    #     for record in self:
    #         old_details = {d.id: d.read()[0] for d in record.vehicle_detail_ids}
    #     result = super().write(vals)
    #     for record in self:
    #         new_details = {}
    #         for counter, d in enumerate(record.vehicle_detail_ids):
    #             new_details[d.id] = {"line": counter + 1,**d.read()[0]}
    #         changes = []
    #         for detail_id, old_vals in old_details.items():
    #             new_vals = new_details.get(detail_id)
    #             if new_vals:
    #                 for field in old_vals.keys():
    #                     if old_vals[field] != new_vals[field] and field != "write_date":
    #                         line = new_details[detail_id]["line"]
    #                         changes.append(Markup(f"Field <i>{field}</i> in line {line} changed from {old_vals[field]} to {new_vals[field]}"))
    #         if changes:
    #             body = Markup("<b>Vehicle Details Updated</b>:<br/>")
    #             body += Markup("<br/>".join(changes))
    #             record.message_post(body=body, subtype_xmlid="mail.mt_comment")
    #     return result


