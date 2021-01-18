
from odoo import fields, models


class CbxProductTemplate(models.Model):
    _inherit = "product.template"

    preferential_country_of_origin = fields.Boolean("Preferential treatment")
