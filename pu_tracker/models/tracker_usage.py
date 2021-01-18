# -*- coding: utf-8 -*-

from odoo import models, fields


class pu_tracker_usage(models.Model):
    _name = 'pu.tracker.usage'
    _description = 'pu_tracker.pu_tracker_usage'

    tracker_id_internal = fields.Integer("Tracker Id Internal")
    tracker_id = fields.Char("Tracker Id")
    usage_id = fields.Char("Usage Id")
    user_email = fields.Char("Email")
    user_partner_id = fields.Many2one('res.partner', string='User')
    time_deleted = fields.Datetime("Deleted")
    time_activated = fields.Datetime("Activated")

