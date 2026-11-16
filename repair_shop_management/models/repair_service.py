from odoo import fields, models, api
from odoo.exceptions import ValidationError


class RepairService(models.Model):
    _name = 'repair.service'
    _description = 'Repair Service'

    name = fields.Char(string='Repair Name',required=True)
    description = fields.Char(string='Repair Description')
    price = fields.Float(string='Repair Price')
    estimated_hours = fields.Float(string='Estimated Hours')
    active = fields.Boolean(string='Active', default=True)

    @api.constrains('price','estimated_hours')
    def _check_estimated_hours_and_price(self):
        for rec in self :
            if rec.price < 0 :
                raise ValidationError('Price cannot be less than 0')
            if rec.estimated_hours <= 0 :
                raise ValidationError('Estimated hours must be greater than 0')
