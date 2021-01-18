from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
import html2text


class SignatureResCompany(models.Model):
    _inherit = "res.company"
    signature_email = fields.Html('Signature')
    alias_domain = fields.Char('Alias (Domain)')

    def write(self, vals):
        if vals.get('signature_email'):
            signature = vals.get('signature_email')
            signature = signature.replace("<p></p><!-- SignatureStart --><p><br></p>", '')\
                .replace("<!-- SignatureStart -->", '').replace("<!-- SignatureEnd -->", '')
            vals['signature_email'] = "<p></p><!-- SignatureStart --><p><br></p>"+signature+"<!-- SignatureEnd -->"
        
        res = super(SignatureResCompany, self).write(vals)
        # self.get_bindings() depends on action records
        self.clear_caches()
        return res
