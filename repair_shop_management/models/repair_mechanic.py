from odoo import api, fields, models

class RepairMechanic(models.Model):
    _name = 'repair.mechanic'
    _description = 'Repair Mechanic'

    name = fields.Char(required=True)
    phone = fields.Char(required=True)
    email = fields.Char()
    specialization = fields.Char(required=True)
    active = fields.Boolean(default=True)

    user_id = fields.Many2one('res.users')
    repair_order_ids = fields.Many2many(
        'repair.order',
        'repair_order_mechanic_rel',
        'mechanic_id',
        'order_id',
        string='Repair Orders'
    )

    _sql_constraints = [
        ('unique_user_id','UNIQUE(user_id)','This user already exists.'),
    ]
