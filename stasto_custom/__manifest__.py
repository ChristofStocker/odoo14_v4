# -*- coding: utf-8 -*-
{
    'name': "stasto_custom",

    'summary': """
        STASTO specific changes in Odoo-Enterprise
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
    'depends': ['base', 'product', 'sale'],

    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/res_company.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
