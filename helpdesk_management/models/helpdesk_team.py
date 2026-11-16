from odoo import fields, models , api

class HelpdeskTeam(models.Model):
    _name = 'helpdesk.team'
    _description = 'Helpdesk Team'

    name = fields.Char(required=True)
    description = fields.Text()
    leader_id = fields.Many2one('res.users')
    member_ids = fields.Many2many('res.users')
    ticket_ids = fields.One2many('helpdesk.ticket','team_id')
    ticket_count = fields.Integer(compute='_compute_ticket_count')
    active = fields.Boolean(default=True)

    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        for rec in self:
            rec.ticket_count = len(rec.ticket_ids)


