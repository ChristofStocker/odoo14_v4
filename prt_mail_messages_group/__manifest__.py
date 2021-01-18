# -*- coding: utf-8 -*-
{
    'name': 'Mail Messages Group.'
            ' Special Group for "Messages" menu',
    'version': '11.0.1.0',
    'summary': """Optional extension for free 'Mail Messages Easy' app""",
    'author': 'Ivan Sokolov, Cetmix',
    'category': 'Discuss',
    'license': 'LGPL-3',
    'website': 'https://cetmix.com',
    'description': """
Limit access to "Messages" menu. Adds special Group for "Messages" menu
""",
    'depends': ['prt_mail_messages'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/groups.xml',
        'views/prt_mail_group.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False
}
