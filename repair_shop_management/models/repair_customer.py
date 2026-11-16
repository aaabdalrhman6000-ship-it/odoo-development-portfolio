from odoo import fields, models

class RepairCustomer(models.Model):
    _name = 'repair.customer'
    _description = 'Repair Customer'
    _order = 'name asc'

    name = fields.Char(string='Customer Name',required=True)
    phone = fields.Char(string='Phone Number',required=True)
    email = fields.Char(string='Email Address')
    address = fields.Text(string='Address')
    active = fields.Boolean(default=True)

    vehicle_ids = fields.One2many('repair.vehicle', 'customer_id')
    repair_order_ids = fields.One2many('repair.order','customer_id')

