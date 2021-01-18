# -*- coding: utf-8 -*-

import math
from datetime import datetime
from datetime import timedelta
from odoo import models, fields
import addons_custom.stasto_base
import pandasql as ps

from .. import methods


class pu_tracker(models.Model):
    _name = 'pu.tracker'
    _description = 'GPS-Tracker'
    _rec_name = 'tracker_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    tracker_id = fields.Char("Tracker Id")
    subscription_id = fields.Char("Subscription Id")
    trial_duration = fields.Integer("Trial Duration (Days)")
    customer_id = fields.Many2one('res.partner', string='Reseller')
    customer_id_ext = fields.Char("Customer Id ext")
    customer = fields.Html("Shipped to")
    shipment_id_ext = fields.Char("Shipment Id ext")
    user_partner_id = fields.Many2one('res.partner', string='User')
    date_activation = fields.Date('Activationdate')
    time_created = fields.Datetime('Created at')
    time_updated = fields.Datetime('Updated at')
    delivered_at = fields.Date('Delivered at')
    iccid = fields.Char("ICCID")
    setup_fee = fields.Boolean("Setup fee")
    date_trial_end = fields.Date("End of Trial")
    usage_id = fields.One2many('pu.tracker.usage', 'tracker_id_internal', string='Usage')
    last_sync_time = fields.Datetime('Last Synchronisation')
    active_device = fields.Boolean("Active")
    user_email = fields.Char("Email")
    activation_count = fields.Integer("Activations")
    material_nr = fields.Char("Material Id")
    sync_disabled = fields.Boolean("Synchronisation disabled")

    def subscription_sync(self):
        pu_tracker.pu_tracker_sync(self, self.tracker_id)
        return self

    def multi_pu_tracker_sync_selected(self):
        for rec in self:
            pass
        return self

    def pu_tracker_sync(self, tracker_id, pd_data=None):
        # for rec in self:
        #     pass
        load_usage = False
        if pd_data is not None:
            sql = f"SELECT * from pd_data where deviceId='{tracker_id}'"
            data = ps.sqldf(sql, locals())
            load_usage = True
        else:
            if tracker_id:
                sql = f"SELECT * from subscription where deviceId={tracker_id} order by trialEnd;"
                load_usage = True
            else:
                domain = [
                    ('id', '=', 2),
                ]
                company = self.env['res.company'].search(domain)
                last_sync_time = company.pu_last_sync_time

                sql = f"""SELECT * from subscription 
                            where
                                subscription.`updatedAt` >= '{last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}'
                            order by createdAt desc;"""
            data = methods.pu_mysqldb.get_traccar_data(self, query=sql)

        for index, row in data.iterrows():
            trial_duration = row["trialDuration"]
            if trial_duration is None or math.isnan(trial_duration):
                trial_duration = 0

            setup_fee = False
            if row["setupFee"] == 1:
                setup_fee = True

            tracker_id = row["deviceId"]

            domain = [
                ('tracker_id', '=', row["deviceId"])
            ]
            tracker = self.env['pu.tracker'].search(domain)

            last_sync_time = None
            active = False
            customer = None
            iccid = None
            wa_matnr = None
            email = None
            activation_count = 0
            if load_usage:
                active, email, activation_count = pu_tracker.pu_tracker_sync_usage(self, tracker_id, tracker.id)
                last_sync_time = datetime.now()
                customer = pu_tracker.get_old_customer(self, tracker_id)
                iccid = pu_tracker.get_iccid(self, tracker_id)
                wa_matnr = pu_tracker.get_shipment_data(self, tracker_id)

            rec = {
                'tracker_id': tracker_id,
                'subscription_id': row["subscriptionId"],
                'trial_duration': trial_duration,
                'customer': customer,
                'user_email': email,
                'last_sync_time': last_sync_time,
                'active_device': active,
                'activation_count': activation_count,
                # 'user_partner_id': None,
                'time_created': methods.pu_datetime.to_datetime_from_db(row["createdAt"]),
                'time_updated': methods.pu_datetime.to_datetime_from_db(row["updatedAt"]),
                'date_trial_end': methods.pu_datetime.to_datetime_from_db(row["trialEnd"]),
                'setup_fee': setup_fee,
                'iccid': iccid,
                'material_nr': wa_matnr,
            }

            if tracker:
                tracker.update(rec)
            else:
                tracker = self.env['pu.tracker'].create(rec)
            self.env.cr.commit()
        return self

    def pu_tracker_sync_usage(self, tracker_id: object, tracker_id_internal: object) -> object:
        # for rec in self:
        #     pass
        activation_count = 0
        sql = f"SELECT * from `usage` where uniqueId={tracker_id} order by createdAt"
        data = methods.pu_mysqldb.get_traccar_data(self, query=sql)
        ids = []
        active = False
        email = False
        for index, row in data.iterrows():
            rec = {
                'tracker_id': row["uniqueId"],
                'tracker_id_internal': tracker_id_internal,
                'usage_id': row["deviceId"],
                'user_email': row["userEmail"],
                'time_activated': methods.pu_datetime.to_datetime_from_db(row["createdAt"]),
                'time_deleted': methods.pu_datetime.to_datetime_from_db_deleted(row["deleted"]),
            }
            activation_count = activation_count + 1
            domain = [
                ('tracker_id', '=', row["uniqueId"]),
                ('usage_id', '=', row["deviceId"]),
            ]
            usage = self.env['pu.tracker.usage'].search(domain)
            if usage:
                usage.update(rec)
            else:
                usage = self.env['pu.tracker.usage'].create(rec)
            self.env.cr.commit()
            if usage.time_deleted.year == 9999:
                active = True
                email = row["userEmail"]
            ids.append(usage.id)
        return active, email, activation_count

    def write(self, vals):
        if vals.get('trial_duration'):
            sql = f"update subscription set trialDuration = {vals['trial_duration']} where deviceId={self.tracker_id};"
            vals['sync_disabled'] = True
            methods.pu_mysqldb.db_execute(self, query=sql)
        if vals.get('user_partner_id'):
            user_partner_id = vals['user_partner_id']
            if user_partner_id > 0:
                sql = f"update `usage` set customerId = '{user_partner_id}' where uniqueId={self.tracker_id} and isnull(deleted);"
            else:
                sql = f"update `usage` set customerId = Null where uniqueId={self.tracker_id} and isnull(deleted);"
            methods.pu_mysqldb.db_execute(self, query=sql)

        if vals.get('setup_fee') is not None:
            if vals.get('setup_fee'):
                sql = f"update subscription set setupFee = 1 where deviceId={self.tracker_id};"
                methods.pu_mysqldb.db_execute(self, query=sql)
            elif not vals.get('setup_fee'):
                sql = f"update subscription set setupFee = Null where deviceId={self.tracker_id};"
                methods.pu_mysqldb.db_execute(self, query=sql)
            vals['sync_disabled'] = True

        res = super(pu_tracker, self).write(vals)
        # self.get_bindings() depends on action records
        # self.clear_caches()
        return res

    def get_old_customer(self, tracker_id):

        html = f"""
                                    <table>
                                        <tr>
                                            <td width='100'><b>Customer#</b></td>
                                            <td width='150'><b>Customer</b></td>
                                            <td width='80'><b>Zip Code</b></td>
                                            <td width='100'><b>City</b></td>
                                            <td width='40'><b>Country</b></td>
                                            <td width='150'><b>Name</b></td>
                                            <td width='200'><b>Email</b></td>
                                        </tr>

                        """

        sql = f"Select" \
              f"    `1_materialbewegung`.GUID," \
              f"    `1_materialbewegung`.WA_VBELN," \
              f"    `1_materialbewegung`.KUNNR," \
              f"    crm_kontakte.TYP," \
              f"    crm_kontakte.TYPID," \
              f"    crm_kontakte.BEZEICHNUNG," \
              f"    crm_kontakte.POSTLEITZAHL," \
              f"    crm_kontakte.ORT," \
              f"    crm_kontakte.LANDISO," \
              f"    crm_kommunikation.KOM_TYP," \
              f"    crm_kommunikation.WERT1," \
              f"    crm_kontakte2.BEZEICHNUNG As BEZEICHNUNG1" \
              f" From" \
              f"    `1_materialbewegung` Inner Join" \
              f"    crm_kontakte On crm_kontakte.TYPID = `1_materialbewegung`.KUNNR Inner Join" \
              f"    crm_kontakte_verknuepfung On crm_kontakte_verknuepfung.ID1 = crm_kontakte.ID" \
              f"    Inner Join" \
              f"    crm_kontakte2 On crm_kontakte2.ID = crm_kontakte_verknuepfung.ID2" \
              f"    Right Join" \
              f"    crm_kommunikation On crm_kommunikation.ID_KONTAKT1 = crm_kontakte_verknuepfung.ID1" \
              f"            And crm_kommunikation.ID_KONTAKT2 = crm_kontakte_verknuepfung.ID2 " \
 \
              f" Where" \
              f"    `1_materialbewegung`.GUID = '{tracker_id}' And" \
              f"    (crm_kontakte.TYP = 'KUNDE' Or crm_kontakte.TYP = 'PRIVATADRESSE' Or" \
              f"        crm_kontakte.TYP = 'LIEFERADRESSE') And" \
              f"    crm_kommunikation.KOM_TYP = 'EMAIL1'"
        data = methods.st_mysqldb.get_data(self, query=sql)
        for index, row in data.iterrows():
            html += f"""
                        <tr>
                        <td>{row["TYPID"]}</td>
                        <td>{row["BEZEICHNUNG"]}</td>
                        <td>{row["POSTLEITZAHL"]}</td>
                        <td>{row["ORT"]}</td>
                        <td>{row["LANDISO"]}</td>
                        <td>{row["BEZEICHNUNG1"]}</td>
                        <td>{row["WERT1"]}</td>
                        </tr>
                    """
        if data.empty:
            sql = f"""
            SELECT    `1_materialbewegung`.GUID,    `1_materialbewegung`.WA_VBELN,    `1_materialbewegung`.KUNNR,    
                crm_kontakte.TYP,    crm_kontakte.TYPID,    crm_kontakte.BEZEICHNUNG,    crm_kontakte.POSTLEITZAHL,    
                crm_kontakte.ORT,    
                crm_kontakte.LANDISO,    crm_kontakte2.BEZEICHNUNG AS BEZEICHNUNG1 
                FROM    `1_materialbewegung` 
                LEFT JOIN    crm_kontakte ON crm_kontakte.TYPID = `1_materialbewegung`.KUNNR 
                LEFT JOIN    crm_kontakte_verknuepfung ON crm_kontakte_verknuepfung.ID1 = crm_kontakte.ID    
                LEFT JOIN    crm_kontakte2 ON crm_kontakte2.ID = crm_kontakte_verknuepfung.ID2 
                WHERE    `1_materialbewegung`.GUID = '{tracker_id}' 
                AND    (crm_kontakte.TYP = 'KUNDE' OR crm_kontakte.TYP = 'PRIVATADRESSE' 
                    OR crm_kontakte.TYP = 'LIEFERADRESSE')
                """
            data = methods.st_mysqldb.get_data(self, query=sql)
            for index, row in data.iterrows():
                html += f"""
                            <tr>
                            <td>{row["TYPID"]}</td>
                            <td>{row["BEZEICHNUNG"]}</td>
                            <td>{row["POSTLEITZAHL"]}</td>
                            <td>{row["ORT"]}</td>
                            <td>{row["LANDISO"]}</td>
                            <td>{row["BEZEICHNUNG1"]}</td>
                            <td></td>
                            </tr>
                        """

        html += f"""         
                            </table>
                """

        return html

    def get_iccid(self, tracker_id):
        sql = f"select ICCID from 1_pu_device_ids where QRCode = '{tracker_id}'"
        data = methods.st_mysqldb.get_data(self, query=sql)
        iccid = 0
        for index, row in data.iterrows():
            iccid = row["ICCID"]
        return iccid

    def get_shipment_data(self, tracker_id):
        sql = f"""
                        Select
                            `1_materialbewegung`.GUID,
                            `1_materialbewegung`.MATNR,
                            `1_materialbewegung`.WA_VBELN,
                            `1_materialbewegung`.WA_POSNR,
                            `1_materialbewegung`.WA_WERK,
                            `1_materialbewegung`.WA_MATNR,
                            `1_materialbewegung`.WA_MATNR_UEPOS,
                            `1_materialbewegung`.WA_ZEIT,
                            `1_materialbewegung`.KUNNR,
                            `1_materialbewegung`.KUNAG
                        From
                            `1_materialbewegung`
                        Where
                            `1_materialbewegung`.GUID = '{tracker_id}'
                        """
        data = methods.st_mysqldb.get_data(self, query=sql)
        wa_matnr = None
        for index, row in data.iterrows():
            wa_matnr = row["WA_MATNR"]
        return wa_matnr

    def _sync_existing_tracker(self):
        # time = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        # domain = [
        #     ('|', ('last_sync_time', '<', time.strftime('%%m')), ('last_sync_time', '=', None)),
        # ]
        domain = [
            ('last_sync_time', '=', False),
        ]

        tracker = self.env['pu.tracker'].search(domain, offset=0, limit=30)
        for usage in tracker:
            pu_tracker.pu_tracker_sync(self, usage.tracker_id)

    def _sync_new_tracker(self, company_id):
        domain = [
            ('id', '=', company_id),
        ]
        company = self.env['res.company'].search(domain)
        last_sync_time = company.pu_last_sync_time
        new_last_sync_time = datetime.now()

        if not last_sync_time:
            last_sync_time = new_last_sync_time - timedelta(days=1)
        sql = f"""
                SELECT DISTINCT subscription.*
                FROM subscription INNER JOIN `usage` ON (subscription.deviceId = `usage`.`uniqueId`) 
                WHERE
                    (`usage`.`updatedAt` >= '{last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}' 
                    OR subscription.`updatedAt` >= '{last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}')
                """

        data = methods.pu_mysqldb.get_traccar_data(self, query=sql)

        for index, row in data.iterrows():
            tracker_id = row["deviceId"]

            pu_tracker.pu_tracker_sync(self, tracker_id, data)
            self._get_user_ids(tracker_id)
        company.update({
            'pu_last_sync_time': methods.pu_datetime.to_datetime_from_db(new_last_sync_time),
        })
        self.env.cr.commit()
        self._sync_tracker_with_missing_emails()

    def _sync_tracker_with_missing_emails(self):
        sql = (f"\n"
               f"                    select id, user_email, tracker_id from\n"
               f"                        pu_tracker \n"
               f"                    where user_email is null\n"
               f"                        and active_device = True\n"
               f"                        limit 30\n"
               )

        self.env.cr.execute(sql)
        data = self.env.cr.fetchall()

        for id_, user_email, tracker_id in data:
            pu_tracker.pu_tracker_sync(self, tracker_id)
            self._get_user_ids(tracker_id)

    def _sync_new_tracker_produced_initial(self, company_id):
        domain = [
            ('id', '=', company_id),
        ]
        company = self.env['res.company'].search(domain)
        last_sync_id = company.pu_last_sync_id_produced
        if not last_sync_id:
            last_sync_id = 0

        sql = f"""
                Select distinct
                        `1_materialbewegung`.ID,
                        `1_materialbewegung`.GUID,
                        `1_materialbewegung`.MATNR,
                        `1_materialbewegung`.WA_VBELN,
                        `1_materialbewegung`.WA_POSNR,
                        `1_materialbewegung`.WA_WERK,
                        `1_materialbewegung`.WA_MATNR,
                        `1_materialbewegung`.WA_MATNR_UEPOS,
                        `1_materialbewegung`.WA_ZEIT,
                        `1_materialbewegung`.KUNNR,
                        `1_materialbewegung`.KUNAG,
                        `1_materialbewegung`.TIMESTAMP
                From
                    `1_materialbewegung`
                Where
                    Length(`1_materialbewegung`.GUID) = 10
                    AND `1_materialbewegung`.GUID like '4710%'
                    AND `1_materialbewegung`.`ID` >= '{last_sync_id}'
                Order By
                    `1_materialbewegung`.ID
                    limit 50
                """

        data = methods.st_mysqldb.get_data(self, query=sql)
        for index, row in data.iterrows():
            type1 = type(row["GUID"])
            if type(row["GUID"]) == str:
                tracker_id = row["GUID"]
            else:
                tracker_id = str(row["GUID"].delta)
            company.update({
                'pu_last_sync_id_produced': row["ID"],
            })
            self.env.cr.commit()
            pu_tracker.pu_tracker_sync_produced(self, tracker_id, data)
            self.env.cr.commit()

    def _sync_new_tracker_produced(self, company_id):
        domain = [
            ('id', '=', company_id),
        ]
        company = self.env['res.company'].search(domain)
        last_sync_time = company.pu_last_sync_time_produced
        new_last_sync_time = datetime.now()
        if not last_sync_time:
            last_sync_time = new_last_sync_time - timedelta(days=1)

        sql = f"""
                Select distinct
                        `1_materialbewegung`.GUID,
                        `1_materialbewegung`.MATNR,
                        `1_materialbewegung`.WA_VBELN,
                        `1_materialbewegung`.WA_POSNR,
                        `1_materialbewegung`.WA_WERK,
                        `1_materialbewegung`.WA_MATNR,
                        `1_materialbewegung`.WA_MATNR_UEPOS,
                        `1_materialbewegung`.WA_ZEIT,
                        `1_materialbewegung`.KUNNR,
                        `1_materialbewegung`.KUNAG,
                        `1_materialbewegung`.TIMESTAMP
                From
                    `1_materialbewegung`
                Where
                    Length(`1_materialbewegung`.GUID) = 10
                    AND `1_materialbewegung`.GUID like '4710%'
                    AND `1_materialbewegung`.`TIMESTAMP` >= '{last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}'
                Order By
                    `1_materialbewegung`.TIMESTAMP
                    limit 2000
                """

        data = methods.st_mysqldb.get_data(self, query=sql)
        for index, row in data.iterrows():
            type1 = type(row["GUID"])
            if type(row["GUID"]) == str:
                tracker_id = row["GUID"]
            else:
                tracker_id = str(row["GUID"].delta)
            company.update({
                'pu_last_sync_time_produced': methods.pu_datetime.to_datetime_from_db(row["TIMESTAMP"]),
            })
            self.env.cr.commit()
            pu_tracker.pu_tracker_sync_produced(self, tracker_id, data)
            self.env.cr.commit()

    def pu_tracker_sync_produced(self, tracker_id, pd_data=None):
        kunnr = None
        # for rec in self:
        #     pass
        if tracker_id:
            if pd_data is not None:
                sql = f"""SELECT *
                        from pd_data where GUID={tracker_id};
                        """
                data = ps.sqldf(sql, locals())
            else:
                sql = f"""SELECT 
                        `1_materialbewegung`.MATNR,
                        `1_materialbewegung`.WA_VBELN,
                        `1_materialbewegung`.WA_POSNR,
                        `1_materialbewegung`.WA_WERK,
                        `1_materialbewegung`.WA_MATNR,
                        `1_materialbewegung`.WA_MATNR_UEPOS,
                        `1_materialbewegung`.WA_ZEIT,
                        `1_materialbewegung`.KUNNR,
                        `1_materialbewegung`.KUNAG 
                from `1_materialbewegung` where GUID={tracker_id};"""
                data = methods.st_mysqldb.get_data(self, query=sql)

            for index, row in data.iterrows():
                wa_vbeln = row["WA_VBELN"]
                wa_matnr = row["WA_MATNR_UEPOS"]
                wa_posnr = row.WA_POSNR
                vgbel = False
                sql = f"""
                    select MATNR, UEPOS, VGBEL from LIPS where 
                        VBELN = '{wa_vbeln}'
                        and POSNR = '{wa_posnr}'
                    """
                sap_data = addons_custom.stasto_base.methods.hdb_connection.get_data(self, query=sql)
                wa_uepos = False
                for sap_index, sap_row in sap_data.iterrows():
                    wa_uepos = sap_row.UEPOS
                    wa_matnr = sap_row.MATNR
                    vgbel = sap_row.VGBEL
                if wa_uepos or wa_uepos != "000000":
                    sql = f"""
                            select MATNR from LIPS where 
                                VBELN = '{wa_vbeln}'
                                and POSNR = '{wa_uepos}'
                            """
                    sap_data = addons_custom.stasto_base.methods.hdb_connection.get_data(self, query=sql)
                    for sap_index, sap_row in sap_data.iterrows():
                        wa_matnr = sap_row.MATNR
                if vgbel:
                    sql = f"""
                            select VKORG, KUNNR from VBAK where 
                                VBELN = '{vgbel}'
                            """
                    sap_data = addons_custom.stasto_base.methods.hdb_connection.get_data(self, query=sql)
                    for sap_index, sap_row in sap_data.iterrows():
                        kunnr = sap_row.KUNNR.lstrip("0")
                        vkorg = sap_row.VKORG

                matnr = row["MATNR"]
                trial_duration = 365
                setup_fee = False

                last_sync_time = None
                active = False
                customer = None
                iccid = None
                email = None
                activation_count = 0

                if wa_vbeln:
                    trial_duration = None
                    if "0030" in wa_matnr or "0-030" in wa_matnr:
                        setup_fee = False
                        trial_duration = "30"
                    elif "1030" in wa_matnr or "1-030" in wa_matnr:
                        setup_fee = True
                        trial_duration = "30"
                    else:
                        trial_duration = "365"
                        setup_fee = False

                    sql = f"SELECT deviceId from subscription where deviceId={tracker_id};"
                    data = methods.pu_mysqldb.get_traccar_data(self, query=sql)
                    if data.empty:
                        if setup_fee:
                            sql = f"""
                                    insert into subscription 
                                    (deviceId, trialDuration, createdAt, setupFee) 
                                        values 
                                    ({tracker_id}, '{trial_duration}', 
                                    '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}',
                                    '1');
                                    """
                        else:
                            sql = f"""
                                insert into subscription 
                                (deviceId, trialDuration, createdAt) 
                                    values 
                                ({tracker_id}, '{trial_duration}', 
                                '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}');
                                """
                        methods.pu_mysqldb.db_execute(self, query=sql)
                    else:
                        domain = [('tracker_id', '=', tracker_id), ]
                        found_tracker = self.env['pu.tracker'].search(domain)
                        if not found_tracker.sync_disabled:
                            if setup_fee:
                                sql = f"""
                                         update subscription
                                            set setupFee='1',
                                            updatedAt = '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'
                                         where
                                            deviceId='{tracker_id}'
                                        """
                            else:
                                sql = f"""
                                         update subscription
                                            set setupFee=Null,
                                            updatedAt = '{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}'
                                         where
                                            deviceId='{tracker_id}'
                                        """
                            methods.pu_mysqldb.db_execute(self, query=sql)
                        else:
                            setup_fee = found_tracker["setup_fee"]
                            trial_duration = found_tracker["trial_duration"]

                    customer = pu_tracker.get_old_customer(self, tracker_id)
                    rec = {
                        'tracker_id': tracker_id,
                        'trial_duration': trial_duration,
                        'customer': customer,
                        'customer_id_ext': kunnr,
                        'user_email': email,
                        'setup_fee': setup_fee,
                        'shipment_id_ext': wa_vbeln,
                        'material_nr': wa_matnr,
                        'last_sync_time': datetime.now(),
                        'time_updated': methods.pu_datetime.to_datetime_from_db(row["WA_ZEIT"]),
                        'delivered_at': methods.pu_datetime.to_datetime_from_db(row["WA_ZEIT"]),
                    }
                    domain = [
                        ('tracker_id', '=', tracker_id)
                    ]
                    tracker = self.env['pu.tracker'].search(domain)
                    if tracker:
                        tracker.update(rec)
                    else:
                        tracker = self.env['pu.tracker'].create(rec)
                    self.env.cr.commit()
                else:
                    if matnr:
                        customer = pu_tracker.get_old_customer(self, tracker_id)
                        rec = {
                            'material_nr': matnr,
                            'customer': customer,
                            'shipment_id_ext': wa_vbeln,
                        }
                        domain = [
                            ('tracker_id', '=', tracker_id)
                        ]
                        tracker = self.env['pu.tracker'].search(domain)
                        if tracker:
                            tracker.update(rec)
                            self.env.cr.commit()

                # domain = [
                #    ('name', '=', tracker_id)
                # ]
                # lot = self.env['stock.production.lot'].search(domain)
                # if lot:
                #    pass
                # else:
                #    rec = {
                #        'name': tracker_id,
                #        'company_id': company_id,
                #    }
                #    # lot = self.env['stock.production.lot'].create(rec)

        return self

    def _get_user_ids(self, tracker_id=False):
        if not tracker_id:
            sql = (f"\n"
                   f"                    select id, user_email from\n"
                   f"                        pu_tracker \n"
                   f"                    where not user_email is null\n"
                   f"                        and user_partner_id is null\n"
                   f"                        limit 500\n"
                   # f"                        and id = '15536'\n"
                   )
        else:
            sql = (f"\n"
                   f"                    select id, user_email from\n"
                   f"                        pu_tracker \n"
                   f"                    where tracker_id = '{tracker_id}'\n"
                   )

        self.env.cr.execute(sql)
        data = self.env.cr.fetchall()
        for id_, user_email in data:
            if not user_email or user_email == "":
                domain = [
                    ('id', '=', id_)
                ]
                tracker = self.env['pu.tracker'].search(domain)
                vals = {
                    'user_partner_id': None
                }
                tracker.update(vals)
                self.env.cr.commit()
                break

            domain = [
                ('email', '=', user_email),
            ]
            users = self.env['res.partner'].search(domain)
            if len(users) == 1:
                for user in users:
                    found_user = user
                    if len(user.parent_id) > 0:
                        found_parent = True
                        found_user = user
                        users_parent = self.env['res.partner'].search([('id', '=', found_user.parent_id[0].id), ])
                        if len(users_parent) > 0:
                            if users_parent[0].name == found_user.name:
                                user_vals = {
                                    'parent_id': False,
                                    'company_type': 'person',
                                }
                                found_user.update(user_vals)
                                self.env.cr.commit()
                                person_archive = {
                                    'active': False,
                                    'email': "",
                                    'phone': "",
                                    'mobile': "",
                                }
                                if not users_parent[0].user_ids:
                                    users_parent[0].write(person_archive)
                                    self.env.cr.commit()
            elif len(users) > 1:
                found_parent = False
                for user in users:
                    if len(user.parent_id) > 0:
                        found_parent = True
                        found_user = user
                        users_parent = self.env['res.partner'].search([('id', '=', found_user.parent_id[0].id), ])
                        if len(users_parent) > 0:
                            if users_parent[0].name == found_user.name:
                                user_vals = {
                                    'parent_id': False,
                                    'company_type': 'person',
                                }
                                found_user.update(user_vals)
                                self.env.cr.commit()
                                person_archive = {
                                    'active': False,
                                    'email': "",
                                    'phone': "",
                                    'mobile': "",
                                }
                                if not users_parent[0].user_ids:
                                    users_parent[0].write(person_archive)
                                    self.env.cr.commit()
                if not found_parent:
                    found_user = users[0]
            else:
                instr = user_email.find("@")
                if instr == -1:
                    user_name = user_email.replace(".", " ").title()
                else:
                    user_name = user_email[:instr].replace(".", " ").title()
                user_vals = {
                    'name': user_name,
                    'email': user_email,
                    'company_type': 'person',
                }
                found_user = self.env['res.partner'].create(user_vals)
                self.env.cr.commit()

            domain = [
                ('id', '=', id_)
            ]
            tracker = self.env['pu.tracker'].search(domain)
            vals = {
                'user_partner_id': found_user.id
            }
            tracker.update(vals)
            self.env.cr.commit()
