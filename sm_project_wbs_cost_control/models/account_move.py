# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    sm_wbs_id = fields.Many2one('sm.project.wbs', string='WBS Item')

    def _sm_wbs_analytic_distribution(self, wbs):
        account = wbs.project_id.account_id
        return {str(account.id): 100.0} if account else False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('sm_wbs_id') and not vals.get('analytic_distribution') and not vals.get('display_type'):
                distribution = self._sm_wbs_analytic_distribution(self.env['sm.project.wbs'].browse(vals['sm_wbs_id']))
                if distribution:
                    vals['analytic_distribution'] = distribution
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('sm_wbs_id') and not vals.get('analytic_distribution'):
            distribution = self._sm_wbs_analytic_distribution(self.env['sm.project.wbs'].browse(vals['sm_wbs_id']))
            if distribution:
                vals = dict(vals, analytic_distribution=distribution)
        return super().write(vals)

    @api.onchange('sm_wbs_id')
    def _onchange_sm_wbs_id(self):
        for line in self:
            if line.sm_wbs_id and not line.display_type:
                line.analytic_distribution = line._sm_wbs_analytic_distribution(line.sm_wbs_id)

    def _prepare_analytic_distribution_line(self, distribution, account_ids, distribution_on_each_plan):
        vals = super()._prepare_analytic_distribution_line(distribution, account_ids, distribution_on_each_plan)
        if self.sm_wbs_id:
            vals['sm_wbs_id'] = self.sm_wbs_id.id
        return vals
