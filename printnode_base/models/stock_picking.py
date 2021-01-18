# Copyright 2019 VentorTech OU
# License OPL-1.0 or later.

from odoo import models, fields, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'multi.print.mixin']

    shipping_label_ids = fields.One2many(
            comodel_name='shipping.label',
            inverse_name='picking_id',
            string='Shipping Labels',
        )

    def _create_shipping_label(self, message):
        label_attachments = [
            (0, 0, {'document_id': attach.id}) for attach in message.attachment_ids
        ]
        shipping_label_vals = {
            'carrier_id': self.carrier_id.id,
            'picking_id': self.id,
            'tracking_numbers': self.carrier_tracking_ref,
            'label_ids': label_attachments,
            'label_status': 'active',
        }
        self.env['shipping.label'].create(shipping_label_vals)

    def send_to_shipper(self):
        """ Redefining a standard method
        """
        user = self.env.user
        auto_print = user.company_id.auto_send_slp
        if auto_print:
            # Expected UserError if there is no one shipping label printer is available.
            user._get_shipping_label_printer()

        super(StockPicking, self).send_to_shipper()

        tracking_ref = self.carrier_tracking_ref
        if not tracking_ref:
            return
        messages_to_parse = self.env['mail.message'].search([
            ('model', '=', 'stock.picking'),
            ('res_id', '=', self.id),
            ('message_type', '=', 'notification'),
            ('attachment_ids', '!=', False),
            ('body', 'ilike', tracking_ref),
        ])
        for message in messages_to_parse:
            self._create_shipping_label(message)

        if auto_print and self.shipping_label_ids:
            self.print_last_shipping_label()

    def cancel_shipment(self):
        """ Redefining a standard method
        """
        for stock_pick in self:
            shipping_label = stock_pick.shipping_label_ids.filtered(
                lambda sl: sl.tracking_numbers == self.carrier_tracking_ref
            )
            shipping_label.write({'label_status': 'inactive'})
        return super(StockPicking, self).cancel_shipment()

    def print_last_shipping_label(self):
        self.ensure_one()

        if self.picking_type_code != 'outgoing':
            return

        label = self.shipping_label_ids[:1]
        if not (label and label.label_ids and label.label_status == 'active'):
            raise UserError(_(
                'There are no available "shipping labels" for printing, '
                'or last "shipping label" in state "In Active"'
            ))

        label.print_via_printnode()

    def _add_multi_print_lines(self):
        product_lines = []
        unit_uom = self.env.ref('uom.product_uom_unit')
        for move in self.move_lines:
            quantity = 1
            if move.product_uom == unit_uom:
                quantity = move.product_uom_qty

            product_lines.append(
                (0, 0, {
                    'product_id': move.product_id.id,
                    'quantity': quantity},
                 )
            )
        return product_lines
