from odoo import api, fields, models
from odoo.exceptions import ValidationError,UserError


class StockAdjustment(models.Model):
    _name = 'wsc.stock.adjustment'
    _description = 'Stock Adjustment'

    name = fields.Char(
        readonly=True,
        default='New',
        string='Ref',
        copy=False)
    date = fields.Date(
        default= fields.Date.today,
        required=True)
    warehouse_id = fields.Many2one(
        'wsc.warehouse',
        required=True)
    line_ids = fields.One2many(
        'wsc.stock.adjustment.line',
        'adjustment_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ],default='draft',required=True)
    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
        required=True)

    _sql_constraints = [
        (
            'unique_adjustment_product_location',
            'unique(adjustment_id, product_id, location_id)',
            'A product can only appear once per location in an adjustment.'
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for rec in vals_list:
            if rec.get('name','New') == 'New':
                rec['name']=(
                    self.env['ir.sequence'].next_by_code('adjustment_seq') or 'New'
                )
        return super().create(vals_list)

    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    "Only draft adjustments can be confirmed."
                )

            if not rec.line_ids:
                raise UserError(
                    "The adjustment must contain at least one line."
                )

            for line in rec.line_ids:
                if line.location_id.location_type != 'internal':
                    raise UserError(
                        "Stock adjustments are only allowed for internal locations."
                    )

                quant = self.env['wsc.stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.location_id.id),
                ], limit=1)

                if quant:
                    if line.counted_quantity < quant.reserved_quantity:
                        raise UserError(
                            "Counted quantity cannot be less than reserved quantity."
                        )

                    quant.quantity = line.counted_quantity

                elif line.counted_quantity > 0:
                    self.env['wsc.stock.quant'].create({
                        'product_id': line.product_id.id,
                        'location_id': line.location_id.id,
                        'quantity': line.counted_quantity,
                    })

            rec.state = 'confirmed'

        return True

    def action_cancel(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError('Only draft adjustments can be canceled.')
            rec.state = 'cancelled'

    def write(self, vals):
        for rec in self:
            if rec.state in ('confirmed', 'cancelled'):
                raise UserError(
                    "You cannot modify a confirmed or cancelled adjustment."
                )

        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    "You can only delete draft adjustments."
                )

        return super().unlink()


class StockAdjustmentLine(models.Model):
    _name = 'wsc.stock.adjustment.line'
    _description = 'Stock Adjustment Line'

    adjustment_id = fields.Many2one(
        'wsc.stock.adjustment',
        required=True,
        ondelete='cascade')
    product_id = fields.Many2one(
        'wsc.product',
        required=True)
    location_id = fields.Many2one(
        'wsc.location',
        required=True)
    theoretical_quantity = fields.Float(compute='_compute_theoretical_quantity')
    counted_quantity = fields.Float(required=True)
    difference = fields.Float(compute='_compute_difference')


    @api.depends('product_id','location_id')
    def _compute_theoretical_quantity(self):
        for rec in self :
            if rec.product_id and rec.location_id:
                quant = self.env['wsc.stock.quant'].search([
                    ('product_id','=',rec.product_id.id),
                    ('location_id','=',rec.location_id.id),
                ],limit=1)
                rec.theoretical_quantity = quant.quantity if quant else 0.0
            else:
                rec.theoretical_quantity = 0.0

    @api.depends('counted_quantity','theoretical_quantity')
    def _compute_difference(self):
        for rec in self :
            rec.difference = rec.counted_quantity - rec.theoretical_quantity

    @api.constrains('counted_quantity')
    def _check_counted_quantity(self):
        for rec in self :
            if rec.counted_quantity < 0 :
                raise ValidationError('Counted quantity cannot be negative.')

    @api.constrains('location_id', 'adjustment_id')
    def _check_location_warehouse(self):
        for rec in self:
            if rec.location_id.location_type != 'internal':
                raise ValidationError(
                    "Adjustment locations must be internal locations."
                )

            if rec.location_id.warehouse_id != rec.adjustment_id.warehouse_id:
                raise ValidationError(
                    "The selected location must belong to the adjustment warehouse."
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            adjustment = self.env['wsc.stock.adjustment'].browse(
                vals.get('adjustment_id')
            )

            if adjustment and adjustment.state != 'draft':
                raise UserError(
                    "You can only add lines to draft adjustments."
                )

        return super().create(vals_list)

    def write(self, vals):
        for rec in self:
            if rec.adjustment_id.state != 'draft':
                raise UserError(
                    "You cannot modify lines of a confirmed or cancelled adjustment."
                )

        return super().write(vals)

    def unlink(self):
        for rec in self:
            if rec.adjustment_id.state != 'draft':
                raise UserError(
                    "You cannot delete lines of a confirmed or cancelled adjustment."
                )

        return super().unlink()