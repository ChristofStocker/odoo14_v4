from odoo import fields, models
from datetime import datetime
from datetime import timedelta
from .. import methods
import addons_custom.stasto_base


class ResPartner(models.Model):
    _inherit = 'res.partner'

    notes = fields.Html('Notes')

    def _sync_crm_partner_initial(self, company_id, kundensegment='%'):
        contact_id = False
        domain = [('id', '=', company_id), ]
        company = self.env['res.company'].search(domain)
        sales_org = company.sales_org_id

        last_sync_id = company.stasto_crm_last_initial_sync_id
        # last_sync_id = 0
        if not last_sync_id:
            last_sync_id = 0
        sql = (f"\n"
               f"            select ID from `crm_kontakte` \n"
               f"                where VKORG='{sales_org}'\n"
               f"                    and (LOESCHKZ='' or isnull(LOESCHKZ))\n"
               f"                    and (TYP = 'KUNDE' or TYP = 'LIEFERADRESSE')\n"
               f"                    and KUNDENSEGMENT like '{kundensegment}'\n"
               f"                    and ID >= {str(last_sync_id)}\n"
               # f"                    and ID >= '197979'\n"               
               f"                order by ID\n"
               f"                limit 150\n"
               f"            ")
        data = addons_custom.stasto_base.methods.st_mysqldb.get_data(self, query=sql)
        for index, row in data.iterrows():
            contact_id = row["ID"]
            company.update({
                'stasto_crm_last_initial_sync_id': contact_id,
            })
            self.env.cr.commit()
            self.sync_crm_partner(row["ID"], company_id)

        company.update({
            'stasto_crm_last_initial_sync_id': contact_id,
        })
        self.env.cr.commit()

    def _sync_crm_partner_updated(self, company_id, kundensegment='%'):
        domain = [('id', '=', company_id), ]
        company = self.env['res.company'].search(domain)
        sales_org = company.sales_org_id

        last_sync_time = company.stasto_crm_last_sync_time_partner_updated
        new_last_sync_time = datetime.now()
        if not last_sync_time:
            last_sync_time = new_last_sync_time - timedelta(days=1)
        sql = (f"\n"
               f"            select ID from `crm_kontakte` \n"
               f"                where VKORG='{sales_org}'\n"
               f"                    and (LOESCHKZ='' or isnull(LOESCHKZ))\n"
               f"                    and (TYP = 'KUNDE' or TYP = 'LIEFERADRESSE')\n"
               f"                    and KUNDENSEGMENT = '{kundensegment}'\n"
               f"                    and TIMESTAMP >= '{last_sync_time.strftime('%Y-%m-%d %H:%M:%S')}'\n"
               f"                order by ID\n"
               f"            ")
        data = addons_custom.stasto_base.methods.st_mysqldb.get_data(self, query=sql)
        for index, row in data.iterrows():
            self.sync_crm_partner(row["ID"], company_id)

        company.update({
            'stasto_crm_last_sync_time_partner_updated': methods.pu_datetime.to_datetime_from_db(new_last_sync_time),
        })

    def sync_crm_partner(self, contact_id, company_id):
        if company_id == 2:
            website_id = self.env['website'] \
                .search([('name', 'ilike', 'PowUnity')])["id"]
            carrier_id = self.env['delivery.carrier'] \
                .search([('name', 'ilike', 'UPS Standard PowUnity')])["id"]
        else:
            website_id = self.env['website'] \
                .search([('name', '=', 'STASTO Automation')])["id"]

        domain = [('id', '=', company_id), ]
        company = self.env['res.company'].search(domain)
        sales_org = company.sales_org_id

        sql = (f"\n"
               f"            select * from `crm_kontakte` \n"
               f"                where ID='{contact_id}'\n"
               f"            ")
        data = addons_custom.stasto_base.methods.st_mysqldb.get_data(self, query=sql)
        for index, row in data.iterrows():
            partner_name = row["BEZEICHNUNG"] or ""
            tag = row["KUNDENSEGMENT"]
            company_type = "person"
            typ = row["TYP"]
            website_published = False
            grade_id = False
            email, phone, mobile = False, False, False
            if typ == "KUNDE" or typ == "LIEFERADRESSE":
                company_type = "company"
            # Pricelist:
            if tag == "PU_Fachhändler":
                company_type = "company"
                pricelist_id = self.env['product.pricelist'] \
                    .search(['&',
                             ('name', '=', 'PU Fachhändler'),
                             ('company_id', '=', company_id)
                             ])["id"]
                grade_id = 3

                turnover_time = datetime.now() - timedelta(days=730)
                sql = f"""
                    select sum(price_unit_net) as sum_result from cbx_invoice where customer_id_ext = '{row["TYPID"]}'
                        and invoice_date >= '{turnover_time.strftime('%Y-%m-%d %H:%M:%S')}'
                        and invoice_type_ext <> 'F5'
                """
                self.env.cr.execute(sql)
                result = self.env.cr.fetchall()
                for sum_result in result:
                    if sum_result[0]:
                        if sum_result[0] > 100:
                            website_published = True
            elif tag == "PU_Flottenkunde":
                company_type = "company"
                pricelist_id = self.env['product.pricelist'] \
                    .search(['&',
                             ('name', '=', 'PU Flotte'),
                             ('company_id', '=', company_id)
                             ])["id"]
            elif tag == "PU_Hersteller":
                company_type = "company"
                pricelist_id = self.env['product.pricelist'] \
                    .search(['&',
                             ('name', '=', 'PU Hersteller'),
                             ('company_id', '=', company_id)
                             ])["id"]
            elif tag == "PU_Endkunde":
                pricelist_id = self.env['product.pricelist'] \
                    .search(['&',
                             ('name', '=', 'PU Privat'),
                             ('company_id', '=', company_id)
                             ])["id"]
            elif tag == "PU_Endkunde-DE":
                pricelist_id = self.env['product.pricelist'] \
                    .search(['&',
                             ('name', '=', 'PU Privat'),
                             ('company_id', '=', company_id)
                             ])["id"]
            elif tag == "PU_Zwischenhändler":
                company_type = "company"
                pricelist_id = self.env['product.pricelist'] \
                    .search(['&',
                             ('name', '=', 'PU Zwischenhändler'),
                             ('company_id', '=', company_id)
                             ])["id"]

            # check if person
            if not row["UID"]:
                sql = f"""
                                Select
                                    crm_kontakte_verknuepfung.POSITION,
                                    crm_kontakte_verknuepfung.ID1,
                                    crm_kontakte_verknuepfung.ID2,
                                    crm_kontakte2.*
                                From
                                    crm_kontakte2 Inner Join
                                    crm_kontakte_verknuepfung On crm_kontakte_verknuepfung.ID2 = crm_kontakte2.ID
                                Where
                                    crm_kontakte_verknuepfung.ID1 = '{row["ID"]}' And
                                    (crm_kontakte2.LOESCHKZ Is Null Or
                                        crm_kontakte2.LOESCHKZ = '')
                                """
                data2 = addons_custom.stasto_base.methods.st_mysqldb.get_data(self, query=sql)
                for index2, row2 in data2.iterrows():
                    person_name = (((str(row2["VORNAME1"]).strip() + " " + str(row2["VORNAME2"])).strip() +
                                    str(row2["NACHNAME"]))).replace("None", "").strip()
                    if person_name == partner_name:
                        company_type = "person"
                        email, phone, mobile = self.get_communication_data(row2["ID1"], row2["ID2"])

            country_id = self.env['res.country'].search([('code', '=', row["LANDISO"])])["id"]
            sprache = str(row["SPRACHE_ISO"] or "")

            # category_id, Tags:
            category_id = self.env['res.partner.category'].search([('name', '=', tag)])["id"]
            if not category_id and tag:
                new_category = {
                    'name': tag,
                }
                category = self.env['res.partner.category'].create(new_category)
                self.env.cr.commit()
                category_id = category["id"]
            # Street:
            street = str(row["STRASSE1"] or "") + " " + str(row["STRASSE2"] or "") + " " + str(row["STRASSE3"] or "")
            street = street.strip()

            new_partner = {
                'company_type': company_type,
                'name': partner_name,
                'zip': row["POSTLEITZAHL"] or "",
                'street': street,
                'city': row["ORT"] or "",
                'country_id': country_id,
                'company_id': company_id,
                'lang': self.env['res.lang'].search([('iso_code', '=', sprache.lower())])["code"],
                'notes': row["NOTIZEN"] or "",
                # 'vat': "",
                'ref': row["ID"] or "",
                'customer_id': row["TYPID"] or "",
                'website_id': website_id or "",
                'website': row["HOMEPAGE1"] or "",
            }
            if pricelist_id:
                new_partner['property_product_pricelist'] = pricelist_id or ""
            if carrier_id:
                new_partner['property_delivery_carrier_id'] = carrier_id or ""
            if category_id:
                new_partner['category_id'] = [category_id]
            if grade_id:
                new_partner['grade_id'] = grade_id
            if tag == "PU_Fachhändler":
                new_partner['website_published'] = website_published
            if email:
                new_partner['email'] = email
            if phone:
                new_partner['phone'] = phone
            if mobile:
                new_partner['mobile'] = mobile

            domain = ['&', ('zip', '=', row["POSTLEITZAHL"]),
                      ('company_id', '=', company_id),
                      ('active', '=', True),
                      ('country_id', '=', country_id),
                      ('name', 'ilike', partner_name), ]
            if row["STRASSE1"]:
                street_split = row["STRASSE1"].split(" ")
                if len(street_split) > 1:
                    domain.append('|', )
                for key in range(len(street_split)):
                    domain.append(('street', 'ilike', street_split[key]))

            partners = self.search(domain)
            if partners:

                if len(partners) == 1:
                    new_partner['category_id'].extend(partners.category_id.ids)
                    try:
                        partners.write(new_partner)
                        self.env.cr.commit()
                    except:
                        pass
                else:
                    tickets = False
                    for partner in partners:
                        if partner:
                            if partner.ticket_count:
                                if partner.ticket_count > 0:
                                    tickets = True
                    if tickets:
                        for partner in partners:
                            if partner:
                                if not partner.ticket_count:
                                    if not partner.user_ids:
                                        partner.write({'active': False, })
                                        self.env.cr.commit()
                    else:
                        skip_first = True
                        for partner in partners:
                            if partner:
                                if skip_first and partner.child_ids:
                                    skip_first = False
                                else:
                                    if not partner.user_ids:
                                        partner.write({'active': False, })
                                        self.env.cr.commit()

                    partners = self.search(domain)
                    if len(partners) == 1:
                        try:
                            new_partner['category_id'].extend(partners.category_id.ids)
                            partners.write(new_partner)
                            self.env.cr.commit()
                        except:
                            pass
            else:  # create new Partner
                try:
                    partners = self.env['res.partner'].create(new_partner)
                    self.env.cr.commit()
                except:
                    pass

                if row["UIDGEPRUEFT"]:
                    new_partner = {
                        'vat': row["UID"] or "",
                    }
                    try:
                        partners.write(new_partner)
                        self.env.cr.commit()
                    except:
                        pass
            if company_type == "company":
                for partner in partners:
                    self.sync_crm_partner_person(partner, company_id)

        return True

    def sync_crm_partner_person(self, partner, company_id):
        sql = f"""
                Select
                    crm_kontakte_verknuepfung.POSITION,
                    crm_kontakte_verknuepfung.ID1,
                    crm_kontakte_verknuepfung.ID2,
                    crm_kontakte2.*
                From
                    crm_kontakte2 Inner Join
                    crm_kontakte_verknuepfung On crm_kontakte_verknuepfung.ID2 = crm_kontakte2.ID
                Where
                    crm_kontakte_verknuepfung.ID1 = '{partner.ref}' And
                    (crm_kontakte2.LOESCHKZ Is Null Or
                        crm_kontakte2.LOESCHKZ = '')
                """
        data = addons_custom.stasto_base.methods.st_mysqldb.get_data(self, query=sql)
        for index, row in data.iterrows():
            email, phone, mobile = self.get_communication_data(False, row["ID2"])

            name = (((str(row["VORNAME1"]).strip() + " " + str(row["VORNAME2"])).strip() +
                     str(row["NACHNAME"]))).replace("None", "").strip()

            # check, if email already exists
            email_exist = False
            found_person = False
            persons = False
            if email:
                domain = ['&', ('company_id', '=', company_id),
                          ('email', '=', email),
                          ('active', '=', True),
                          ]
                persons = self.search(domain)
                if len(persons) > 0:
                    email_exist = True

            person_source = {
                'company_id': company_id or "",
                'ref': str(row["ID2"]) or "",
                'name': name or "",
                'phone': phone or "",
                'mobile': mobile or "",
                'function': row["POSITION"] or "",
                'company_type': 'person',
            }
            if not email_exist:
                person_source['email'] = email

            if persons:
                if len(persons) > 0:
                    if len(persons) == 1:
                        for person in persons:
                            if not person.parent_id:
                                person.write(person_source)
                                self.env.cr.commit()
                                found_person = person
                            else:
                                if person.parent_id.id == partner.id:
                                    if len(name) > 0:
                                        person.write(person_source)
                                        self.env.cr.commit()
                    else:
                        skip_first = True
                        for person in persons:
                            if person:
                                if skip_first and person.parent_id:
                                    skip_first = False
                                    person.write(person_source)
                                    self.env.cr.commit()
                                    found_person = person
                                else:
                                    person_archive = {
                                        'active': False,
                                        'email': "",
                                        'phone': "",
                                        'mobile': "",
                                    }
                                    if not person.user_ids:
                                        person.write(person_archive)
                                        self.env.cr.commit()

            else:
                domain = ['&', ('company_id', '=', company_id),
                          ('is_company', '=', False),
                          ('active', '=', True),
                          ('parent_id', '=', False),
                          ]

                if len(name) > 0 and len(partner.child_ids) > 0:
                    name_split = name.split(" ")
                    counter = 0
                    for key in range(len(name_split)):
                        counter += 1
                        if len(name_split) != counter:
                            domain.append('|', )
                        domain.append(('name', 'ilike', name_split[key]))
                    counter = 0
                    for child_id in partner.child_ids:
                        counter += 1
                        if len(partner.child_ids) != counter:
                            domain.append('|', )
                        domain.append(('id', '=', child_id.id))

                    persons = self.search(domain)

                    if len(persons) == 1:
                        persons.write(person_source)
                        self.env.cr.commit()
                        found_person = persons[0]
                    else:
                        skip_first = True
                        for person in persons:
                            if person:
                                if skip_first:
                                    skip_first = False
                                    person.write(person_source)
                                    self.env.cr.commit()
                                    found_person = person
                                else:
                                    person_archive = {
                                        'active': False,
                                        'email': "",
                                        'phone': "",
                                        'mobile': "",
                                    }
                                    if not person.user_ids:
                                        person.write(person_archive)
                                        self.env.cr.commit()

                if not found_person:
                    if len(name) > 0:
                        domain = ['&', ('company_id', '=', company_id),
                                  ('is_company', '=', False),
                                  ('active', '=', True),
                                  ]

                        name_split = name.split(" ")
                        if len(name_split) > 1:
                            domain.append('|', )
                        for key in range(len(name_split)):
                            domain.append(('name', 'ilike', name_split[key]))
                        persons = self.search(domain)
                        for person in persons:
                            if person.parent_id:
                                pass
                            else:
                                found_person = person
                if not found_person:
                    if email:
                        domain = ['&', ('company_id', '=', company_id),
                                  ('is_company', '=', False),
                                  ('active', '=', True),
                                  ('email', '=', email),
                                  ]
                        persons = self.search(domain)
                        for person in persons:
                            if person.parent_id:
                                pass
                            else:
                                found_person = person

                if not found_person:
                    if person_source['name'] != "" or email:
                        try:
                            found_person = self.env['res.partner'].create(person_source)
                            self.env.cr.commit()
                        except:
                            pass
            if found_person:
                if not found_person.parent_id:
                    person_source['parent_id'] = partner.id
                    try:
                        found_person.write(person_source)
                        self.env.cr.commit()
                    except:
                        pass
        return True

    def delete_phone_ids_inactive_partners(self, company_id):
        domain = ['&', ('company_id', '=', company_id),
                  # ('company_type', '=', 'person'),
                  ('active', '=', False),
                  ('|'),
                  ('email', '!=', False),
                  ('|'),
                  ('phone', '!=', False),
                  ('mobile', '!=', False),
                  ]
        persons = self.search(domain)
        for person in persons:
            person_archive = {
                'active': False,
                'email': '',
                'phone': '',
                'mobile': '',
                # 'phone_number_ids': [],
            }
            try:
                if not person.user_ids:
                    res = person.write(person_archive)
            except:
                pass
            self.env.cr.commit()
        self.archive_duplicate_emails(company_id)
        return True

    def archive_duplicate_emails(self, company_id):
        sql = f"""
            select COUNT(ID) as count, email from res_partner
            where 
                not email is null
                and company_id = {company_id}
                and user_id is null
            group by email
            having COUNT(ID) > 1;
            """
        self.env.cr.execute(sql)
        result = self.env.cr.fetchall()
        for count, email in result:
            ticket = False
            domain = ['&', ('company_id', '=', company_id),
                      ('is_company', '=', True),
                      ('email', '=', f'{email}'),
                      ('user_id', '=', False),
                      ]
            partners = self.search(domain)

            if partners:
                if len(partners) < count:
                    for partner in partners:
                        company = {
                            'active': False,
                            'email': '',
                            'phone': '',
                            'mobile': '',
                            # 'phone_number_ids': [],
                        }
                        if not partner.ticket_count and not partner.user_ids:
                            res = partner.write(company)
                            self.env.cr.commit()
                        else:
                            ticket = True
                else:
                    skip_first = True
                    for partner in partners:
                        if partner:
                            if skip_first:
                                skip_first = False
                            else:
                                company = {
                                    'active': False,
                                    'email': '',
                                    'phone': '',
                                    'mobile': '',
                                    # 'phone_number_ids': [],
                                }
                                if not partner.user_ids:
                                    partner.write(company)
                                    self.env.cr.commit()

            domain = ['&', ('company_id', '=', company_id),
                      ('is_company', '=', False),
                      ('email', '=', f'{email}'),
                      ('user_id', '=', False),
                      ]
            persons = self.search(domain)
            if persons:
                skip_first = True
                for person in persons:
                    if person.ticket_count:
                        ticket = True
                if ticket:
                    skip_first = False
                for person in persons:
                    if person:
                        if skip_first:
                            skip_first = False
                        else:
                            company = {
                                'active': False,
                                'email': '',
                                'phone': '',
                                'mobile': '',
                                # 'phone_number_ids': [],
                            }
                            if not person.ticket_count and not person.user_ids:
                                res = person.write(company)
                                self.env.cr.commit()
        return True

    def get_communication_data(self, id1=False, id2=False):
        email = False
        phone = False
        mobile = False
        sql = False
        if not id1:
            sql = f"""
                            Select
                                *
                            From
                                crm_kommunikation
                            Where
                                crm_kommunikation.ID_KONTAKT2 = '{id2}' and 
                                (LOESCHKZ Is Null Or LOESCHKZ = '')
                        """
        else:
            sql = f"""
                                        Select
                                            *
                                        From
                                            crm_kommunikation
                                        Where
                                            crm_kommunikation.ID_KONTAKT2 = '{id2}' and 
                                            crm_kommunikation.ID_KONTAKT1 = '{id1}' and 
                                            (LOESCHKZ Is Null Or LOESCHKZ = '')
                                    """
        if sql:
            data2 = addons_custom.stasto_base.methods.st_mysqldb.get_data(self, query=sql)
            for index2, row2 in data2.iterrows():
                if row2["KOM_TYP"] == "EMAIL1":
                    email = row2["WERT1"]
                if row2["KOM_TYP"] == "TELEFON1":
                    phone = (((str(row2["WERT1"]).strip() + " " + str(row2["WERT2"])).strip() \
                              + " " + str(row2["WERT3"])).strip() + " " + str(row2["WERT4"])).replace("None",
                                                                                                      "").strip()
                if row2["KOM_TYP"] == "HANDY1":
                    mobile = (((str(row2["WERT1"]).strip() + " " + str(row2["WERT2"])).strip() \
                               + " " + str(row2["WERT3"])).strip() + " " + str(row2["WERT4"])).replace("None",
                                                                                                       "").strip()
        return email, phone, mobile

    def archive_persons_form_archived_companies(self):
        domain = [('active', '=', False), ]
        partners = self.search(domain)
        for partner in partners:
            for child in partner.child_ids:

                domain = [('id', '=', child.id), ]
                person = self.search(domain)
                person_source = {
                    'active': False,
                    'email': '',
                    'phone': '',
                    'mobile': '',
                    # 'phone_number_ids': [],
                }
                if not person.ticket_count and not person.user_ids:
                    res = person.write(person_source)
                    self.env.cr.commit()
