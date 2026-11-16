{
    'name': "Ware House Stock Control sys",
    'author': "Abdo",
    'category': 'Inventory',
    'version': '17.0.0.1.0',

    'description': """
    Warehouse Stock Control System
    
    Manage:
    - Products
    - Warehouses and locations
    - Stock quantities
    - Receipts and deliveries
    - Internal transfers
    - Inventory adjustments
    """,

    'depends': [
        'base',
    ],

    'data': [

        'security/security.xml',
        'security/ir.model.access.csv',

        'data/sequence.xml',

        'views/product_views.xml',
        'views/warehouse_views.xml',
        'views/location_views.xml',
        'views/stock_quant_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_move_views.xml',
        'views/stock_adjustment_views.xml',
        'views/base_menu.xml',

    ],

    'application': True,
    'installable': True,
    'license': 'LGPL-3',
}