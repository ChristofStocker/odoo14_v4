# -*- coding: utf-8 -*-
# from odoo import http


# class StastoMigration(http.Controller):
#     @http.route('/stasto_migration/stasto_migration/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/stasto_migration/stasto_migration/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('stasto_migration.listing', {
#             'root': '/stasto_migration/stasto_migration',
#             'objects': http.request.env['stasto_migration.stasto_migration'].search([]),
#         })

#     @http.route('/stasto_migration/stasto_migration/objects/<model("stasto_migration.stasto_migration"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('stasto_migration.object', {
#             'object': obj
#         })
