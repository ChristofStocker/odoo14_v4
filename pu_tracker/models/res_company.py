import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class pu_tracker_sync(models.Model):
    _inherit = "res.company"
    pu_last_sync_time = fields.Datetime('Last Sync GPS-Tracker Usage')
    pu_last_sync_time_produced = fields.Datetime('Last Sync GPS-Tracker Shipment')
    pu_last_sync_id_produced = fields.Char('Last Sync Id GPS-Tracker Shipment Initial')
