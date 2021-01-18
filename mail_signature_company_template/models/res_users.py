from odoo import api, fields, models

import logging

_logger = logging.getLogger(__name__)


class SignatureResUsers(models.Model):
    _inherit = "res.users"
    signature_name = fields.Char('Name')
    signature_name_dependent = fields.Char('Name', company_dependent=True)
    signature_email = fields.Char('Email')
    signature_email_dependent = fields.Char('Email', company_dependent=True)
    signature_phone = fields.Text('Phone', translate=True)
    signature_phone_dependent = fields.Text('Phone', company_dependent=True, translate=True)
    signature_position = fields.Text('Position', translate=True)
    signature_position_dependent = fields.Text('Position', company_dependent=True, translate=True)
    signature_country = fields.Char('Country', translate=True)
    signature_country_dependent = fields.Char('Country', company_dependent=True, translate=True)

    def write(self, vals):
        if vals.get('signature'):
            signature = vals['signature']
            signature = signature.replace("<p></p><!-- OrigSignatureStart --><p><br></p>", '')\
                .replace("<!-- OrigSignatureStart -->", '').replace("<!-- OrigSignatureEnd -->", '')
            vals['signature'] = "<p></p><!-- OrigSignatureStart --><p><br></p>"+signature+"<!-- OrigSignatureEnd -->"
        res = super(SignatureResUsers, self).write(vals)
        # self.get_bindings() depends on action records
        self.clear_caches()
        return res
