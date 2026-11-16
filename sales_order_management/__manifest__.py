{
    'name': "Sales Order Management",
    'author': "Abdo",
    'category': 'Sales',
    'version': '17.0.0.1.0',

    'depends': [
        'base',
        'mail',
        'product',
        'account',
    ],

    'data': [

        'security/security.xml',
        'security/ir.model.access.csv',

        'data/sequence.xml',
        'data/som_cron.xml',

        'views/som_order_views.xml',
        'views/som_order_line_views.xml',
        'views/som_order_tag_views.xml',
        'views/base_menus.xml',

        'wizard/som_order_cancel_wizard_views.xml',

        'report/report.xml',



    ],

    'demo':[
        'demo/som_demo.xml',
    ],

    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}