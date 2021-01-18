# Part of Softhealer Technologies.
{
    "name": "Global Search",

    "author": "Softhealer Technologies",

    "website": "https://www.softhealer.com",

    "version": "14.0.1",
    
    "license": "OPL-1",

    "support": "support@softhealer.com",

    "category": "Extra Tools",

    "summary": "Configurable Global Search, Easy Object Search, Quick Object Find Module, Fast Object Find App, Get Object Using Attributes,Overall Odoo Object Search, Global Model Search Odoo",

    "description": """
A global search used to search any object based on the configuration. You can search all object's data easily. You can also configure one to many fields. The "Global Search" is visible to all odoo users. The search box is available at the top of the menu. Search results on click redirect to that record on the new tab. You can easily perform a search on multi-company objects also we have beautifully show company name before so you can see search results related to that company, we have show object (model) nicely whenever you have search query found in multiple objects, you can very easily see the difference of different objects. It also takes care of access rights of users, if a user doesn't have any object access than it will not show that record in search results. if the user has multi-company enabled than it shows multi-company results. We have made this looks fully configurable you can easily configure what is an important object(model) and related fields of that object(model), We have made security groups for this configurations so only who have right that user only can configure this global search objects and fields, All internal users can use this global search feature. Cheers!""",

    "depends": ['base_setup', 'web'],

    "data": [
        "template/assets.xml",
        "security/base_security.xml",
        "security/ir.model.access.csv",
        "views/global_search_view.xml",
    ],
    "qweb": [
        "static/src/xml/*.xml",
    ],

    "images": ["static/description/background.png", ],
    "live_test_url": "https://youtu.be/rbkWI9j0XN0",
    "installable": True,
    "auto_install": False,
    "application": True,
    "price": 40,
    "currency": "EUR"
}
