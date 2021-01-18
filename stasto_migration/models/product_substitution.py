from odoo import models, fields


class stasto_substitution(models.Model):
    _name = 'stasto.substitution'
    _description = 'stasto_migration.stasto_substitution'

    product_id_old = fields.Char("Product Id old")
    product_id = fields.Many2one('product.template', string='Product')