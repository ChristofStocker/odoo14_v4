
from odoo import fields, models, api


class CbxProductTemplate(models.Model):
    _inherit = "product.template"

    cbx_matchcode = fields.Char("Matchcode")
