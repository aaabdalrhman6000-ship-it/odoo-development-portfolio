{
    'name': "Repair Shop",
    'author': "Abdo",
    'category': '',
    'version': '17.0.0.1.0',

    'depends': [
        'base',
    ],

    'data': [

        'security/repair_shop_groups.xml',
        'security/ir.model.access.csv',
        'security/repair_shop_rules.xml',


        'data/repair_order_sequence.xml',

        'views/repair_customer_views.xml',
        'views/repair_vehicle_views.xml',
        'views/repair_mechanic_views.xml',
        'views/repair_service_views.xml',
        'views/repair_order_views.xml',
        'views/repair_part_views.xml',
        'views/repair_order_line_view.xml',

        'views/base_menu.xml',
    ],

    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}