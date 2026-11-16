from odoo import fields, models,api
from odoo.exceptions import ValidationError


class StockQuant(models.Model):
    _name = 'wsc.stock.quant'
    _description = 'Stock Quant'

    product_id = fields.Many2one(
        'wsc.product',
        string='Product',
        required=True,
        ondelete='restrict',
    )

    location_id = fields.Many2one(
        'wsc.location',
        string='Location',
        required=True,
        ondelete='restrict',
    )

    quantity = fields.Float(
        string='On Hand Quantity',
        default=0.0,
    )

    reserved_quantity = fields.Float(
        string='Reserved Quantity',
        default=0.0,
    )

    available_quantity = fields.Float(
        string='Available Quantity',
        compute='_compute_available_quantity',
        store=True,
    )

    _sql_constraints = [
        (
            'unique_product_location',
            'UNIQUE(product_id, location_id)',
            'A product can have only one quant per location.'
        )
    ]

    @api.depends('quantity','reserved_quantity')
    def _compute_available_quantity(self):
        for rec in self:
            rec.available_quantity = rec.quantity - rec.reserved_quantity

    @api.constrains('reserved_quantity', 'quantity')
    def _check_for_quantity(self):
        for rec in self:
            if rec.quantity < 0:
                raise ValidationError(
                    "On-hand quantity cannot be negative."
                )

            if rec.reserved_quantity < 0:
                raise ValidationError(
                    "Reserved quantity cannot be negative."
                )

            if rec.reserved_quantity > rec.quantity:
                raise ValidationError(
                    "Reserved quantity cannot exceed on-hand quantity."
                )

    @api.constrains('location_id')
    def _check_location_type(self):
        for rec in self:
            if rec.location_id.location_type != 'internal':
                raise ValidationError(
                    "Stock quants can only belong to internal locations."
                )
