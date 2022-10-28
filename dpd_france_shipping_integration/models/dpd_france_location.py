from odoo import models, fields, api


class DPDFranceLocations(models.Model):
    _name = "dpdfrance.locations"
    _rec_name = "pudo_name"
    pudo_id = fields.Char(string="Pudo Id", help="Pudo Id Number")
    pudo_name = fields.Char(string="Name", help="Pudo Name")
    pudo_street = fields.Char(string="Street", help="Pudo street")
    pudo_zip = fields.Char(string="Zip", help="Pudo zip")
    pudo_city = fields.Char(string="City", help="Pudo City")
    pudo_longitude = fields.Char(string="Longitude")
    pudo_latitude = fields.Char(string="Latitude")

    sale_order_id = fields.Many2one("sale.order", string="Sales Order")

    def set_location(self):
        self.sale_order_id.dpd_france_location_id = self.id
