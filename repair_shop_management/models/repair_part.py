from odoo import fields, models ,api
from odoo.exceptions import ValidationError


class RepairPart(models.Model):
    _name = 'repair.part'
    _description = 'Repair Part'

    name = fields.Char(string='Name',required=True)
    part_number = fields.Char(string='Part Number',required=True)
    description = fields.Char(string='Description')
    price = fields.Float(string='Price')
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('unique_part_number', 'unique (part_number)', 'This part number already exists.'),
    ]

    @api.constrains('price')
    def _check_price(self):
        for rec in self:
            if rec.price < 0:
                raise ValidationError('Price cannot be less than 0')
