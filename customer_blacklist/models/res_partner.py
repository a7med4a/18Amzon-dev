from odoo import fields, models, api
from lxml import etree

class ResPartner(models.Model):
    _inherit = 'res.partner'

    blacklist_status = fields.Selection(string="Blacklist Status", selection=[
        ("running", "Running"),
        ("warning", "Warning"),
        ("blocked", "Blocked")], required=False, default="running", readonly=True,store=True)
    blacklist_reason = fields.Text(string='Blacklist Reason', readonly=True)
    blacklist_history_ids = fields.One2many('res.partner.blacklist.history', 'partner_id', string='Blacklist History')

    @api.model
    def get_view(self, view_id=None, view_type='form', **options):
        res = super().get_view(view_id, view_type, **options)
        if (view_type == 'form' or view_type == 'list') and options.get('action_id') == self.env.ref('customer_blacklist.rental_individual_customers_action_blocked').id:
            doc = etree.XML(res['arch'])
            list_view = doc.xpath("//list")
            form_view = doc.xpath("//form")
            if list_view:
                list_view[0].set("create", "0")
            if form_view:
                form_view[0].set("create", "0")
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res