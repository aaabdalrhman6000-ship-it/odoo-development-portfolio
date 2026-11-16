from odoo import fields, models,api
from odoo.exceptions import ValidationError
class Location(models.Model):
    _name = 'wsc.location'
    _description = 'Location'

    name = fields.Char(string='Location Name', required=True)
    complete_name = fields.Char(compute='_compute_complete_name')
    warehouse_id = fields.Many2one(
        'wsc.warehouse',
        string='Warehouse',
        ondelete='restrict',
    )
    parent_id = fields.Many2one(
        'wsc.location',
        string='Parent Location',
        ondelete='restrict',
    )
    child_ids = fields.One2many(
        'wsc.location',
        'parent_id',string='Child Locations')

    location_type = fields.Selection([
        ('internal', 'Internal'),
        ('supplier', 'Supplier'),
        ('customer', 'Customer'),
    ], string='Location Type', required=True, default='internal')
    active = fields.Boolean(default=True)

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for rec in self:
            if rec.parent_id:
                parent_name = rec.parent_id.complete_name or rec.parent_id.name
                rec.complete_name = f"{parent_name}/{rec.name}" if rec.name else parent_name
            else:
                rec.complete_name = rec.name or ''

    @api.constrains('parent_id')
    def _check_parent_location(self):
        for rec in self:
            if rec.parent_id == rec:
                raise ValidationError(
                    "A location cannot be its own parent."
                )

            parent = rec.parent_id

            while parent:
                if parent == rec:
                    raise ValidationError(
                        "Circular location hierarchy is not allowed."
                    )

                parent = parent.parent_id

    @api.constrains('warehouse_id', 'parent_id')
    def _check_parent_warehouse(self):
        for rec in self:
            if rec.parent_id:
                if (
                        rec.warehouse_id != rec.parent_id.warehouse_id
                        and (rec.warehouse_id or rec.parent_id.warehouse_id)
                ):
                    raise ValidationError(
                        "A child location must belong to the same warehouse as its parent."
                    )

    @api.constrains('name')
    def _check_location_name(self):
        for rec in self:
            if not rec.name or not rec.name.strip():
                raise ValidationError("Location name cannot be empty.")

    @api.constrains('warehouse_id', 'location_type')
    def _check_internal_warehouse(self):
        for rec in self:
            if rec.location_type == 'internal' and not rec.warehouse_id:
                raise ValidationError(
                    "Internal locations must belong to a warehouse."
                )