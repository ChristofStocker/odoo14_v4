import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class SignatureResCompany(models.Model):
    _inherit = "res.company"
    sales_org_id = fields.Char('Sales Organisation Id')
