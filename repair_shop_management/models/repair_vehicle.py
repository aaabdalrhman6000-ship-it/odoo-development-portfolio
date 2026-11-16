from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RepairVehicle(models.Model):
    _name = 'repair.vehicle'
    _description = 'Repair Vehicle'
    _order = 'name asc'

    name = fields.Char(string='vehicle name', required=True)
    license_plate = fields.Char(required=True)
    brand = fields.Char()
    model_year = fields.Integer(required=True)
    color = fields.Char()
    vin = fields.Char(required=True)
    active = fields.Boolean(default=True)

    customer_id = fields.Many2one('repair.customer',required=True)
    repair_order_ids = fields.One2many('repair.order','vehicle_id')

    _sql_constraints = [
        ('unique_license_plate', 'unique (license_plate)', 'License Plate should be unique'),
    ]

    @api.constrains('model_year')
    def _check_model_year(self):
        for rec in self:
            if rec.model_year <=0:
                raise ValidationError('Model year must be greater than 0')
