# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    theme_color_brand = fields.Char(company_dependent=True, string="Theme Brand Color", default="rgba(124,123,173,1)",
                                    help="Set color here to change the color of the Top menu bar")

    theme_color_primary = fields.Char(company_dependent=True, string="Theme Primary Color",
                                      default="rgba(124,123,173,1)",
                                      help="Set color here to change the color of the buttons, links etc.,")

    # @api.depends_context('force_company')
    # def _get_current_company(self):
    #     # val = self.theme_color_primary
    #     # vale = self.env['res.users'].browse(self.uid)
    #     company_id = self.env.company.id
    #     return company_id
