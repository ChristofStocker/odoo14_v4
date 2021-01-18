from odoo import api, SUPERUSER_ID

from . import models

#----------------------------------------------------------
# Hooks
#----------------------------------------------------------


XML_ID = "bicolor_backend_theme._assets_primary_variables"
SCSS_URL = "/bicolor_backend_theme/static/src/scss/colors.scss"

def _uninstall_reset_changes(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['bicolor_backend_theme.scss_editor'].reset_values(SCSS_URL, XML_ID)
