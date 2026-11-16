from odoo import api, fields, models
from odoo.exceptions import ValidationError


class RepairOrder(models.Model):
    _name = 'repair.order'
    _description = 'Repair Order'

    ref = fields.Char(string='Ref',default='New',readonly=True)
    order_date = fields.Date(string='Order Date',default=fields.Date.today)
    expected_completion_date = fields.Date(string='Expected Completion Date')
    actual_completion_date = fields.Date(string='Actual Completion Date')
    description = fields.Text(string='Description')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancel', 'Cancelled'),
    ],default='draft',readonly=True)

    customer_id = fields.Many2one('repair.customer')
    vehicle_id = fields.Many2one('repair.vehicle')
    order_line_ids = fields.One2many('repair.order.line','order_id')
    mechanic_ids = fields.Many2many(
        'repair.mechanic',
        'repair_order_mechanic_rel',
        'order_id',
        'mechanic_id',
        string='Mechanics'
    )

    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_total_amount')

    total_service_amount = fields.Float(
        string='Total Service Amount',
        compute='_compute_service_amount')

    total_parts_amount = fields.Float(
        string='Total Parts Amount',
        compute='_compute_total_parts_amount')

    @api.model_create_multi
    def create(self, vals_list):
        for rec in vals_list:
            if rec.get('ref','New') == 'New':
                rec['ref']=(
                        self.env['ir.sequence'].next_by_code('order_seq') or 'New'
                )
        return super().create(vals_list)


    @api.depends('total_service_amount','total_parts_amount')
    def _compute_total_amount(self):
        for rec in self:
            rec.total_amount = rec.total_parts_amount + rec.total_service_amount

    @api.depends('order_line_ids.line_type', 'order_line_ids.subtotal')
    def _compute_service_amount(self):
        for rec in self:
            rec.total_service_amount = sum(
                rec.order_line_ids.filtered(
                    lambda line : line.line_type =='service'
                ).mapped('subtotal')
            )

    @api.depends('order_line_ids.line_type', 'order_line_ids.subtotal')
    def _compute_total_parts_amount(self):
        for rec in self:
            rec.total_parts_amount = sum(
                rec.order_line_ids.filtered(
                    lambda line : line.line_type =='spare_part'
                ).mapped('subtotal')
            )

    @api.constrains('customer_id','vehicle_id')
    def _check_customer_id_and_vehicle(self):
        for rec in self :
            if rec.customer_id and rec.vehicle_id :
                if rec.vehicle_id.customer_id != rec.customer_id :
                    raise ValidationError('The selected vehicle does not belong to this customer.')

    @api.constrains('expected_completion_date','order_date')
    def _check_expected_completion_date(self):
        for rec in self :
            if rec.order_date and rec.expected_completion_date :
                if rec.expected_completion_date < rec.order_date:
                    raise ValidationError('Expected completion date cannot be earlier than order date.')

    @api.constrains('order_date','actual_completion_date')
    def _check_actual_completion_date(self):
        for rec in self :
            if rec.order_date and rec.actual_completion_date:
                if rec.actual_completion_date < rec.order_date:
                    raise ValidationError('Actual completion date cannot be earlier than order date.')

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(
                    'Only draft orders can be confirmed.'
                )
            rec.state = 'confirmed'

    def action_start(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise ValidationError(
                    'Only confirmed orders can be moved to In Progress.'
                )
            rec.state = 'in_progress'

    def action_complete(self):
        for rec in self:
            if rec.state != 'in_progress':
                raise ValidationError(
                    'Only orders in progress can be completed.'
                )
            if not rec.customer_id :
                raise ValidationError('You should choose a customer.')
            if not rec.order_line_ids:
                raise ValidationError('You should set an order line.')
            if not rec.mechanic_ids:
                raise ValidationError('You should choose a mechanic .')
            if not rec.vehicle_id:
                raise ValidationError('You should choose a vehicle.')

            rec.state = 'completed'
            rec.actual_completion_date = fields.Date.today()

    def action_cancel(self):
        for rec in self:
            if rec.state not in ('draft', 'confirmed'):
                raise ValidationError(
                    'Only draft or confirmed orders can be cancelled.'
                )
            rec.state = 'cancel'

