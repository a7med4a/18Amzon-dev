
from odoo import models, fields, api
from lxml import etree

class InheritResPartner(models.Model):
    _inherit = 'res.partner'

    is_insurance_company=fields.Boolean('Is Insurance Company ?')

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        config = self.env["insurance.config.settings"].search([], order="id desc", limit=1)
        if config:
            # Only apply these defaults if the context matches your action
            if self.env.context.get('default_is_insurance_company'):
                defaults.update({
                    'company_type': 'company',
                    'property_account_payable_id': config.account_pay_id.id if config.account_pay_id else False,
                    'category_id': [(6, 0, config.category_id.ids)] if config.category_id else [(6, 0, [])],
                    'is_insurance_company': True,
                })
        return defaults

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id, view_type, **options)
        config = self.env["insurance.config.settings"].search([], order="id desc", limit=1)
        if config:
            partner_action_form = self.env.ref('fleet_insurance.action_contacts_data')
            context = {
                'default_company_type': 'company',
                'default_property_account_payable_id': config.account_pay_id.id if config.account_pay_id else False,
                'default_category_id': [(6, 0, config.category_id.ids)] if config.category_id else [(6, 0, [])],
                'default_is_insurance_company': True,
            }
            domain=[('company_type','=','company'),('is_insurance_company','=',True)]
            partner_action_form.write({"context": context, "domain": domain})
        if view_type == 'form' and options.get('action_id') == partner_action_form.id:
            doc = etree.XML(res['arch'])
            company_type_fields = doc.xpath("//div/field[@name='company_type']")
            if company_type_fields:
                company_type_fields[0].set("invisible", "1")
            vat_fields = doc.xpath("//field[@name='vat']")
            if vat_fields:
                new_field = etree.Element("field", name="is_insurance_company", string="Is Insurance Company?", readonly="1")
                vat_fields[0].addnext(new_field)
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

