from odoo import  fields, models

class HelpdeskTag(models.Model):
    _name = 'helpdesk.tag'
    _description = 'Helpdesk Tag'

    name = fields.Char(string='Name',required=True)
    color = fields.Integer()
    active = fields.Boolean(default=True)