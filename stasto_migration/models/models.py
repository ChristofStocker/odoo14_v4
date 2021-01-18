# -*- coding: utf-8 -*-

from odoo import models, fields


class stasto_migration(models.Model):
    _name = 'stasto.migration'
    _description = 'stasto_migration.stasto_migration'

    key_old = fields.Char("Old Key")
    key_new = fields.Char("New Key")
    usage = fields.Many2one('stasto.migration.usage')
    default_bool = fields.Boolean("Default")

    description = fields.Text("Key Description")

    def write(self, vals):
        if vals.get('default_bool'):
            usage = str(self.usage["id"])
            self._cr.execute("UPDATE stasto_migration SET default_bool = FALSE WHERE default_bool = TRUE AND usage = '" + usage + "'")
        res = super(stasto_migration, self).write(vals)
        self.clear_caches()
        return res

    # @api.onchange('default_bool')
    # def _change_default_status(self):
    #     self._cr.execute("""UPDATE stasto_migration SET default_bool = FALSE WHERE default_bool = TRUE""")

class stasto_migration_usage(models.Model):
    _name = 'stasto.migration.usage'
    _description = 'Usage'

    name = fields.Char("Usage")
    keys = fields.One2many('stasto.migration', 'usage')
    description = fields.Text("Usage Description")


