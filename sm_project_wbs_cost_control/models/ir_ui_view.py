# -*- coding: utf-8 -*-
from lxml import etree

from odoo import _, fields, models


SM_GANTT_VALID_ATTRIBUTES = {
    '__validate__',
    'class',
    'create',
    'date_start',
    'delete',
    'duration',
    'edit',
    'groups',
    'id_field',
    'js_class',
    'link_model',
    'link_source_field',
    'link_target_field',
    'link_type_field',
    'links_serialized_json',
    'open',
    'progress',
    'string',
    'text',
}


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(
        selection_add=[('sm_gantt', 'SM Gantt')],
        ondelete={'sm_gantt': 'cascade'},
    )

    def _get_view_info(self):
        info = super()._get_view_info()
        info['sm_gantt'] = {'icon': 'fa fa-tasks', 'multi_record': True}
        return info

    def _is_qweb_based_view(self, view_type):
        return view_type == 'sm_gantt' or super()._is_qweb_based_view(view_type)

    def _get_view_fields(self, view_type, models):
        if view_type == 'sm_gantt':
            models[self._name] = list(self._fields.keys())
            return models
        return super()._get_view_fields(view_type, models)

    def _validate_tag_sm_gantt(self, node, name_manager, node_info):
        if not node_info['validate']:
            return
        for child in node.iterchildren(tag=etree.Element):
            if child.tag != 'field':
                self._raise_view_error(_('SM Gantt child can only be field, got %s', child.tag), child)
        remaining = set(node.attrib) - SM_GANTT_VALID_ATTRIBUTES
        if remaining:
            self._raise_view_error(
                _(
                    'Invalid attributes (%(invalid_attributes)s) in sm_gantt view. Attributes must be in (%(valid_attributes)s)',
                    invalid_attributes=remaining,
                    valid_attributes=SM_GANTT_VALID_ATTRIBUTES,
                ),
                node,
            )
