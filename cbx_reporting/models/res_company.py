import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class cbx_reporting_sync(models.Model):
    _inherit = "res.company"
    sap_invoices_last_update_time = fields.Datetime('Last Update Reporting Invoices')
    sap_invoices_last_sync_id = fields.Char('Last Id Reporting Invoices')
