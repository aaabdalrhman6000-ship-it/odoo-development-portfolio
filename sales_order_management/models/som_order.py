from odoo import api, fields, models
from odoo.exceptions import ValidationError,UserError


class SomOrder(models.Model):
    _name = 'som.order'
    _description = 'SOM Order'
    _inherit = ['mail.thread','mail.activity.mixin']

    name = fields.Char(default='New',readonly=True,string='Ref')
    partner_id = fields.Many2one('res.partner',required=True,tracking=True)
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        tracking=True)
    date_order = fields.Datetime(default=fields.Datetime.now,required=True,tracking=True)
    validity_date = fields.Date(help='Quotation expiration',tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ],default='draft',tracking=True)

    tag_ids = fields.Many2many('som.order.tag')
    line_ids = fields.One2many('som.order.line','order_id')
    amount_untaxed = fields.Monetary(default=0,store=True,compute='_compute_amount_untaxed')
    amount_tax = fields.Monetary(default=0,compute='_compute_amount_tax')
    amount_total = fields.Monetary(default=0,compute='_compute_amount_total',tracking=True)
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.user.company_id.currency_id)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self : self.env.company)
    note = fields.Text()
    cancel_reason = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for rec in vals_list:
            if rec.get('name','New') == 'New':
                rec['name']=(
                        self.env['ir.sequence'].next_by_code('order_seq') or 'New'
                )

        return super().create(vals_list)

    @api.depends('line_ids.subtotal')
    def _compute_amount_untaxed(self):
        for rec in self :
            rec.amount_untaxed = sum(rec.line_ids.mapped('subtotal'))

    @api.depends(
        'line_ids.tax_ids',
        'line_ids.discount',
        'line_ids.quantity',
        'line_ids.price_unit',
        'line_ids.product_id',
        'partner_id',
        'currency_id',
    )
    def _compute_amount_tax(self):
        for rec in self:
            total_tax = 0.0

            for line in rec.line_ids:
                if line.tax_ids:
                    discounted_price = (
                            line.price_unit * (1 - line.discount / 100)
                    )

                    taxes = line.tax_ids.compute_all(
                        discounted_price,
                        currency=rec.currency_id,
                        quantity=line.quantity,
                        product=line.product_id,
                        partner=rec.partner_id,
                        handle_price_include=False,
                    )

                    total_tax += (
                            taxes['total_included'] - taxes['total_excluded']
                    )

            rec.amount_tax = rec.currency_id.round(total_tax)

    @api.depends('amount_tax', 'amount_untaxed')
    def _compute_amount_total(self):
        for rec in self :
            rec.amount_total = rec.amount_tax + rec.amount_untaxed

    @api.constrains('validity_date')
    def _check_validity_date(self):
        for rec in self:
            if rec.validity_date and rec.date_order:
                if rec.validity_date < rec.date_order.date():
                    raise ValidationError('Validity date cannot be earlier than date order.')

    @api.constrains('cancel_reason','state')
    def _check_cancel_reason(self):
        for rec in self:
            if rec.state == 'cancelled' and not rec.cancel_reason:
                raise ValidationError('You must provide a cancellation reason.')


    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError('confirmed only')
            if not rec.line_ids:
                raise UserError('You cannot confirm an order without order lines.')

            if rec.amount_total <= 0:
                raise UserError('Order total must be greater than zero.')
            rec.state = 'confirmed'

    def action_done(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError('Done only')
            rec.state = 'done'

    def action_cancel(self):
        for rec in self :
            if rec.state not in ('draft','confirmed'):
                raise UserError('Cancellation only')
            rec.state = 'cancelled'

    def action_reset_to_draft(self):
        for rec in self:
            if rec.state != 'cancelled':
                raise UserError('Draft only')
            rec.state = 'draft'

    @api.model
    def check_cancelled_orders(self):
        expired_orders = self.sudo().search([
            ('state', '=', 'draft'),
            ('validity_date', '!=', False),
            ('validity_date', '<', fields.Date.today()),
        ])

        expired_orders.write({
            'state': 'cancelled',
            'cancel_reason': 'Automatically cancelled because the quotation validity date expired.',
        })