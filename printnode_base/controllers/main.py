# Copyright 2019 VentorTech OU
# License OPL-1.0 or later.

import json
from copy import deepcopy

from odoo.addons.web.controllers.main import DataSet, ReportController

from odoo.http import request
from odoo.http import serialize_exception as _serialize_exception
from odoo.tools import html_escape
from odoo.tools.translate import _
from odoo import http, api
from werkzeug.exceptions import ImATeapot

SECURITY_GROUP = 'printnode_base.printnode_security_group_user'
PDF = ['qweb-pdf']
RAW = ['qweb-text']


# we use this dummy exception to clearly differentiate
# printnode exception in ajax response for downloading report
class PrintNodeSuccess(ImATeapot):
    pass


class ControllerProxy(http.Controller):

    def printnode_print(self, printer_id, report_id, objects, copies=1):
        """ PrintNode
        """
        return printer_id.printnode_print(report_id, objects, copies=copies)


class DataSetProxy(DataSet, ControllerProxy):

    def _execute_printnode_jobs(self, action_ids, action_object_ids):
        for action in request.env['printnode.action.button'].browse(action_ids):
            objects = action._get_model_objects(action_object_ids)
            if not objects:
                continue
            printer = action._get_action_printer()
            super(DataSetProxy, self).printnode_print(
                printer, action.report_id, objects,
                copies=action.number_of_copies)

    def _call_kw(self, model, method, args, kwargs):
        user = request.env.user
        if not user.has_group(SECURITY_GROUP) \
                or not user.company_id.printnode_enabled or not user.printnode_enabled:
            return super(DataSetProxy, self)._call_kw(model, method, args, kwargs)

        # We have a list of methods which will never be handled in 'printnode.action.button'.
        # In that case just will be returned a 'super method'.
        su = request.env['ir.config_parameter'].sudo()
        methods_list = su.get_param('printnode_base.skip_methods', '').split(',')
        # In addition, we need to choose only 'call_kw_multi' sub method, so
        # let's filter this like in standard Odoo function 'def call_kw()'.
        method_ = getattr(type(request.env[model]), method)
        api_ = getattr(method, '_api', None)
        if (method in methods_list) or (api_ in ('model', 'model_create')):
            return super(DataSetProxy, self)._call_kw(model, method, args, kwargs)

        actions = request.env['printnode.action.button'].search([
            ('model_id.model', '=', model),
            ('method_id.method', '=', method),
        ])
        post_ids, pre_ids = [], []

        for action in actions.filtered(lambda a: a.active and a.report_id):
            (post_ids, pre_ids)[action.preprint].append(action.id)

        printnode_object_ids = args[0] if args else None

        self._execute_printnode_jobs(pre_ids, printnode_object_ids)

        # We need to update variables 'post_ids' and 'printnode_object_id' from context.
        args_, kwargs_ = deepcopy(args[1:]), deepcopy(kwargs)
        context_, *_rest = api.split_context(method_, args_, kwargs_)
        if isinstance(context_, dict):
            post_ids += context_.get('printnode_action_ids', [])
            object_ids_from_kwargs = context_.get('printnode_object_ids')
            printnode_object_ids = object_ids_from_kwargs or printnode_object_ids

        result = super(DataSetProxy, self)._call_kw(model, method, args, kwargs)

        # If we had gotten 'result' as another one wizard or something - we need to save our
        # variables 'printnode_action_ids' and 'printnode_object_ids' in context and do printing
        # after the required 'super method' will be performed.
        if post_ids and result and isinstance(result, dict) and 'context' in result:
            new_context = dict(result.get('context'))
            if not new_context.get('printnode_action_ids'):
                new_context.update({'printnode_action_ids': post_ids})
            if not new_context.get('printnode_object_ids'):
                new_context.update({'printnode_object_ids': printnode_object_ids})
            result['context'] = new_context
            return result

        if not post_ids:
            return result

        self._execute_printnode_jobs(post_ids, printnode_object_ids)

        return result


class ReportControllerProxy(ReportController, ControllerProxy):

    @http.route('/report/download', type='http', auth="user")
    def report_download(self, data, token, context=None):
        """ print reports on report_download
        """
        user = request.env.user
        if not user.has_group(SECURITY_GROUP) \
                or not user.company_id.printnode_enabled or not user.printnode_enabled:
            return super(ReportControllerProxy, self).report_download(data, token, context)

        requestcontent = json.loads(data)

        if requestcontent[1] not in PDF + RAW:
            return super(ReportControllerProxy, self).report_download(data, token, context)

        ext = requestcontent[1].split('-')[1]
        report_name, object_ids = requestcontent[0].\
            split('/report/{}/'.format(ext))[1].split('?')[0].split('/')

        report_id = request.env['ir.actions.report']._get_report_from_name(report_name)
        printer_id = user._get_report_printer(report_id.id)

        if not printer_id:
            return super(ReportControllerProxy, self).report_download(data, token, context)

        try:
            ids = [int(x) for x in object_ids.split(',')]
            obj = request.env[report_id.model].browse(ids)

            super(ReportControllerProxy, self).printnode_print(printer_id, report_id, obj)

        except Exception as e:
            return request.make_response(html_escape(json.dumps({
                'code': 200,
                'message': 'Odoo Server Error',
                'data': _serialize_exception(e),
            })))

        index = user.company_id.im_a_teapot
        raise PrintNodeSuccess(['', _('Sent to PrintNode')][index])
