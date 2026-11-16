{
    'name': "Helpdesk System",
    'author': "Abdo",
    'category': '',
    'version': '17.0.0.1.0',

    'depends': [
        'base',
    ],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',

        'data/ticket_sequence.xml',

        'views/ticket_views.xml',
        'views/team_views.xml',
        'views/tag_views.xml',
        'views/menu_views.xml',

    ],

    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}