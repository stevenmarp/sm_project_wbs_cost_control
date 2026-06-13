# -*- coding: utf-8 -*-
from odoo import fields, models, _


class ProjectProject(models.Model):
    _inherit = 'project.project'

    sm_wbs_ids = fields.One2many('sm.project.wbs', 'project_id', string='WBS Items')
    sm_wbs_count = fields.Integer(compute='_compute_sm_wbs_amounts')
    sm_wbs_planned_cost = fields.Monetary(compute='_compute_sm_wbs_amounts', currency_field='currency_id')
    sm_wbs_committed_cost = fields.Monetary(compute='_compute_sm_wbs_amounts', currency_field='currency_id')
    sm_wbs_actual_cost = fields.Monetary(compute='_compute_sm_wbs_amounts', currency_field='currency_id')
    sm_wbs_variance_cost = fields.Monetary(compute='_compute_sm_wbs_amounts', currency_field='currency_id')

    def _compute_sm_wbs_amounts(self):
        for project in self:
            wbs_items = project.sm_wbs_ids
            project.sm_wbs_count = len(wbs_items)
            project.sm_wbs_planned_cost = sum(wbs_items.filtered(lambda w: not w.parent_id).mapped('planned_cost'))
            project.sm_wbs_committed_cost = sum(wbs_items.filtered(lambda w: not w.parent_id).mapped('committed_cost'))
            project.sm_wbs_actual_cost = sum(wbs_items.filtered(lambda w: not w.parent_id).mapped('actual_cost'))
            project.sm_wbs_variance_cost = project.sm_wbs_planned_cost - project.sm_wbs_actual_cost

    def action_open_sm_wbs(self):
        self.ensure_one()
        return {
            'name': _('WBS Cost Control'),
            'type': 'ir.actions.act_window',
            'res_model': 'sm.project.wbs',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id, 'search_default_project_id': self.id},
        }
