from odoo import fields, models
from odoo.exceptions import UserError


class SomOrderCancelWizard(models.TransientModel):
    _name = 'som.order.cancel.wizard'
    _description = 'SOM Order Cancel Wizard'

    order_id = fields.Many2one(
        'som.order',
        string='Order',
        required=True
    )

    cancel_reason = fields.Text(
        string='Cancel Reason',
        required=True
    )

    def action_cancel_order(self):
        self.ensure_one()

        order = self.order_id

        if order.state not in ('draft', 'confirmed'):
            raise UserError(
                'Only draft or confirmed orders can be cancelled.'
            )

        order.write({
            'cancel_reason': self.cancel_reason,
            'state': 'cancelled',
        })

        return {'type': 'ir.actions.act_window_close'}