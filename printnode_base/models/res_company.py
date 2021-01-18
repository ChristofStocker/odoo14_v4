# Copyright 2019 VentorTech OU
# License OPL-1.0 or later.

from odoo import fields, models, api

REPORT_DOMAIN = [
    ('model', '=', 'product.product'),
    ('report_type', 'in', ['qweb-pdf', 'qweb-text']),
]


class Company(models.Model):
    _inherit = 'res.company'

    printnode_enabled = fields.Boolean(
        string='Print via PrintNode',
        default=False,
    )

    printnode_printer = fields.Many2one(
        'printnode.printer',
        string='Printer',
    )

    printnode_recheck = fields.Boolean(
        string='Mandatory check Printing Status',
        default=False,
    )

    company_label_printer = fields.Many2one(
        'printnode.printer',
        string='Shipping Label Printer',
    )

    auto_send_slp = fields.Boolean(
        string='Auto-send to Shipping Label Printer',
        default=False,
    )

    im_a_teapot = fields.Boolean(
        string='Show success notifications',
        default=True,
    )

    wizard_report_ids = fields.Many2many(
        'ir.actions.report',
        string='Available Reports',
        domain=REPORT_DOMAIN,
    )

    def_wizard_report_id = fields.Many2one(
        'ir.actions.report',
        string='Default Report',
        domain=REPORT_DOMAIN,
    )


class Settings(models.TransientModel):
    _inherit = 'res.config.settings'

    printnode_enabled = fields.Boolean(
        readonly=False,
        related='company_id.printnode_enabled',
    )

    printnode_printer = fields.Many2one(
        'printnode.printer',
        readonly=False,
        related='company_id.printnode_printer',
    )

    printnode_recheck = fields.Boolean(
        readonly=False,
        related='company_id.printnode_recheck',
    )

    company_label_printer = fields.Many2one(
        'printnode.printer',
        readonly=False,
        related='company_id.company_label_printer',
    )

    auto_send_slp = fields.Boolean(
        readonly=False,
        related='company_id.auto_send_slp',
    )

    im_a_teapot = fields.Boolean(
        readonly=False,
        related='company_id.im_a_teapot',
    )

    wizard_report_ids = fields.Many2many(
        readonly=False,
        related='company_id.wizard_report_ids',
    )

    def_wizard_report_id = fields.Many2one(
        readonly=False,
        related='company_id.def_wizard_report_id',
    )

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super(Settings, self).fields_get()
        available_report_ids = self.env.company.wizard_report_ids.ids
        if available_report_ids:
            res['def_wizard_report_id']['domain'] = [('id', 'in', available_report_ids)]
        return res

    @api.onchange('wizard_report_ids')
    def _onchange_available_wizard_report(self):
        available_report_ids = self.wizard_report_ids.ids
        wizard_domain = [('id', 'in', available_report_ids)]

        if not available_report_ids:
            self.def_wizard_report_id = False
            wizard_domain = REPORT_DOMAIN
        elif self.def_wizard_report_id and self.def_wizard_report_id.id not in available_report_ids:
            self.def_wizard_report_id = available_report_ids[0]

        return {
            'domain': {
                'def_wizard_report_id': wizard_domain,
            },
        }
