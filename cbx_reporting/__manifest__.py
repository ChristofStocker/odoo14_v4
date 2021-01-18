# -*- coding: utf-8 -*-
{
    'name': "Cibex Reporting",

    'summary': "Analyse Sales and Purchasing, etc.",

    'description': """
        
    """,

    'author': "Cibex GmbH",
    'website': "http://cibex.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '13.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', ],
    'images': ['static/description/reporting.png'],

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/invoice.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
