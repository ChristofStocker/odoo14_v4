# -*- coding: utf-8 -*-
{
    'name': "cbx_product_matchcode",

    'summary': """
        Add new field to products for searching with matchcode
        """,

    'description': """
        Long description of module's purpose
    """,

    'author': "STASTO Iternational KG",
    'website': "http://www.stasto.eu",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'product'],

    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
