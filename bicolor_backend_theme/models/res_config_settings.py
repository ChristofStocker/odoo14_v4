###################################################################################
#
#    Copyright (C) 2017 MuK IT GmbH
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###################################################################################

import re
import uuid
import base64

from odoo import api, fields, models

XML_ID = "bicolor_backend_theme._assets_primary_variables"
SCSS_URL = "/bicolor_backend_theme/static/src/scss/colors.scss"


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    theme_color_brand = fields.Char(
        string="Theme Brand Color", related="company_id.theme_color_brand", readonly=False)
    
    theme_color_primary = fields.Char(
        string="Theme Primary Color", related="company_id.theme_color_primary", readonly=False)
    
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        variables = [
            'o-brand-odoo',
            'o-brand-primary',
        ]
        colors = self.env['bicolor_backend_theme.scss_editor'].get_values(
            SCSS_URL, XML_ID, variables
        )
        brand_changed = self.theme_color_brand != colors['o-brand-odoo']
        primary_changed = self.theme_color_primary != colors['o-brand-primary']
        if brand_changed or primary_changed:
            variables = [
                {'name': 'o-brand-odoo', 'value': self.theme_color_brand or "#243742"},
                {'name': 'o-brand-primary', 'value': self.theme_color_primary or "#5D8DA8"}
            ]
            self.env['bicolor_backend_theme.scss_editor'].replace_values(
                SCSS_URL, XML_ID, variables
            )
        return res

    @api.depends_context('force_company')
    def switch_company(self, company_id=False):
        company_selected = self.env['res.company'].browse(company_id)
        variables = [
            'o-brand-odoo',
            'o-brand-primary',
        ]
        colors = self.env['bicolor_backend_theme.scss_editor'].get_values(
            SCSS_URL, XML_ID, variables
        )
        colors["o-brand-odoo"] = company_selected.theme_color_brand
        colors["o-brand-primary"] = company_selected.theme_color_primary

        variables = [
            {'name': 'o-brand-odoo', 'value': colors["o-brand-odoo"] or "#243742"},
            {'name': 'o-brand-primary', 'value': colors["o-brand-primary"] or "#5D8DA8"}
        ]
        self.env['bicolor_backend_theme.scss_editor'].replace_values(
            SCSS_URL, XML_ID, variables
        )
        return

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        variables = [
            'o-brand-odoo',
            'o-brand-primary',
        ]
        colors = self.env['bicolor_backend_theme.scss_editor'].get_values(
            SCSS_URL, XML_ID, variables
        )
        res.update({
            'theme_color_brand': colors['o-brand-odoo'],
            'theme_color_primary': colors['o-brand-primary'],
        })
        return res

    @api.model
    def get_o_brand_primary(self):
        return "rgba(124,123,173,1)"