# -*- coding: utf-8 -*-
##########################################################################


from odoo import api, fields, models, tools, _
from odoo.http import request
from odoo.exceptions import AccessError
from odoo.tools import lazy_property
from odoo.api import Environment
import logging
_logger = logging.getLogger(__name__)
from odoo import SUPERUSER_ID
class IrRule(models.Model):
    _inherit = 'ir.rule'

    @api.model
    def _eval_context(self):
        res = super(IrRule, self)._eval_context()
        res['branch_ids'] = self.env.branches.ids
        res['branch_id'] = self.env.branch.id
        return res

    def _compute_domain_keys(self):
        """ Return the list of context keys to use for caching ``_compute_domain``. """
        return super(IrRule, self)._compute_domain_keys() + ['allowed_branch_ids']

class BranchEnvironment(Environment):

    @lazy_property
    def branch(self):
        branch_ids = self.context.get('allowed_branch_ids', [])
        if branch_ids:
            if self.user.id != SUPERUSER_ID:
            # if not self.su:
                user_branch_ids = self.user.branch_ids.ids
                if any(bid not in user_branch_ids for bid in branch_ids):
                    raise AccessError(_("Access to unauthorized or invalid branches."))
            return self['res.branch'].browse(branch_ids[0])
        return self.user.branch_id.with_env(self)

    @lazy_property
    def branches(self):
        branch_ids = self.context.get('allowed_branch_ids', [])
        if branch_ids:
            if self.user.id != SUPERUSER_ID:
            # if not self.su:
                user_branch_ids = self.user.branch_ids.ids
                if any(bid not in user_branch_ids for bid in branch_ids):
                    raise AccessError(_("Access to unauthorized or invalid branches."))
            return self['res.branch'].browse(branch_ids)
        return self.user.branch_ids.with_env(self)

    Environment.branch = branch
    Environment.branches = branches

class BranchHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super(BranchHttp, self).session_info()
        user = request.env.user
        if self.env.user.has_group('base.group_user'):
            result.update({
                # current_company should be default_company
                "user_branches": {
                    'current_branch': user.branch_id.id,  #(user.branch_id.id, user.branch_id.name, user.branch_id.company_id.id, user.branch_id.company_id.name), #user.branch_id.id,
                    'allowed_branches': {
                        brh.id: {
                            'id': brh.id,
                            'name': brh.name,
                            'company': brh.company_id.id,
                            'company_name': brh.company_id.name,
                        } for brh in user.branch_ids
                    },
                },
                "show_effect": True,
                "display_switch_branch_menu": user.has_group('branches_management.group_multi_branch') and len(user.branch_ids) > 1,
            })
        return result

