# Copyright 2019 VentorTech OU
# License OPL-1.0 or later.

import requests

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PrintNodeAccount(models.Model):
    """ PrintNode Account entity
    """
    _name = 'printnode.account'
    _description = 'PrintNode Account'

    _rec_name = 'username'

    printnode_id = fields.Integer('Printnode ID')

    endpoint = fields.Char(
        string='Endpoint',
        required=True,
        readonly=True,
        default='https://api.printnode.com/'
    )

    username = fields.Char(
        string='API Key',
        required=True
    )

    password = fields.Char(
        string='Password',
        required=False
    )

    computer_ids = fields.One2many(
        'printnode.computer', 'account_id',
        string='Computers'
    )

    status = fields.Char(
        string='Status',
        compute='_get_account_status',
        store=True,
        readonly=True
    )

    alias = fields.Char(
        string='Alias'
    )

    _sql_constraints = [
        ('printnode_id', 'unique(printnode_id)', 'Account already exists.'),
        ('username', 'unique(username)', 'Username (token) must be unique.'),
    ]

    def _get_printnode_response(self, uri):
        """ Send request with basic authentication and API key
        """

        auth = requests.auth.HTTPBasicAuth(self.username, self.password or '')
        if self.endpoint.endswith('/'):
            self.endpoint = self.endpoint[:-1]

        try:
            resp = requests.get('{}/{}'.format(self.endpoint, uri), auth=auth)
            resp.raise_for_status()

            self.status = 'OK'
            return resp.json()

        except requests.exceptions.RequestException as e:
            self.env['printnode.printer'].search([]).write({
                'status': 'offline'
            })

            self.status = e  # or resp.json().get('message')
            return []

    @api.depends('endpoint', 'username', 'password')
    def _get_account_status(self):
        """ Request PrintNode account details - whoami
        """
        for rec in self.filtered(lambda x: x.endpoint and x.username):
            rec._get_printnode_response('whoami')

    def _get_node(self, node_type, node_id, parent_id):
        """ Parse and update PrintNode nodes (printer and computers)
        """
        node = self.env['printnode.{}'.format(node_type)].search([
            ('printnode_id', '=', node_id['id']),
            '|', ('active', '=', False), ('active', '=', True)
        ], limit=1)

        if not node:
            params = {
                'printnode_id': node_id['id'],
                'name': node_id['name'],
                'status': node_id['state'],
            }
            if node_type == 'computer':
                params.update({'account_id': parent_id})
            if node_type == 'printer':
                params.update({'computer_id': parent_id})

            node = node.create(params)
        else:
            node.write({
                'status': node_id['state'],
            })

        return node

    def import_printers(self):
        """ Re-import list of printers into OpenERP.
        """
        for printer in self._get_printnode_response('printers'):
            c = self._get_node('computer', printer['computer'], self.id)
            p = self._get_node('printer', printer, c.id)

    def recheck_printer(self, printer, print_sample_report=False):
        """ Re-check particular printer status
        """
        uri = 'printers/{}'.format(printer.printnode_id)

        resp = self._get_printnode_response(uri)
        printer.write({'status': resp
            and resp[0]['computer']['state'] == 'connected'
            and resp[0]['state']
            or 'offline'})

        return printer.online

    @api.model
    def create(self, vals):
        account = super(PrintNodeAccount, self).create(vals)
        account.import_printers()

        return account

    def unlink(self):
        for account in self:
            account.unlink_devices()
        return super(PrintNodeAccount, self).unlink()

    def unlink_devices(self):
        """ delete computers, printers, print jobs and user rules
        """

        for computer in self.computer_ids:
            for rule in self.env['printnode.rule'].search([
                ('printer_id', 'in', computer.printer_ids.ids),
            ]):
                rule.unlink()
            for printer in computer.printer_ids:
                for job in printer.printjob_ids:
                    job.unlink()
                printer.unlink()
            computer.unlink()
