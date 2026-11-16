from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class StockPicking(models.Model):
    _name = 'wsc.stock.picking'
    _description = 'Stock Picking'

    ref = fields.Char(
        string='Ref',
        readonly=True,
        default='New',
        copy=False,
    )

    operation_type = fields.Selection([
        ('receipt', 'Receipt'),
        ('delivery', 'Delivery'),
        ('internal_transfer', 'Internal Transfer'),
    ], required=True)

    scheduled_date = fields.Datetime(
        default=fields.Datetime.now,
    )

    date_done = fields.Datetime(readonly=True)

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
    )

    warehouse_id = fields.Many2one(
        'wsc.warehouse',
        required=True,
        ondelete='restrict',
    )

    location_id = fields.Many2one(
        'wsc.location',
        required=True,
        ondelete='restrict',
    )

    location_dest_id = fields.Many2one(
        'wsc.location',
        string='Destination Location',
        required=True,
        ondelete='restrict',
    )

    move_ids = fields.One2many(
        'wsc.stock.move',
        'picking_id',
        string='Stock Moves',
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], default='draft', required=True, readonly=True)

    user_id = fields.Many2one(
        'res.users',
        default=lambda self: self.env.user,
    )

    total_quantity = fields.Float(
        string='Total Quantity',
        compute='_compute_total_quantity',
        store=True,
    )

    # Generate picking reference
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', 'New') == 'New':
                sequence = self.env['ir.sequence'].next_by_code(
                    'picking_seq'
                )

                if not sequence:
                    raise UserError(
                        "Picking sequence is not configured."
                    )

                vals['ref'] = sequence

        return super().create(vals_list)

    # Calculate total planned quantity
    @api.depends('move_ids.product_uom_qty')
    def _compute_total_quantity(self):
        for rec in self:
            rec.total_quantity = sum(
                rec.move_ids.mapped('product_uom_qty')
            )

    # Validate source and destination locations
    @api.constrains(
        'operation_type',
        'location_id',
        'location_dest_id',
    )
    def _check_locations(self):
        for rec in self:
            if rec.location_id == rec.location_dest_id:
                raise ValidationError(
                    "Source and destination locations must be different."
                )

            source_type = rec.location_id.location_type
            destination_type = rec.location_dest_id.location_type

            if rec.operation_type == 'receipt':
                if source_type != 'supplier':
                    raise ValidationError(
                        "Receipt source location must be a supplier location."
                    )

                if destination_type != 'internal':
                    raise ValidationError(
                        "Receipt destination must be an internal location."
                    )

            elif rec.operation_type == 'delivery':
                if source_type != 'internal':
                    raise ValidationError(
                        "Delivery source location must be an internal location."
                    )

                if destination_type != 'customer':
                    raise ValidationError(
                        "Delivery destination must be a customer location."
                    )

            elif rec.operation_type == 'internal_transfer':
                if (
                    source_type != 'internal'
                    or destination_type != 'internal'
                ):
                    raise ValidationError(
                        "Internal transfers require two internal locations."
                    )

    # Validate warehouse ownership of internal locations
    @api.constrains(
        'warehouse_id',
        'location_id',
        'location_dest_id',
    )
    def _check_warehouse_locations(self):
        for rec in self:
            locations = rec.location_id | rec.location_dest_id

            for location in locations:
                if (
                    location.location_type == 'internal'
                    and location.warehouse_id != rec.warehouse_id
                ):
                    raise ValidationError(
                        "Internal locations must belong to "
                        "the selected warehouse."
                    )

    # Validate all related stock moves
    @api.constrains(
        'move_ids',
        'location_id',
        'location_dest_id',
    )
    def _check_picking_moves(self):
        for rec in self:
            for move in rec.move_ids:
                if move.location_id != rec.location_id:
                    raise ValidationError(
                        "Stock move source must match picking source."
                    )

                if move.location_dest_id != rec.location_dest_id:
                    raise ValidationError(
                        "Stock move destination must match picking destination."
                    )

    # Confirm picking and all its moves
    def action_confirm(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    "Only draft pickings can be confirmed."
                )

            if not rec.move_ids:
                raise UserError(
                    "A picking must contain at least one stock move."
                )

            for move in rec.move_ids:
                if move.state != 'draft':
                    raise UserError(
                        "All stock moves must be in draft state."
                    )

            for move in rec.move_ids:
                move.write({'state': 'confirmed'})

            super(StockPicking, rec).write({
                'state': 'confirmed',
            })

        return True

    # Complete picking and all its moves
    def action_done(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(
                    "Only confirmed pickings can be completed."
                )

            if not rec.move_ids:
                raise UserError(
                    "This picking has no stock moves."
                )

            for move in rec.move_ids:
                if move.state != 'confirmed':
                    raise UserError(
                        "All stock moves must be confirmed before completion."
                    )

            for move in rec.move_ids:
                move.action_done()

            super(StockPicking, rec).write({
                'state': 'done',
                'date_done': fields.Datetime.now(),
            })

        return True

    # Cancel picking and all its moves
    def action_cancel(self):
        for rec in self:
            if rec.state not in ('draft', 'confirmed'):
                raise UserError(
                    "Only draft or confirmed pickings can be cancelled."
                )

            if any(move.state == 'done' for move in rec.move_ids):
                raise UserError(
                    "You cannot cancel a picking containing completed moves."
                )

            for move in rec.move_ids:
                if move.state not in ('draft', 'confirmed'):
                    raise UserError(
                        "Only draft or confirmed moves can be cancelled."
                    )

            for move in rec.move_ids:
                move.write({'state': 'cancelled'})

            super(StockPicking, rec).write({
                'state': 'cancelled',
            })

        return True

    # Protect important picking information
    def write(self, vals):
        workflow_fields = {
            'state',
            'date_done',
            'ref',
        }

        protected_fields = {
            'operation_type',
            'warehouse_id',
            'location_id',
            'location_dest_id',
            'partner_id',
            'move_ids',
        }

        if workflow_fields.intersection(vals):
            raise UserError(
                "Workflow fields can only be changed through picking actions."
            )

        for rec in self:
            if (
                rec.state != 'draft'
                and protected_fields.intersection(vals)
            ):
                raise UserError(
                    "You cannot change picking information or stock moves "
                    "after confirmation."
                )

        return super().write(vals)

    # Delete draft pickings only
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(
                    "Only draft pickings can be deleted."
                )

        return super().unlink()
