import logging

from odoo import _, api, fields, models, modules, tools
from odoo.exceptions import ValidationError

from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class Message(models.Model):
    _inherit = 'mail.message'

    @api.model_create_multi
    def create(self, vals_list):
        used_model_res_partner = False
        for vals in vals_list:
            if vals.get('model') == "res.partner":
                used_model_res_partner = True
            if vals.get('subtype_id') == self.env.ref('mail.mt_comment').id and vals.get('model') \
                    and vals.get('res_id') and hasattr(self.env[vals.get('model')], 'company_id'):
                record_company_id = self.env[vals.get('model')].browse(vals.get('res_id')).company_id
                if self.env[vals.get('model')].browse(vals.get('res_id')).company_id \
                        and self.env.company != record_company_id and vals.get('message_type') == "comment":
                    raise ValidationError(_("This record is from {}, and you are trying to send an email from {}".format(record_company_id.name, self.env.company.name)))

        if used_model_res_partner:
            active_id = self._context.get('active_id')
            partner_obj = self.env['res.partner']
            domain = [('id', '=', active_id)]
            partner = partner_obj.search(domain)
            partner_company_id = partner["company_id"].id
            if self.env.company.id != partner_company_id and partner_company_id:
                raise ValidationError(_(
                    "This record is from {}, and you are trying to send an email from {}".format(partner["company_id"].name,
                                                                                                 self.env.company.name)))

        return super(Message, self).create(vals_list)
