# -*- coding: utf-8 -*-
{
    "name": """Dual Color Backend Theme""",
    "summary": """Customisable dual color backend theme.""",
    "category": "Theme/Backend",
    "images": ['static/description/banner.png','static/description/theme_screenshot.png'],
    "version": "13.0.1.0",
    "description": """This theme will let you set dual color backend theme.
        * Set the colors through HTML color picker.
        * Set different colors for menubars and widgets.
    """,

    "author": "S&V",
    "license": "OPL-1",
    "website": "https://www.sandv.biz",
    "support": "odoo@sandv.biz",
    "price": 50.00,
    "currency": "EUR",
    "depends": [
        "web", 'base_setup','base'
    ],
    "data": [
        "template/assets.xml",
        'view/res_config_settings_view.xml'
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
    "application": False,
}
