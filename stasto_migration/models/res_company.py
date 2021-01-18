import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class pu_tracker_sync(models.Model):
    _inherit = "res.company"
    stasto_crm_last_initial_sync_id = fields.Integer('STASTO CRM - last initial Sync contact_id')
    stasto_crm_last_sync_time_partner_updated = fields.Datetime('STASTO CRM - last synchronisation time contact')
