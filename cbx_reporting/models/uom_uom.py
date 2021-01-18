
from odoo import fields, models


class CbxProductTemplate(models.Model):
    _inherit = "uom.uom"

    id_ext = fields.Char("External Id")
