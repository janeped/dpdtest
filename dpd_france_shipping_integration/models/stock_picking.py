from odoo import fields, models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    dpd_france_default_weight = fields.Char("DPD France Default Weight",copy=False,default=3)

