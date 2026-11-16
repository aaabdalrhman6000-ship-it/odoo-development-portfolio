from odoo import api, fields, models

class SalesOrderTag(models.Model):
    _name = 'som.order.tag'
    _description = 'Sales Order Tag'

    name = fields.Char(required=True)
    color = fields.Integer(default=0)

    _sql_constraints = [
        ('unique_name','UNIQUE (name)','This field must be unique.'),
    ]