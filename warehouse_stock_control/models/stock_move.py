from odoo import fields, models, api
from odoo.exceptions import UserError, ValidationError


class StockMove(models.Model):
    _name = 'wsc.stock.move'
    _description = 'Warehouse Stock Move'

    name = fields.Char(string='Stock Move')

    picking_id = fields.Many2one(
        'wsc.stock.picking',
        string='Picking',
        required=True,
        ondelete='cascade',
    )

    product_id = fields.Many2one(
        'wsc.product',
        string='Product',
        required=True,
        ondelete='restrict',
    )

    product_uom_qty = fields.Float(
        string='Quantity',
        required=True,
    )

    location_id = fields.Many2one(
        'wsc.location',
        string='Source Location',
        required=True,
        ondelete='restrict',
    )

    location_dest_id = fields.Many2one(
        'wsc.location',
        string='Destination Location',
        required=True,
        ondelete='restrict',
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', required=True)

    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
    )

    quantity_done = fields.Float(
        string='Quantity Done',
        default=0.0,
    )

    # Update stock quantity at a specific location
    def _update_stock_quant(self, location, quantity_delta):
        self.ensure_one()

        quant = self.env['wsc.stock.quant'].search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', location.id),
        ], limit=1)

        if quant:
            new_quantity = quant.quantity + quantity_delta

            if new_quantity < 0:
                raise UserError(
                    f"Not enough stock for {self.product_id.name} "
                    f"in location {location.complete_name}."
                )

            if new_quantity < quant.reserved_quantity:
                raise UserError(
                    "You cannot reduce stock below the reserved quantity."
                )

            quant.quantity = new_quantity

        else:
            if quantity_delta < 0:
                raise UserError(
                    f"No stock found for {self.product_id.name} "
                    f"in location {location.complete_name}."
                )

            if quantity_delta > 0:
                self.env['wsc.stock.quant'].create({
                    'product_id': self.product_id.id,
                    'location_id': location.id,
                    'quantity': quantity_delta,
                })

    # Complete stock movement
    def action_done(self):
        for rec in self:
            if rec.state != 'confirmed':
                raise UserError(
                    "Only confirmed stock moves can be completed."
                )

            if rec.quantity_done <= 0:
                raise UserError(
                    "Done quantity must be greater than zero."
                )

            if rec.quantity_done > rec.product_uom_qty:
                raise UserError(
                    "Done quantity cannot exceed planned quantity."
                )

            operation_type = rec.picking_id.operation_type

            if operation_type == 'receipt':
                rec._update_stock_quant(
                    rec.location_dest_id,
                    rec.quantity_done,
                )

            elif operation_type == 'delivery':
                rec._update_stock_quant(
                    rec.location_id,
                    -rec.quantity_done,
                )

            elif operation_type == 'internal_transfer':
                rec._update_stock_quant(
                    rec.location_id,
                    -rec.quantity_done,
                )

                rec._update_stock_quant(
                    rec.location_dest_id,
                    rec.quantity_done,
                )

            else:
                raise UserError("Invalid picking operation type.")

            rec.write({'state': 'done'})

        return True

    # Prevent modification of protected stock move information
    def write(self, vals):
        protected_fields = {
            'picking_id',
            'product_id',
            'product_uom_qty',
            'location_id',
            'location_dest_id',
        }

        for rec in self:
            if rec.state in ('done', 'cancelled'):
                raise UserError(
                    "You cannot modify a completed or cancelled stock move."
                )

            if (
                rec.state == 'confirmed'
                and protected_fields.intersection(vals)
            ):
                raise UserError(
                    "You cannot change product, locations, picking, "
                    "or planned quantity after confirmation."
                )

        return super().write(vals)

    # Prevent deletion of completed or cancelled moves
    def unlink(self):
        for rec in self:
            if rec.state in ('done', 'cancelled'):
                raise UserError(
                    "You cannot delete a completed or cancelled stock move."
                )

        return super().unlink()

    # Validate planned and completed quantities
    @api.constrains('product_uom_qty', 'quantity_done')
    def _check_quantities(self):
        for rec in self:
            if rec.product_uom_qty <= 0:
                raise ValidationError(
                    "Planned quantity must be greater than zero."
                )

            if rec.quantity_done < 0:
                raise ValidationError(
                    "Done quantity cannot be negative."
                )

            if rec.quantity_done > rec.product_uom_qty:
                raise ValidationError(
                    "Done quantity cannot exceed planned quantity."
                )

    # Validate source and destination locations
    @api.constrains(
        'location_id',
        'location_dest_id',
        'picking_id',
    )
    def _check_move_locations(self):
        for rec in self:
            if rec.location_id == rec.location_dest_id:
                raise ValidationError(
                    "Source and destination locations cannot be the same."
                )

            if rec.location_id and rec.location_dest_id:
                operation_type = rec.picking_id.operation_type

                if operation_type == 'receipt':
                    if rec.location_id.location_type != 'supplier':
                        raise ValidationError(
                            "Receipt source must be a supplier location."
                        )

                    if rec.location_dest_id.location_type != 'internal':
                        raise ValidationError(
                            "Receipt destination must be an internal location."
                        )

                elif operation_type == 'delivery':
                    if rec.location_id.location_type != 'internal':
                        raise ValidationError(
                            "Delivery source must be an internal location."
                        )

                    if rec.location_dest_id.location_type != 'customer':
                        raise ValidationError(
                            "Delivery destination must be a customer location."
                        )

                elif operation_type == 'internal_transfer':
                    if (
                        rec.location_id.location_type != 'internal'
                        or rec.location_dest_id.location_type != 'internal'
                    ):
                        raise ValidationError(
                            "Internal transfers require internal locations."
                        )

                else:
                    raise ValidationError(
                        "Invalid picking operation type."
                    )

            if rec.picking_id:
                if rec.location_id != rec.picking_id.location_id:
                    raise ValidationError(
                        "Move source location must match "
                        "the picking source location."
                    )

                if rec.location_dest_id != rec.picking_id.location_dest_id:
                    raise ValidationError(
                        "Move destination location must match "
                        "the picking destination location."
                    )
