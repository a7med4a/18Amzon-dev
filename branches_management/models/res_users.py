# -*- coding: utf-8 -*-
##########################################################################


from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
import logging
_logger = logging.getLogger(__name__)


class Users(models.Model):
    _inherit = "res.users"

    def _branches_count(self):
        return self.env['res.branch'].sudo().search_count([])

    def _compute_branches_count(self):
        branches_count = self._branches_count()
        for user in self:
            user.branches_count = branches_count

    branch_id = fields.Many2one('res.branch', string='Branch', required=True, ondelete='restrict', default=lambda self: self.env.branch.id, help='The default branch for this user.', domain="[('company_id','in',company_ids)]")
    branch_ids = fields.Many2many('res.branch', 'res_branches_users_rel', 'user_b_id', 'ubid', string='Branches', ondelete='restrict', default=lambda self: self.env.branches.ids, domain="[('company_id','in',company_ids)]")
    branches_count = fields.Integer(compute='_compute_branches_count', string="Number of Branches", default=_branches_count)

    @api.constrains('branch_id', 'branch_ids')
    def _check_branch(self):
        if any(user.branch_id and user.branch_id not in user.branch_ids for user in self):
            raise ValidationError(_('The chosen branch is not in the allowed branches for this user'))

    @api.constrains('company_ids', 'branch_ids')
    def _check_branch_cmp(self):
        for user in self:
            brch_cmp = [obj.company_id.id for obj in user.branch_ids] if user.branch_ids else []
            if any(user.company_ids and obj not in user.company_ids.ids for obj in brch_cmp):
                raise ValidationError(_('The branches are not in the allowed companies for this user'))

    @api.model_create_multi
    def create(self, values):
        user = super(Users, self).create(values)
        group_multi_branch = self.env.ref('branches_management.group_multi_branch', False)
        for value in values:
            if group_multi_branch and 'branch_ids' in value:
                if len(user.branch_ids) <= 1 and user.id in group_multi_branch.users.ids:
                    user.write({'groups_id': [(3, group_multi_branch.id)]})
                elif len(user.branch_ids) > 1 and user.id not in group_multi_branch.users.ids:
                    user.write({'groups_id': [(4, group_multi_branch.id)]})
        if user.partner_id.branch_id:
            user.partner_id.branch_id = user.branch_id
        return user

    def write(self, values):
        res = super(Users, self).write(values)
        group_multi_branch = self.env.ref('branches_management.group_multi_branch', False)
        if group_multi_branch and 'branch_ids' in values:
            for user in self:
                if len(user.branch_ids) <= 1 and user.id in group_multi_branch.users.ids:
                    user.write({'groups_id': [(3, group_multi_branch.id)]})
                elif len(user.branch_ids) > 1 and user.id not in group_multi_branch.users.ids:
                    user.write({'groups_id': [(4, group_multi_branch.id)]})
        for user in self:
            if user.partner_id.branch_id and user.partner_id.branch_id.id != values.get('branch_id'):
                user.partner_id.write({'branch_id': user.branch_id.id})
        return res

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + ['branch_id']

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + ['branch_id']

class Partner(models.Model):
    _inherit = "res.partner"

    branch_id = fields.Many2one('res.branch', 'Branch')
    @api.constrains('branch_id', 'company_id')
    def _check_branch_id(self):
        for obj in self:
            if obj.branch_id and not obj.company_id:
                raise ValidationError(_('Company is required with Branch.'))
            if obj.branch_id and obj.branch_id not in obj.company_id.branch_ids:
                raise ValidationError(_('Branch should belongs to the selected Company.'))

class ResCompany(models.Model):
    _inherit = "res.company"

    branch_ids = fields.One2many("res.branch", "company_id", string="Company Branches", readonly=True)
    default_branch_id = fields.Many2one("res.branch", string="Default Branch", domain="[('id','in',branch_ids)]")

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    branch_id = fields.Many2one('res.branch', 'Branch', default=lambda self: self.env.branch, ondelete='restrict', domain="[('company_id','in',company_ids)]")
