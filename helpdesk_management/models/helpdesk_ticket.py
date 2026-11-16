from odoo import api, fields, models
# from datetime import timedelta
from odoo.exceptions import ValidationError


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _order = 'date_create desc'

    ref = fields.Char(string="Reference",readonly=True,default='New')
    name = fields.Char(string="Name",required=True)
    description = fields.Text(string="Description")

    priority = fields.Selection([
        ('low','Low'),
        ('normal','Normal'),
        ('high','High'),
        ('urgent','Urgent'),
    ],default='normal')

    state = fields.Selection([
        ('new','New'),
        ('in_progress','In Progress'),
        ('solved','Solved'),
        ('closed','Closed'),
    ],default='new')

    date_create = fields.Datetime(default=fields.Datetime.now)
    deadline = fields.Date(string="Deadline")
    is_urgent = fields.Boolean(default=False)
    estimated_hours = fields.Float(string="Estimated Hours")
    active = fields.Boolean(default=True)

    is_overdue = fields.Boolean(compute='_compute_is_overdue',store=True)
    days_remaining = fields.Integer(compute='_compute_days_remaining')
    ticket_duration = fields.Float(compute='_compute_ticket_duration')

    partner_id = fields.Many2one('res.partner',string='Customer')
    user_id = fields.Many2one('res.users')
    team_id = fields.Many2one('helpdesk.team')
    tag_ids = fields.Many2many('helpdesk.tag')


    _sql_constraints = [
        ('check_estimated_hours',
         'CHECK(estimated_hours >= 0)',
         'Estimated Hours cannot be negative.'),
    ]


    @api.model_create_multi
    def create(self, vals):
        for rec in vals :
            if rec.get('ref','New') == 'New':
                rec['ref'] =(
                    self.env['ir.sequence'].next_by_code('ticket_seq') or 'New'
                )
        return super().create(vals)

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_solve(self):
        self.write({'state': 'solved'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_reset(self):
        self.write({'state': 'new'})

    @api.depends('deadline','state')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for rec in self:
            if rec.deadline :
                if rec.deadline < today and rec.state not in ['solved','closed']:
                    rec.is_overdue = True
                else:
                    rec.is_overdue = False
            else:
                rec.is_overdue = False

    @api.depends('deadline')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for rec in self:
            if rec.deadline :
                days_remaining = rec.deadline - today
                rec.days_remaining = days_remaining.days
            else :
                rec.days_remaining = 0

    @api.depends('date_create')
    def _compute_ticket_duration(self):
        for rec in self:
            if rec.date_create :
                duration = fields.Datetime.now() - rec.date_create
                rec.ticket_duration = duration.total_seconds() / 86400
            else:
                rec.ticket_duration = 0

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.description = f"Customer : {self.partner_id.name}"
        else:
            self.description= 'Customer'

    @api.onchange('priority')
    def _onchange_priority(self):
        if self.priority =='urgent':
            self.is_urgent = True
        else:
            self.is_urgent = False

    @api.constrains('deadline', 'date_create')
    def _check_deadline(self):
        for rec in self :
            if rec.deadline and rec.date_create :
                creation_date = fields.Date.to_date(rec.date_create)
                if rec.deadline < creation_date :
                    raise ValidationError('Deadline cannot be before ticket creation date.')



    @api.constrains('estimated_hours')
    def _check_estimated_hours(self):
        for rec in self :
            if rec.estimated_hours:
                if rec.estimated_hours < 0 :
                    raise ValidationError('Estimated Hours cannot be negative.')