from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from requests import request
import base64
import hashlib
import xml.etree.ElementTree as etree
from odoo.addons.dpd_france_shipping_integration.models.dpd_response import Response


class SaleOrder(models.Model):
    _inherit = "sale.order"

    dpd_france_location_ids = fields.One2many("dpdfrance.locations", "sale_order_id",
                                              string="DPD France Locations")
    dpd_france_location_id = fields.Many2one("dpdfrance.locations", string="DPD France Location",
                                             help="DPD Fracne locations", copy=False)

    def get_locations(self):
        order = self
        # Shipper and Recipient Address
        shipper_address = order.warehouse_id.partner_id
        recipient_address = order.partner_shipping_id
        # check sender Address
        if not shipper_address.zip or not shipper_address.city or not shipper_address.country_id:
            raise ValidationError("Please Define Proper Sender Address!")
        # check Receiver Address
        if not recipient_address.zip or not recipient_address.city or not recipient_address.country_id:
            raise ValidationError("Please Define Proper Recipient Address!")
        if not self.carrier_id.company_id:
            raise ValidationError("Credential not available!")
        if self.carrier_id.dpd_service != "Pickup":
            raise ValidationError("For Get Pickup Location You Need To Select Pickup Service in Shipping Method")
        try:
            pickup_point_request = etree.Element("soap12:Envelope")
            pickup_point_request.attrib['xmlns:xsi'] = "http://www.w3.org/2001/XMLSchema-instance"
            pickup_point_request.attrib['xmlns:xsd'] = "http://www.w3.org/2001/XMLSchema"
            pickup_point_request.attrib['xmlns:soap12'] = "http://www.w3.org/2003/05/soap-envelope"

            body_node = etree.SubElement(pickup_point_request, "soap12:Body")
            get_pudo_list = etree.SubElement(body_node, 'GetPudoList')
            get_pudo_list.attrib['xmlns'] = "http://MyPudo.pickup-services.com/"
            etree.SubElement(get_pudo_list, 'carrier').text = self.carrier_id.company_id.dpd_fr_carrier_id or ''
            etree.SubElement(get_pudo_list, 'key').text = self.carrier_id.company_id.dpd_fr_key or ''
            etree.SubElement(get_pudo_list, 'zipCode').text = str(recipient_address.zip or "")
            etree.SubElement(get_pudo_list, 'city').text = str(recipient_address.city or "")
            etree.SubElement(get_pudo_list, 'countrycode').text = str(
                recipient_address.country_id and recipient_address.country_id.code or '')
            etree.SubElement(get_pudo_list, 'requestID').text = self.name or '0'
            etree.SubElement(get_pudo_list, 'date_from').text = self.date_order.strftime(
                "%d/%m/%Y") or fields.Date.today().strftime("%d/%m/%Y")
            etree.SubElement(get_pudo_list, 'max_pudo_number').text = "10"
        except Exception as e:
            raise ValidationError(e)

        try:
            headers = {
                'SOAPAction': 'http://MyPudo.pickup-services.com/GetPudoList',
                'Content-Type': 'application/soap+xml; charset="utf-8',
            }
            URL = "http://mypudo.pickup-services.com/mypudo/mypudo.asmx"
            response_data = request(method='POST', url=URL, headers=headers, data=etree.tostring(pickup_point_request))
        except Exception as e:
            raise ValidationError(e)
        if response_data.status_code in [200, 201]:
            api = Response(response_data)
            response_data = api.dict()
            dpd_fracne_locations = self.env['dpdfrance.locations']
            existing_records = self.env['dpdfrance.locations'].search(
                [('sale_order_id', '=', order and order.id)])
            existing_records.sudo().unlink()
            if response_data:
                common_response = response_data.get('Envelope').get('Body').get('GetPudoListResponse').get(
                    'GetPudoListResult').get('RESPONSE')
                if common_response.get('ERROR'):
                    raise ValidationError(common_response.get('ERROR').get('value'))
                locations = common_response.get('PUDO_ITEMS').get('PUDO_ITEM')
                if isinstance(locations,dict):
                    locations = [locations]
                for location in locations:
                    point_location_id = dpd_fracne_locations.sudo().create(
                        {'pudo_id': location.get('PUDO_ID'),
                         'pudo_name': location.get('NAME'),
                         'pudo_street': location.get('ADDRESS1'),
                         'pudo_zip': location.get('ZIPCODE'),
                         'pudo_city': location.get('CITY'),
                         'sale_order_id': self.id})
            else:
                raise ValidationError("Location Not Found For This Address! %s " % (response_data))
        else:
            raise ValidationError("%s %s" % (response_data, response_data.text))
