# -*- coding: utf-8 -*-
import json
from datetime import datetime, time, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SmProjectWbs(models.Model):
    _name = 'sm.project.wbs'
    _description = 'Project Work Breakdown Structure'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _parent_name = 'parent_id'
    _parent_store = True
    _order = 'project_id, parent_path, sequence, id'
    _rec_name = 'display_name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(copy=False, tracking=True, default=lambda self: _('New'))
    display_name = fields.Char(compute='_compute_display_name', store=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    project_id = fields.Many2one('project.project', required=True, ondelete='cascade', index=True, tracking=True)
    company_id = fields.Many2one(related='project_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='project_id.currency_id', readonly=True)
    parent_id = fields.Many2one('sm.project.wbs', string='Parent WBS', index=True, ondelete='cascade', domain="[('project_id', '=', project_id)]")
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many('sm.project.wbs', 'parent_id', string='Child WBS')
    task_id = fields.Many2one('project.task', string='Linked Task', domain="[('project_id', '=', project_id)]", tracking=True)
    manager_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True, required=True)
    progress = fields.Float(string='Progress (%)', default=0.0, tracking=True)
    planned_revenue = fields.Monetary(currency_field='currency_id', tracking=True)
    cost_line_ids = fields.One2many('sm.project.wbs.cost.line', 'wbs_id', string='Budget Lines')
    purchase_line_ids = fields.One2many('purchase.order.line', 'sm_wbs_id', string='Purchase Lines')
    analytic_line_ids = fields.One2many('account.analytic.line', 'sm_wbs_id', string='Analytic Lines')
    planned_cost = fields.Monetary(compute='_compute_planned_cost', store=True, recursive=True, currency_field='currency_id')
    direct_planned_cost = fields.Monetary(string='Manual Planned Cost', currency_field='currency_id', tracking=True)
    committed_cost = fields.Monetary(compute='_compute_committed_cost', store=True, recursive=True, currency_field='currency_id')
    actual_cost = fields.Monetary(compute='_compute_actual_cost', store=True, recursive=True, currency_field='currency_id')
    forecast_cost = fields.Monetary(compute='_compute_control_amounts', store=True, currency_field='currency_id')
    remaining_cost = fields.Monetary(compute='_compute_control_amounts', store=True, currency_field='currency_id')
    variance_cost = fields.Monetary(compute='_compute_control_amounts', store=True, currency_field='currency_id')
    margin_amount = fields.Monetary(compute='_compute_control_amounts', store=True, currency_field='currency_id')
    planned_margin = fields.Monetary(compute='_compute_control_amounts', store=True, currency_field='currency_id')
    cost_performance = fields.Float(compute='_compute_control_amounts', store=True, string='Cost Performance (%)')
    analytic_line_count = fields.Integer(compute='_compute_counts')
    purchase_line_count = fields.Integer(compute='_compute_counts')
    sm_gantt_start = fields.Datetime(compute='_compute_sm_gantt_schedule', inverse='_inverse_sm_gantt_start', store=True)
    sm_gantt_duration = fields.Integer(compute='_compute_sm_gantt_schedule', inverse='_inverse_sm_gantt_duration', store=True, default=1)
    sm_gantt_open = fields.Boolean(string='Open in Gantt', default=True)
    depending_wbs_ids = fields.One2many('sm.project.wbs.dependency', 'wbs_id', string='Successors')
    dependency_wbs_ids = fields.One2many('sm.project.wbs.dependency', 'depending_wbs_id', string='Predecessors')
    sm_gantt_links_serialized_json = fields.Text(compute='_compute_sm_gantt_links_json')
    note = fields.Html()

    _project_code_unique = models.Constraint(
        'unique(project_id, code)',
        'WBS code must be unique per project.',
    )
    _progress_range = models.Constraint(
        'check(progress >= 0 and progress <= 100)',
        'Progress must be between 0 and 100.',
    )

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = '[%s] %s' % (rec.code, rec.name) if rec.code and rec.code != _('New') else rec.name

    @api.depends('cost_line_ids.subtotal', 'direct_planned_cost', 'child_ids.planned_cost')
    def _compute_planned_cost(self):
        for rec in self:
            line_total = sum(rec.cost_line_ids.mapped('subtotal'))
            child_total = sum(rec.child_ids.mapped('planned_cost'))
            rec.planned_cost = (line_total or rec.direct_planned_cost) + child_total

    @api.depends('purchase_line_ids.price_subtotal', 'purchase_line_ids.order_id.state', 'child_ids.committed_cost')
    def _compute_committed_cost(self):
        for rec in self:
            lines = rec.purchase_line_ids.filtered(lambda line: not line.display_type and line.order_id.state != 'cancel')
            rec.committed_cost = sum(lines.mapped('price_subtotal')) + sum(rec.child_ids.mapped('committed_cost'))

    @api.depends('analytic_line_ids.amount', 'child_ids.actual_cost')
    def _compute_actual_cost(self):
        for rec in self:
            rec.actual_cost = sum(-line.amount for line in rec.analytic_line_ids if line.amount < 0) + sum(rec.child_ids.mapped('actual_cost'))

    @api.depends('planned_cost', 'planned_revenue', 'progress', 'actual_cost', 'committed_cost')
    def _compute_control_amounts(self):
        for rec in self:
            forecast = max(rec.actual_cost, rec.committed_cost, rec.planned_cost)
            rec.forecast_cost = forecast
            rec.remaining_cost = max(rec.planned_cost - rec.actual_cost, 0.0)
            rec.variance_cost = rec.planned_cost - rec.actual_cost
            rec.margin_amount = rec.planned_revenue - rec.actual_cost
            rec.planned_margin = rec.planned_revenue - rec.planned_cost
            rec.cost_performance = rec.planned_cost and (rec.actual_cost / rec.planned_cost) * 100.0 or 0.0

    def _compute_counts(self):
        for rec in self:
            rec.analytic_line_count = self.env['account.analytic.line'].search_count([('sm_wbs_id', 'child_of', rec.id)])
            rec.purchase_line_count = self.env['purchase.order.line'].search_count([('sm_wbs_id', 'child_of', rec.id), ('display_type', '=', False)])

    @api.depends('date_start', 'date_end')
    def _compute_sm_gantt_schedule(self):
        today = fields.Date.today()
        for rec in self:
            start_date = rec.date_start or today
            end_date = rec.date_end or start_date
            rec.sm_gantt_start = datetime.combine(start_date, time.min)
            rec.sm_gantt_duration = max((end_date - start_date).days + 1, 1)

    def _inverse_sm_gantt_start(self):
        for rec in self:
            if rec.sm_gantt_start:
                start_date = fields.Date.to_date(rec.sm_gantt_start)
                rec.date_start = start_date
                rec.date_end = start_date + timedelta(days=max(rec.sm_gantt_duration or 1, 1) - 1)

    def _inverse_sm_gantt_duration(self):
        for rec in self:
            start_date = fields.Date.to_date(rec.date_start) or fields.Date.to_date(rec.sm_gantt_start)
            if start_date:
                rec.date_end = start_date + timedelta(days=max(rec.sm_gantt_duration or 1, 1) - 1)

    @api.depends('dependency_wbs_ids', 'dependency_wbs_ids.wbs_id', 'dependency_wbs_ids.relation_type')
    def _compute_sm_gantt_links_json(self):
        for rec in self:
            links = []
            for link in rec.dependency_wbs_ids:
                links.append({
                    'id': link.id,
                    'source': link.wbs_id.id,
                    'target': link.depending_wbs_id.id,
                    'type': link.relation_type,
                })
            rec.sm_gantt_links_serialized_json = json.dumps(links)

    @api.constrains('parent_id', 'project_id')
    def _check_parent_project(self):
        for rec in self:
            if rec.parent_id and rec.parent_id.project_id != rec.project_id:
                raise ValidationError(_('Parent WBS must belong to the same project.'))

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_start > rec.date_end:
                raise ValidationError(_('Start date must be before end date.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('sm.project.wbs') or _('New')
        return super().create(vals_list)

    def action_approve(self):
        self.write({'state': 'approved'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_done(self):
        self.write({'state': 'done', 'progress': 100.0})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})

    def action_open_analytic_lines(self):
        self.ensure_one()
        return {
            'name': _('Actual Cost Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_mode': 'list,form,pivot,graph',
            'domain': [('sm_wbs_id', 'child_of', self.id)],
            'context': {'default_sm_wbs_id': self.id, 'default_project_id': self.project_id.id},
        }

    def action_open_purchase_lines(self):
        self.ensure_one()
        return {
            'name': _('Committed Purchase Lines'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.line',
            'view_mode': 'list,form',
            'domain': [('sm_wbs_id', 'child_of', self.id), ('display_type', '=', False)],
            'context': {'default_sm_wbs_id': self.id},
        }


class SmProjectWbsCostLine(models.Model):
    _name = 'sm.project.wbs.cost.line'
    _description = 'WBS Budget Cost Line'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    wbs_id = fields.Many2one('sm.project.wbs', required=True, ondelete='cascade', index=True)
    project_id = fields.Many2one(related='wbs_id.project_id', store=True, readonly=True)
    company_id = fields.Many2one(related='wbs_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='wbs_id.currency_id', readonly=True)
    cost_type = fields.Selection([
        ('labor', 'Labor'),
        ('material', 'Material'),
        ('equipment', 'Equipment'),
        ('subcontract', 'Subcontract'),
        ('overhead', 'Overhead'),
        ('other', 'Other'),
    ], default='material', required=True)
    product_id = fields.Many2one('product.product')
    name = fields.Char(required=True)
    quantity = fields.Float(default=1.0)
    uom_id = fields.Many2one('uom.uom')
    unit_cost = fields.Monetary(currency_field='currency_id')
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True, currency_field='currency_id')

    @api.depends('quantity', 'unit_cost')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_cost

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.name = line.name or line.product_id.display_name
                line.uom_id = line.uom_id or line.product_id.uom_id
                line.unit_cost = line.unit_cost or line.product_id.standard_price


class SmProjectWbsDependency(models.Model):
    _name = 'sm.project.wbs.dependency'
    _description = 'WBS Dependency'

    wbs_id = fields.Many2one('sm.project.wbs', string='WBS Item', required=True, ondelete='cascade')
    depending_wbs_id = fields.Many2one('sm.project.wbs', string='Depending WBS', required=True, ondelete='cascade')
    relation_type = fields.Selection([
        ('0', 'Finish to Start'),
        ('1', 'Start to Start'),
        ('2', 'Finish to Finish'),
        ('3', 'Start to Finish'),
    ], default='0', required=True, string='Type')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('done', 'Done'),
    ], default='draft', string='State')

    _wbs_dependency_unique = models.Constraint(
        'unique(wbs_id, depending_wbs_id)',
        'Two WBS items can only have one dependency relation.',
    )
    _wbs_dependency_not_self = models.Constraint(
        'check(wbs_id != depending_wbs_id)',
        'WBS item cannot depend on itself.',
    )

    @api.constrains('wbs_id', 'depending_wbs_id')
    def _check_same_project(self):
        for rec in self:
            if rec.wbs_id.project_id != rec.depending_wbs_id.project_id:
                raise ValidationError(_('WBS dependencies must belong to the same project.'))
