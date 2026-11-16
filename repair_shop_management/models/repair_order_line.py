from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RepairOrderLine(models.Model):
    _name = 'repair.order.line'
    _description = 'Repair Order Line'

    order_id = fields.Many2one('repair.order',required=True)
    service_id = fields.Many2one('repair.service')
    part_id = fields.Many2one('repair.part')
    line_type = fields.Selection([
        ('service','Service'),
        ('spare_part','Spare Part'),
    ],required=True)
    description = fields.Char()
    quantity = fields.Float()
    unit_price = fields.Float()
    subtotal = fields.Float(compute='_compute_subtotal')

    _sql_constraints = [
        ('check_quantity', 'CHECK (quantity > 0)',
         'Quantity must be greater than 0'),
        ('check_unit_price', 'CHECK (unit_price >= 0)',
         'Unit price cannot be negative'),
    ]

    @api.depends('quantity','unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.quantity * rec.unit_price

    @api.constrains('line_type', 'service_id', 'part_id')
    def _check_line_type(self):
        for rec in self:
            if rec.line_type == 'service':
                if not rec.service_id:
                    raise ValidationError('Please select a service.')
                if rec.part_id:
                    raise ValidationError(
                        'A service line cannot have a spare part.'
                    )

            elif rec.line_type == 'spare_part':
                if not rec.part_id:
                    raise ValidationError('Please select a spare part.')
                if rec.service_id:
                    raise ValidationError(
                        'A spare part line cannot have a service.'
                    )