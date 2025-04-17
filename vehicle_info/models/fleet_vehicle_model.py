from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FleetVehicleModelInherit(models.Model):
    _inherit = 'fleet.vehicle.model'

    name = fields.Char('Model name', required=True, tracking=True)
    category_id = fields.Many2one('fleet.vehicle.model.category', 'Category', tracking=True,required=True)
    model_year = fields.Integer(tracking=True)


    @api.constrains('model_year')
    def _check_model_year(self):
        for rec in self:
            if rec.model_year <= 0 :
                raise ValidationError(_("Model year must be have a value of any year,please Add model year"))

    def write(self, values):
        for rec in self :
            if 'name' in values and 'model_year' in values :
                values['name'] = f"{values['name']}/{str(values['model_year'])}"
            elif 'name' in values:
                name = values['name'].rsplit('/', 1)[0]
                if not name :
                    name = values['name']
                values['name'] = f"{name}/{str(rec.model_year)}"
            elif 'model_year' in values :
                name= rec.name.rsplit('/', 1)[0]
                if not name :
                    name = values['name']
                values['name'] = f"{name}/{str(values['model_year'])}"
        return super().write(values)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' in vals and 'model_year' in vals:
                vals['name'] = f"{vals['name']}/{str(vals['model_year'])}"
        return super().create(vals_list)