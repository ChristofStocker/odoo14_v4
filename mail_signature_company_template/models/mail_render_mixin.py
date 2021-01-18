from odoo import models, tools
from odoo.http import request
from odoo.exceptions import ValidationError
# from odoo import http
from odoo.tools.translate import _


class MailRenderMixin(models.AbstractModel):
    _inherit = "mail.render.mixin"

    def _replace_local_links(self, html, base_url=None):

        html = super()._replace_local_links(html, base_url=base_url)

        result = html
        signature = self.env.company.signature_email

        if not signature:
            signature = self.env.user.signature
        else:
            if "<!-- OrigSignatureStart -->" in result:
                pos1 = result.find('<!-- OrigSignatureStart -->')
                pos2 = result.find('<!-- OrigSignatureEnd -->')
                result = result[:pos1] + signature + result[pos2 + 25:]

        mail_template = self.env['mail.template']
        result = mail_template._debrand_body(result, "Gesendet")
        result = mail_template._debrand_body(result, "Powered by")
        skip = False
        try:
            session = request.session
        except (AttributeError, RuntimeError):
            skip = True

        if not skip:
            if 'base_url' not in session:
                session['base_url'] = None

            base_url = session['base_url']
            if not base_url:
                if self.id:
                    if 'signup_url' in self:
                        if self['signup_url']:
                            request.session['base_url'] = self['signup_url'].replace('https://', '') \
                                .replace('http://', '')
                else:
                    request.session['base_url'] = request.httprequest.base_url.replace('https://', '') \
                        .replace('http://', '')

        if base_url:
            base_url = base_url[0:base_url.find('/')]
            result = self.rewrite_url_domain(result, base_url)

        result = self.get_signature(result)
        if not '<!-- SignatureStart -->' in result:
            pass
        # result = result.replace('<!-- SignatureStart -->', '').replace('<!-- SignatureEnd -->', '')
        result = self.render_html(result)
        return result

    def rewrite_url_domain(self, html, base_url):
        # html = html.replace()
        model_class = self.env.company

        # company_id = getattr(model_class, "id")
        alias_domain = getattr(model_class, "alias_domain")
        if alias_domain:
            alias_domain = alias_domain.replace('http://', '').replace('https://', '')
            html = html.replace(base_url, alias_domain).replace("http://", "https://")

        return html

    def get_signature(self, html):
        html = html.replace('%24%7B', '${').replace('%7D', '}')
        pos1 = html.find('${')

        while pos1 > 0:
            pos2 = html.find('}', pos1) + 1
            field = html[pos1:pos2]
            model_id = field.replace('${object.', '').replace('}', '')
            property_name = model_id[model_id.find('.') + 1:]
            model_name = model_id.replace('.' + property_name, '')

            if property_name == "signature_image_url":
                signature_user = self.env.user.signature
                pos1 = signature_user.find("src=\"")
                pos2 = signature_user.find("\"", pos1 + 5)
                value = signature_user[pos1 + 5:pos2]
            else:
                if model_name == 'company_id':
                    model_class = self.env.company
                else:
                    model_class = self.env.user
                    # model_class.lang = "de_DE"

                if 'signature_' in property_name:
                    property_name = property_name + '_dependent'

                value = getattr(model_class, property_name)
                if not value:
                    value = getattr(model_class, property_name.replace('_dependent', ''))

            if value:
                value = str(value).replace('\n', '<br />').replace('http://', '')
                html = html.replace(field, value)
            else:
                html = html.replace(field, '')

            pos1 = html.find('${')

        html = html.replace('&amp;', '&')
        html = html.replace("b'", "data:image/jpg;base64,")
        return html

    def render_html(self, html):
        basecolor = self.env.company.primary_color
        if basecolor == '':
            basecolor = '#875A7B';
        html = html.replace('#875A7B', basecolor)
        return html
