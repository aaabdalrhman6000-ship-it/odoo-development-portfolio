from odoo import api,models,fields
from odoo.exceptions import ValidationError


class SomOrderLine(models.Model):
    _name = 'som.order.line'
    _description = 'SOM Order Line'

    order_id = fields.Many2one('som.order',required=True)
    product_id = fields.Many2one('product.product',required=True)
    name = fields.Char(required=True)
    quantity = fields.Float(required=True)
    price_unit = fields.Monetary(currency_field="currency_id")
    discount = fields.Float()
    tax_ids = fields.Many2many('account.tax')
    subtotal = fields.Monetary(currency_field="currency_id",compute='_compute_subtotal')
    currency_id = fields.Many2one(
        'res.currency',
        default= lambda self : self.env.user.company_id.currency_id,
        related='product_id.currency_id',)

    @api.depends('discount','price_unit','quantity')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.price_unit * rec.quantity * (1 - rec.discount/100)

    @api.constrains('discount', 'price_unit', 'quantity')
    def _check_all(self):
        for rec in self:
            if rec.discount < 0 or rec.discount > 100:
                raise ValidationError(
                    'Discount must be between 0 and 100.'
                )

            if rec.price_unit < 0:
                raise ValidationError(
                    'Price unit cannot be negative.'
                )

            if rec.quantity <= 0:
                raise ValidationError(
                    'Quantity must be greater than zero.'
                )