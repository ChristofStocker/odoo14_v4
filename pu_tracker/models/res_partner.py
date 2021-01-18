import logging
import threading
from datetime import datetime
from email.utils import parseaddr

# changed by Christof Stocker
import html2text
import pytz
from odoo import models, fields, api, _, tools, SUPERUSER_ID, registry
from odoo.exceptions import AccessError


class Partner(models.Model):
    _inherit = "res.partner"

    tracker_user_count = fields.Integer(string="GPS-Tracker", compute='_tracker_user_count')
    tracker_buyer_count = fields.Integer(string="GPS-Tracker", compute='_tracker_buyer_count')

    # @api.depends('pu.tracker')
    def _tracker_user_count(self):
        for rec in self:
            if rec.id:
                rec.tracker_user_count = self.env['pu.tracker'].search_count([('user_partner_id', 'child_of', rec.id)])
            else:
                rec.tracker_user_count = 0

    def _tracker_buyer_count(self):
        for rec in self:
            if rec.id:
                rec.tracker_buyer_count = self.env['pu.tracker'].search_count([('customer_id', 'child_of', rec.id)])
            else:
                rec.tracker_buyer_count = 0

    # -- Open related
    def partner_tracker(self):
        self.ensure_one()

        # Choose what messages to display
        open_mode = self._context.get('open_mode', 'from')

        if open_mode == 'tracker_user':
            domain = []
            if len(self.child_ids) > 0:
                domain.append('|')
                ids = []
                for _id in self.child_ids:
                    ids.append(_id.id)
                domain.append(('user_partner_id', 'in', ids))
            domain.append(('user_partner_id', 'in', self.ids))
        elif open_mode == 'tracker_buyer':
            domain = []
            if len(self.child_ids) > 0:
                domain.append('|')
                ids = []
                for _id in self.child_ids:
                    ids.append(_id.id)
                domain.append(('customer_id', 'in', ids))
            domain.append(('customer_id', 'in', self.ids))

        tree_view_id = self.env.ref('pu_tracker.pu_tracker_view_tree').id
        form_view_id = self.env.ref('pu_tracker.pu_tracker_view_form').id

        return {
            'name': _("GPS-Tracker"),
            'views': [[tree_view_id, "tree"], [form_view_id, "form"]],
            'res_model': 'pu.tracker',
            'type': 'ir.actions.act_window',
            # 'context': "{'check_messages_access': True}",
            'target': 'current',
            'domain': domain
        }