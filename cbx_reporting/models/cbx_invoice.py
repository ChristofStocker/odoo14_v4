
from odoo.exceptions import ValidationError
from odoo import models, fields
from datetime import datetime
from datetime import timedelta
import addons_custom.stasto_base

from .. import methods


class cbx_invoice(models.Model):
    _name = 'cbx.invoice'
    _description = 'Invoice'
    # _rec_name = 'invoice_name'

    name = fields.Char("Invoice#")
    company_id = fields.Many2one("res.company", string="Company")

    customer_id = fields.Many2one('res.partner', string='Customer')
    customer_id_ext = fields.Char("Customer Id external")

    product_id = fields.Many2one('product.template', string='Product')
    product_id_ext = fields.Char("Product Id external")
    weight = fields.Float("Weight")
    product_description = fields.Char("Product Description")
    product_uom_id = fields.Many2one("uom.uom", string="Unit")
    quantity = fields.Float("Quantity")

    invoice_type_ext = fields.Char("Invoice Type external")
    invoice_name = fields.Char("Invoice#")
    invoice_pos = fields.Char("Pos")
    invoice_canceled = fields.Boolean("Invoice canceled")
    invoice_date = fields.Date("Date")
    invoice_payment_term_ext = fields.Char("Method of payment")
    invoice_payment_term_id = fields.Many2one("account.payment.term", string="Payment term")

    discount = fields.Float("Discount")

    exchange_rate = fields.Float("Exchange rate")

    delivery_ext = fields.Char("Delivery# external")
    delivery_pos_ext = fields.Char("Delivery pos external")

    salesorder_ext = fields.Char("Salesorder# external")
    salesorder_pos_ext = fields.Char("Salesorder pos external")

    currency_id = fields.Many2one("res.currency", string="Currency")
    price_unit = fields.Monetary("Listprice", "currency_id")
    price_unit_net = fields.Monetary("Net price", "currency_id")
    price_unit_shipment = fields.Monetary("Shipment price", "currency_id")
    margin = fields.Monetary("Margin", "currency_id")
    average_purchase_price = fields.Monetary("Purchase price ∅", "currency_id")
    commission = fields.Monetary("Commission", "currency_id")

    currency_id_eur = fields.Many2one("res.currency", string="Currency €")
    price_unit_eur = fields.Monetary("Listprice €", "currency_id")
    price_unit_net_eur = fields.Monetary("Net price €", "currency_id")
    price_unit_shipment_eur = fields.Monetary("Shipment price €", "currency_id")
    margin_eur = fields.Monetary("Margin €", "currency_id")
    average_purchase_price_eur = fields.Monetary("Purchase price ∅ €", "currency_id")
    commission_eur = fields.Monetary("Commission €", "currency_id")

    def _sync_sap_invoices_initial(self, company_id, invoice_type=None):
        company = self.env['res.company'].search([('id', '=', company_id), ])
        sales_org = company.sales_org_id
        last_sync_id = company.sap_invoices_last_sync_id
        if not last_sync_id:
            last_sync_id = 0

        last_sync_id_sap = str(last_sync_id)

        # Code - Code Start
        if invoice_type:
            sql = f"""
                                select 
                                    VBRK.VBELN
                                from VBRK
                                inner join VBRP on (VBRK.VBELN = VBRP.VBELN)
                                where VBRK.VKORG='{sales_org}'
                                and VBRK.FKART = '{invoice_type}'
                                group by VBRK.VBELN
                                order by VBRK.VBELN
                            """
        else:
            sql = f"""
                    select 
                        VBRK.VBELN
                    from VBRK
                    inner join VBRP on (VBRK.VBELN = VBRP.VBELN)
                    where VBRK.VKORG='{sales_org}'
                    and VBRK.VBELN >= '{last_sync_id_sap}'
                    group by VBRK.VBELN
                    order by VBRK.VBELN
                    limit 300
                """
        data = addons_custom.stasto_base.methods.hdb_connection.get_data(self, query=sql)
        for index, row in data.iterrows():
            vbeln = str(row["VBELN"])
            self._sync_sap_invoices(company_id, row["VBELN"])
            company.update({
                'sap_invoices_last_sync_id': vbeln,
            })
            self.env.cr.commit()
        # Code - End

    def _sync_sap_invoices_update(self, company_id):
        company = self.env['res.company'].search([('id', '=', company_id), ])
        sales_org = company.sales_org_id
        last_sync_time = company.sap_invoices_last_update_time
        new_last_sync_time = datetime.now()
        if not last_sync_time:
            last_sync_time = new_last_sync_time - timedelta(days=1)

        # Code - Code Start
        sql = f"""
                select 
                    VBRK.VBELN
                from VBRK
                inner join VBRP on (VBRK.VBELN = VBRP.VBELN)
                where VBRK.VKORG='{sales_org}'
                and VBRK.FKDAT>='{methods.pu_datetime.to_sapdate(new_last_sync_time - timedelta(days=1))}'
                group by VBRK.VBELN
                order by VBRK.VBELN desc
            """
        data = addons_custom.stasto_base.methods.hdb_connection.get_data(self, query=sql)
        for index, row in data.iterrows():
            self._sync_sap_invoices(company_id, row["VBELN"])

        sql = f"""
                select cdpos.objectid as VBELN, cdhdr.udate from cdhdr
                    inner join cdpos on (cdhdr.changenr = cdpos.changenr)
                    where 
                    cdpos.objectclas = 'FAKTBELEG' 
                    and (cdpos.tabname = 'VBRP' or cdpos.tabname = 'VBRK')
                    and cdhdr.udate >= '{methods.pu_datetime.to_sapdate(new_last_sync_time - timedelta(days=1))}'
            """
        data = addons_custom.stasto_base.methods.hdb_connection.get_data(self, query=sql)
        for index, row in data.iterrows():
            self._sync_sap_invoices(company_id, row["VBELN"])
        # Code - End
        company.update({
            'sap_invoices_last_update_time': methods.pu_datetime.to_datetime_from_db(new_last_sync_time),
        })
        self.env.cr.commit()

    def _sync_sap_invoices(self, company_id, invoice_id=None):
        domain = [('id', '=', company_id), ]
        company = self.env['res.company'].search(domain)
        sales_org = company.sales_org_id

        if invoice_id is None:
            sql = f"""
                        select 
                            VBRK.VKORG, VBRK.MANDT, VBRK.VBELN, VBRK.WAERK, VBRK.FKDAT, VBRK.KDGRP, VBRK.ERNAM, 
                            VBRK.KUNRG, VBRK.STWAE, VBRK.LANDTX, VBRK.FKART,
                            VBRP.POSNR, VBRP.FKLMG, VBRP.VRKME, VBRP.NTGEW, VBRP.NETWR, VBRP.KZWI1, VBRP.KZWI6, VBRP.WAVWR, 
                            VBRP.KURSK, VBRP.VGBEL, VBRP.VGPOS, VBRP.AUBEL, VBRP.AUPOS, VBRP.MATNR, VBRP.ARKTX, VBRP.WERKS, 
                            VBRP.CMPRE, VBRP.BRTWR
                        from VBRK
                        inner join VBRP on (VBRK.VBELN = VBRP.VBELN)
                        where VBRK.VKORG='{sales_org}'
                        order by VBRK.VBELN desc
                    """
        else:
            sql = f"""
                                    select 
                                        VBRK.VKORG, VBRK.MANDT, VBRK.VBELN, VBRK.WAERK, VBRK.FKDAT, VBRK.KDGRP, VBRK.ERNAM, 
                                        VBRK.KUNRG, VBRK.STWAE, VBRK.LANDTX, VBRK.FKART,
                                        VBRP.POSNR, VBRP.FKLMG, VBRP.VRKME, VBRP.NTGEW, VBRP.NETWR, VBRP.KZWI1, VBRP.KZWI6, VBRP.WAVWR, 
                                        VBRP.KURSK, VBRP.VGBEL, VBRP.VGPOS, VBRP.AUBEL, VBRP.AUPOS, VBRP.MATNR, VBRP.ARKTX, VBRP.WERKS, 
                                        VBRP.CMPRE, VBRP.BRTWR
                                    from VBRK
                                    inner join VBRP on (VBRK.VBELN = VBRP.VBELN)
                                    where VBRK.VKORG='{sales_org}'
                                    and VBRK.VBELN='{invoice_id}'
                                    order by VBRK.VBELN desc
                                """
        data = addons_custom.stasto_base.methods.hdb_connection.get_data(self, query=sql)
        for index, row in data.iterrows():
            currency_id = self.env['res.currency'].search([('name', '=', f'{row["WAERK"]}')])["id"]
            uom_id = self.env['uom.uom'].search([('id_ext', '=', f'{row["VRKME"]}')])["id"]
            if row["KZWI1"] == 0:
                discount = 0
            else:
                discount = (1-row["KZWI6"]/row["KZWI1"])*100
            invoice_type = row["FKART"]
            margin = (row["KZWI6"] - row["WAVWR"]) or 0
            price_unit_net = row["KZWI6"] or 0
            list_price = float(row.KZWI1) or 0,
            list_price = float(''.join(map(str, list_price)))
            average_purchase_price = row["WAVWR"] or 0
            price_unit_shipment = (row["NETWR"]-row["KZWI6"]) or 0
            quantity = float(row.FKLMG) or 0,
            quantity = float(''.join(map(str, quantity)))

            if invoice_type == "S1" or invoice_type == "RE" or invoice_type == "G2"\
                    or invoice_type == "IVS":
                margin = -margin
                price_unit_net = -price_unit_net
                list_price = -list_price
                average_purchase_price = -average_purchase_price
                price_unit_shipment = -price_unit_shipment
                quantity = -quantity
            new_rec = {
                'company_id': company.id,
                'currency_id': currency_id,
                'invoice_type_ext': invoice_type or "",
                'customer_id_ext': row["KUNRG"].lstrip("0") or "",
                'name': row["VBELN"].lstrip("0") or "",
                'invoice_pos': row["POSNR"] or "",
                'product_id_ext': row["MATNR"].lstrip("0") or "",
                'exchange_rate': row["KURSK"] or 0,
                'price_unit': list_price,
                'price_unit_net': price_unit_net,
                'price_unit_shipment': price_unit_shipment,
                'margin': margin,
                'discount': discount or 0,
                'quantity': quantity,
                'average_purchase_price': average_purchase_price,
                'weight': row["NTGEW"] or 0,
                'product_description': row["ARKTX"] or "",
                'delivery_ext': row["VGBEL"].lstrip("0") or "",
                'delivery_pos_ext': row["VGPOS"] or 0,
                'salesorder_ext': row["AUBEL"].lstrip("0") or "",
                'salesorder_pos_ext': row["AUPOS"] or 0,
                'product_uom_id': uom_id,
                'invoice_date': methods.pu_datetime.to_date_from_hdb(row["FKDAT"]),

            }

            invoice_pos = self.env['cbx.invoice'] \
                .search(['&', ('name', '=', f'{row["VBELN"].lstrip("0")}'),
                         ('invoice_pos', '=', f'{row["POSNR"]}'),
                         ])
            if len(invoice_pos) == 0:
                self.env['cbx.invoice'].create(new_rec)
            else:
                if len(invoice_pos) > 1:
                    sql = f"""delete from cbx_invoice where 
                                name='{row["VBELN"].lstrip("0")}' and
                                and invoice_pos='{row["POSNR"]}'"""
                    self.env.cr.execute(sql)
                    self.env['cbx.invoice'].create(new_rec)
                else:
                    invoice_pos.write(new_rec)
            pass
            self.env.cr.commit()

    def _convert_monetary_exchangerate(self):
        sql = f"""
                    update cbx_invoice
                        set 
                            price_unit_net_eur = price_unit_net,
                            average_purchase_price_eur = average_purchase_price,
                            margin_eur = margin,
                            price_unit_shipment_eur = price_unit_shipment,
                            commission_eur = commission,
                            price_unit_eur = price_unit,
                            currency_id_eur = '1'
                        where 
                            currency_id_eur is null
                            and currency_id = '1'
                """
        self.env.cr.execute(sql)
        self.env.cr.commit()

        sql = f"""
            select id, currency_id, exchange_rate, price_unit_net, average_purchase_price, margin,
                price_unit_shipment, commission, price_unit
            from cbx_invoice
                where currency_id_eur is null
                and currency_id <> '1'
                order by id desc
            limit 10000
        """
        self.env.cr.execute(sql)
        result = self.env.cr.fetchall()
        for _id, currency_id, exchange_rate, price_unit_net, average_purchase_price, margin, price_unit_shipment, \
                commission, price_unit in result:
            if currency_id == 1:
                vals = {
                    'currency_id_eur': 1,
                    'price_unit_net_eur': price_unit_net,
                    'average_purchase_price_eur': average_purchase_price,
                    'margin_eur': margin,
                    'price_unit_shipment_eur': price_unit_shipment,
                    'commission_eur': commission,
                    'price_unit_eur': price_unit,
                }
                domain = [('id', '=', _id), ]
                rec = self.env['cbx.invoice'].search(domain)
                if len(rec) == 1:
                    rec.write(vals)
                    self.env.cr.commit()
