from odoo import fields,models,api
from odoo.exceptions import ValidationError

class Product(models.Model):
    _name = 'wsc.product'
    _description = 'Warehouse Product'

    name = fields.Char(string='Product',required=True)
    default_code = fields.Char(string='Default Code')
    description = fields.Text(string='Description')
    category = fields.Selection([
        ('electronics','Electronics'),
        ('furniture','Furniture'),
        ('accessories','Accessories'),
        ('others','Others'),
    ])
    unit_price = fields.Float(string='Unit Price')
    cost_price = fields.Float(string='Cost Price')
    active = fields.Boolean(string='Active', default=True)
    minimum_stock = fields.Float(string='Minimum Stock')
    stock_quant_ids = fields.One2many(
        'wsc.stock.quant','product_id',string='Stock Quants')
    total_quantity = fields.Float(
        string='Total Quantity',
        compute='_compute_total_quantity',store=True)
    is_low_stock = fields.Boolean(
        string='Is Low Stock',
        compute='_compute_is_low_stock',
        store=True)

    _sql_constraints = [
        ('unique_code','UNIQUE(default_code)','Code Should be unique'),
    ]

    @api.depends('stock_quant_ids','stock_quant_ids.quantity')
    def _compute_total_quantity(self):
        for rec in self :
            rec.total_quantity = sum(
                rec.stock_quant_ids.mapped('quantity')
            )

    @api.depends('total_quantity', 'minimum_stock')
    def _compute_is_low_stock(self):
        for rec in self:
            rec.is_low_stock = (
                    rec.minimum_stock > 0
                    and rec.total_quantity <= rec.minimum_stock
            )

    @api.constrains('unit_price', 'cost_price', 'minimum_stock')
    def _check_product_values(self):
        for rec in self:
            if rec.unit_price < 0 or rec.cost_price < 0:
                raise ValidationError(
                    "Product prices cannot be negative."
                )

            if rec.minimum_stock < 0:
                raise ValidationError(
                    "Minimum stock cannot be negative."
                )

    @api.constrains('default_code')
    def _check_default_code(self):
        for rec in self:
            if rec.default_code and not rec.default_code.strip():
                raise ValidationError(
                    "Product code cannot contain only spaces."
                )




# if rec.total_quantity <= rec.minimum_stock :
#     rec.is_low_stock = True
# else:
#     rec.is_low_stock = False
#
