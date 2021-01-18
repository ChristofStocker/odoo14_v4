
import base64

from lxml import html as htmltree

from odoo import _, api, models, fields, tools
from odoo.exceptions import UserError


class MailTemplate(models.Model):
    _inherit = "mail.template"
    name = fields.Char('Name', translate=True)

    @api.model
    def _debrand_body(self, html, text_line="Powered by"):

        powered_by = _(text_line)
        if powered_by not in html:
            return html
        root = htmltree.fromstring(html)
        powered_by_elements = root.xpath("//*[text()[contains(.,'%s')]]" % powered_by)
        for elem in powered_by_elements:
            # make sure it isn't a spurious powered by
            if any(
                [
                    "www.odoo.com" in child.get("href", "")
                    for child in elem.getchildren()
                ]
            ):
                for child in elem.getchildren():
                    elem.remove(child)
                elem.text = None

            if any(
                [
                    self.env.company.website in child.get("href", "")
                    for child in elem.getchildren()
                ]
            ):
                for child in elem.getchildren():
                    elem.remove(child)
                elem.text = None

        return htmltree.tostring(root).decode("utf-8")

    @api.model
    def render_post_process(self, html):
        html = super().render_post_process(html)
        return self._debrand_body(html)


