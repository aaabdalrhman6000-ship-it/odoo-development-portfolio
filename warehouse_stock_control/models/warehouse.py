from odoo import fields, models,api
from odoo.exceptions import ValidationError

class WarehouseStockControl(models.Model):
    _name = 'wsc.warehouse'
    _description = 'Warehouse Stock Control'

    name = fields.Char(string='Warehouse Name', required=True)

    code = fields.Char(string='Warehouse Code', required=True)

    manager_id = fields.Many2one(
        'res.users',
        string='Warehouse Manager',
        ondelete='restrict',
    )

    location_ids = fields.One2many(
        'wsc.location',
        'warehouse_id',
        string='Locations',
    )

    stock_location_id = fields.Many2one(
        'wsc.location',
        string='Main Stock Location',
        ondelete='restrict',
    )
    address = fields.Char()
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('unique_code','UNIQUE(code)','Code should be unique')
    ]

    @api.constrains('stock_location_id')
    def _check_stock_location(self):
        for rec in self:
            if rec.stock_location_id:
                if rec.stock_location_id.warehouse_id != rec:
                    raise ValidationError(
                        "The main stock location must belong to this warehouse."
                    )

                if rec.stock_location_id.location_type != 'internal':
                    raise ValidationError(
                        "The main stock location must be an internal location."
                    )

    @api.constrains('code')
    def _check_code(self):
        for rec in self:
            if not rec.code or not rec.code.strip():
                raise ValidationError(
                    "Warehouse code cannot be empty."
                )