from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    notes = fields.Html('Notes')
    customer_id = fields.Char('Customer Id')
    supplier_id = fields.Char('Supplier Id')