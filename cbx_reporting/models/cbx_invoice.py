from odoo.exceptions import ValidationError
from odoo import models, fields
from datetime import datetime
from datetime import timedelta
import requests
from forex_python.converter import CurrencyRates
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
    invoice_name = fields.Char("InvoiceName")
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
    price_unit_eur = fields.Monetary("Listprice €", "currency_id_eur")
    price_unit_net_eur = fields.Monetary("Net price €", "currency_id_eur")
    price_unit_shipment_eur = fields.Monetary("Shipment price €", "currency_id_eur")
    margin_eur = fields.Monetary("Margin €", "currency_id_eur")
    average_purchase_price_eur = fields.Monetary("Purchase price ∅ €", "currency_id_eur")
    commission_eur = fields.Monetary("Commission €", "currency_id_eur")

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
                discount = (1 - row["KZWI6"] / row["KZWI1"]) * 100
            invoice_type = row["FKART"]

            margin = (row["KZWI6"] - row["WAVWR"]) or 0
            price_unit_net = row["KZWI6"] or 0
            list_price = float(row.KZWI1) or 0,
            list_price = float(''.join(map(str, list_price)))
            average_purchase_price = row["WAVWR"] or 0
            price_unit_shipment = (row["NETWR"] - row["KZWI6"]) or 0
            if currency_id == 11:
                margin = margin * 100
                price_unit_net = price_unit_net * 100
                list_price = list_price * 100
                average_purchase_price = average_purchase_price * 100
                price_unit_shipment = price_unit_shipment * 100
            quantity = float(row.FKLMG) or 0,
            quantity = float(''.join(map(str, quantity)))

            if invoice_type == "S1" or invoice_type == "RE" or invoice_type == "G2" \
                    or invoice_type == "IVS" or invoice_type == "IG":
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
            else:
                invoice = self.env['cbx.invoice'].search([('id', '=', _id), ])
                domain = ['&', ('company_id', '=', invoice.company_id.id),
                          ('currency_id', '=', 1),
                          ('name', '=', invoice.invoice_date),
                          ]
                currency_rate = self.env['res.currency.rate'].search(domain)
                rate = 0
                if len(currency_rate) > 0:
                    rate = currency_rate.rate
                else:
                    currency_name = invoice.currency_id.name
                    if currency_name == "RSD":
                        rate_date = str(invoice.invoice_date.year) + "-" \
                                    + ("00" + str(invoice.invoice_date.month))[-2:] + "-" \
                                    + ("00" + str(invoice.invoice_date.day))[-2:]
                        r = requests.get(f'https://currencies.apps.grandtrunk.net/getrate/{rate_date}/rsd/eur')
                        rate = float(r.text)
                    else:
                        c = CurrencyRates()
                        rate = c.get_rate(currency_name, 'EUR', invoice.invoice_date)
                    vals = {
                        'company_id': invoice.company_id.id,
                        'currency_id': 1,
                        'name': invoice.invoice_date,
                        'rate': rate,
                    }
                    self.env['res.currency.rate'].create(vals)
                    self.env.cr.commit()

                if rate != 0:
                    vals = {
                        'currency_id_eur': 1,
                        'price_unit_net_eur': (price_unit_net or 0) * float(rate),
                        'average_purchase_price_eur': (average_purchase_price or 0) * float(rate),
                        'margin_eur': (margin or 0) * float(rate),
                        'price_unit_shipment_eur': (price_unit_shipment or 0) * float(rate),
                        'commission_eur': (commission or 0) * float(rate),
                        'price_unit_eur': (price_unit or 0) * float(rate),
                    }
                    domain = [('id', '=', _id), ]
                    rec = self.env['cbx.invoice'].search(domain)
                    if len(rec) == 1:
                        rec.write(vals)
                        self.env.cr.commit()

    def _sync_salsys_invoices_initial(self, company_id, invoice_type=None):
        company = self.env['res.company'].search([('id', '=', company_id), ])
        sales_org = company.sales_org_id
        last_sync_id = company.sap_invoices_last_sync_id
        if not last_sync_id:
            last_sync_id = 0

        last_sync_id_sap = str(last_sync_id)

        sql = f"""
                Select
                    d.doc_number
                From
                    docs As d With(NoLock)
                Where
                    d.id_doc_type In (6, 21, 20) And
                    d.doc_canceled = 0 And
                    d.doc_export_accounting = 1 And
                    d.doc_number >= '{last_sync_id_sap}'
                    AND d.doc_date_tax >= '20190101' 
                Order By
                    d.doc_number
                OFFSET 0 ROWS FETCH NEXT 100 ROWS ONLY
                """
        data = addons_custom.stasto_base.methods.salsys_connection.get_data(self, query=sql)
        for index, row in data.iterrows():
            doc_number = str(row["doc_number"])
            self._sync_salsys_invoices(company_id, doc_number)
            company.update({
                'sap_invoices_last_sync_id': doc_number,
            })
            self.env.cr.commit()

    def _sync_salsys_invoices(self, company_id, invoice_id=None):
        domain = [('id', '=', company_id), ]
        company = self.env['res.company'].search(domain)
        sales_org = company.sales_org_id

        sql = f"""
                            Select
                            d.id_doc_type,
                            doc_type = dbo.kfn_translat(dt.guid_lng_constant, 0, Null),
                            d.doc_number,
                            d.doc_export_accounting,
                            d.doc_date,
                            d.doc_date,
                            d.doc_date_tax,
                            d.doc_disc_percent,
                            d.doc_vat_low,
                            d.doc_vat_high,
                            d.doc_price_0,
                            d.doc_price_low_vat,
                            d.doc_price_high_wo_vat,
                            d.doc_disc_price_0,
                            d.doc_disc_price_low,
                            d.doc_disc_price_low,
                            d.doc_price_sum,
                            d.doc_price_total,
                            d.doc_price_round,
                            c.cu_code,
                            dd.dd_exchange,
                            dd.dd_price_0_fc,
                            dd.dd_price_low_wo_vat_fc,
                            dd.dd_price_high_wo_vat_fc,
                            dd.dd_price_total_fc,
                            dl.dl_desc,
                            dl.dl_position,
                            dl.dl_amount,
                            dl.dl_price,
                            dl.dl_price_unit_disc,
                            dl.dl_price_sum_wo_vat,
                            ddl.dld_price_fc,
                            ddl.dld_price_unit_disc_fc,
                            ddl.dld_price_sum_wo_vat_fc,
                            p.product_id,
                            p.pr_type,
                            pr_desc_DE = dbo.kfn_translat(p.guid_lng_constant1, 0, Null),
                            pr_desc_EN = dbo.kfn_translat(p.guid_lng_constant1, 2, Null),
                            actual_purchase_price = Case
                                When dl.guid_ms_card Is Not Null
                                Then dbo.kfn_price_basic_ms_card2(dl.guid_ms_card, '89630571-CD31-4DD4-B0F9-90E1768AB5C1', GetDate(), 2)
                                Else 0
                            End,
                            document_purchase_price = Case
                                When dl.guid_ms_card Is Not Null
                                Then dbo.kfn_price_basic_ms_card2(dl.guid_ms_card, '89630571-CD31-4DD4-B0F9-90E1768AB5C1', d.doc_date, 2)
                                Else 0
                            End,
                            document_storage_avg_price = Cast(dbo.kfn_FT_disint_null(dbo.kfn_stock_recount(dl.guid_st_card, DateAdd(ms, 100,
                            d.doc_date)), ';', 2) As money)
                        From
                            docs As d With(NoLock) Inner Join
                            doc_types As dt On dt.id_doc_type = d.id_doc_type Left Join
                            currencies As c On c.id_currency = d.id_currency Left Join
                            doc_details As dd On dd.guid_doc = d.guid_doc Inner Join
                            doc_lists As dl On dl.guid_doc = d.guid_doc Left Join
                            doc_list_details As ddl On ddl.guid_doc_list = dl.guid_doc_list Left Join
                            ms_cards As msc On msc.guid_ms_card = dl.guid_ms_card Left Join
                            products As p On p.guid_product = msc.guid_product Inner Join
                            doc_types On d.id_doc_type = doc_types.id_doc_type
                        Where
                            d.id_doc_type In (6, 21, 20) And
                            d.doc_canceled = 0 And
                            d.doc_export_accounting = 1 And
                            d.doc_number = '{invoice_id}'
                        Order By
                            d.doc_number

                        """
        data = addons_custom.stasto_base.methods.salsys_connection.get_data(self, query=sql)
        for index, row in data.iterrows():
            cu_code = row.cu_code
            currency = ""
            if cu_code == "€":
                currency = "EUR"
            elif cu_code == "Kč":
                currency = "CZK"
            elif cu_code == "$":
                currency = "USD"
            if currency == "":
                break

            currency_id = self.env['res.currency'].search([('name', '=', f'{currency}')])["id"]
            # uom_id = self.env['uom.uom'].search([('id_ext', '=', f'{row["VRKME"]}')])["id"]
            if row["dl_price"] or 0 == 0:
                discount = 0
            else:
                discount = (1 - row["dl_price_unit_disc"] or 0 / row["dl_price"]) * 100
            invoice_type = row["doc_type"]

            quantity = float(row.dl_amount or 0),
            quantity = float(''.join(map(str, quantity)))

            average_purchase_price = float(row["document_storage_avg_price"] or 0) * quantity * 1.05

            margin = ((row["dl_price_sum_wo_vat"] or 0) - average_purchase_price)
            price_unit_net = row["dl_price_sum_wo_vat"] or 0

            list_price = (float(row.dl_price or 0)) * quantity

            # list_price = float(''.join(map(str, list_price)))

            price_unit_shipment = 0

            if currency_id == 11:
                margin = margin * 100
                price_unit_net = price_unit_net * 100
                list_price = list_price * 100
                average_purchase_price = average_purchase_price * 100
                price_unit_shipment = price_unit_shipment * 100

            if invoice_type == "credit_note":
                margin = -margin
                price_unit_net = -price_unit_net
                list_price = -list_price
                average_purchase_price = -average_purchase_price
                price_unit_shipment = -price_unit_shipment
                quantity = -quantity

            new_rec = {
                'company_id': company_id,
                'currency_id': currency_id,
                'invoice_type_ext': invoice_type or "",
                # 'customer_id_ext': row["KUNRG"].lstrip("0") or "",
                'name': row["doc_number"] or "",
                'invoice_pos': row["dl_position"] or "",
                'product_id_ext': row["product_id"] or "",
                # 'exchange_rate': row["KURSK"] or 0,
                'price_unit': list_price,
                'price_unit_net': price_unit_net,
                'price_unit_shipment': price_unit_shipment,
                'margin': margin,
                'discount': discount or 0,
                'quantity': quantity,
                'average_purchase_price': average_purchase_price,
                # 'weight': row["NTGEW"] or 0,
                'product_description': row["dl_desc"] or "",
                # 'delivery_ext': row["VGBEL"].lstrip("0") or "",
                # 'delivery_pos_ext': row["VGPOS"] or 0,
                # 'salesorder_ext': row["AUBEL"].lstrip("0") or "",
                # 'salesorder_pos_ext': row["AUPOS"] or 0,
                # 'product_uom_id': uom_id,
                'invoice_date': row["doc_date_tax"],
            }

            invoice_pos = self.env['cbx.invoice'] \
                .search(['&', ('name', '=', f'{row["doc_number"]}'),
                         ('invoice_pos', '=', f'{row["dl_position"]}'),
                         ])
            if len(invoice_pos) == 0:
                self.env['cbx.invoice'].create(new_rec)
            else:
                if len(invoice_pos) > 1:
                    sql = f"""delete from cbx_invoice where 
                                name='{row["doc_number"]}' and
                                and invoice_pos='{row["dl_position"]}'"""
                    self.env.cr.execute(sql)
                    self.env['cbx.invoice'].create(new_rec)
                else:
                    invoice_pos.write(new_rec)
            pass
            self.env.cr.commit()

