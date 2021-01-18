# Copyright 2019 VentorTech OU
# License OPL-1.0 or later.

from odoo import models, fields


class ShippingLabel(models.Model):
    """ Shipping Label entity from Delivery Carrier
    """
    _name = 'shipping.label'
    _description = 'Shipping Label'
    _rec_name = 'picking_id'
    _order = 'create_date desc'

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        string='Delivery Carrier',
        required=True,
        readonly=True,
    )

    picking_id = fields.Many2one(
        comodel_name='stock.picking',
        string='Delivery Order',
        domain='[("picking_type_id.code", "=", "outgoing")]',
        required=True,
        readonly=True,
    )

    tracking_numbers = fields.Char(
        string='Tracking Number(s)',
        readonly=True,
    )

    label_ids = fields.One2many(
        comodel_name='shipping.label.document',
        inverse_name='shipping_id',
        string='Shipping Label(s)',
        ondelete='cascade',
        readonly=True,
        copy=False,
    )

    label_status = fields.Selection(
        [
            ('active', 'Active'),
            ('inactive', 'In Active'),
        ],
        string='Status',
    )

    def _get_attachment_list(self):
        self.ensure_one()
        attachment_list = []
        paper_id = self.carrier_id.autoprint_paperformat_id
        for label in self.label_ids:
            doc = label.document_id
            doc_name = doc.name
            qtype = 'qweb-pdf' if doc_name.lower().endswith('.pdf') else 'qweb-text'
            params = {
                'title': doc_name,
                'type': qtype,
                'size': paper_id,
            }
            attachment_list.append((doc.datas.decode('ascii'), params))
        return attachment_list

    def print_via_printnode(self):
        user = self.env.user
        printer = user._get_shipping_label_printer()

        for ship_lab in self:
            attachment_list = ship_lab._get_attachment_list()
            if not attachment_list:
                continue
            for ascii_data, params in attachment_list:
                printer.printnode_print_b64(ascii_data, params)


class ShippingLabelDocument(models.Model):
    """ Attached Document to the Shipping Label entity
    """
    _name = 'shipping.label.document'
    _description = 'Shipping Label Document'
    _rec_name = 'document_id'

    shipping_id = fields.Many2one(
        string='Related Shipping Label',
    )

    document_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Shipping Label Document',
    )
