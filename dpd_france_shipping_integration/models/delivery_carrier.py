# -*- coding: utf-8 -*-

import bs4
from odoo import fields, models, _
import binascii
from odoo.exceptions import ValidationError
import xml.etree.ElementTree as etree
from .dpd_request import DPDFranceRequest
# from .dpd_test_response import DPDTestResponse


class DPDDeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    delivery_type = fields.Selection(selection_add=[("dpd_fr", "DPD France")],
                                     ondelete={'dpd_fr': 'set default'})
    dpd_service = fields.Selection([('Classic', 'Classic'), ('Predict', 'Predict'), ('Pickup', 'Pickup')],
                                   string="DPD Services", default="Classic")

    def dpd_fr_rate_shipment(self, order):
        return {'success': True, 'price': 0.0, 'error_message': False, 'warning_message': False}

    def dpd_fr_send_shipping(self, pickings):
        url = (self.company_id and self.company_id.dpd_fr_api_url)
        request_body = self.prepare_dpd_fr_request_body(picking=pickings)
        response_data = DPDFranceRequest.send_request(self, request_data=request_body, url=url)
        # response_data = DPDTestResponse.api_response(self)
        result = response_data and response_data.get('Envelope') and response_data.get('Envelope').get(
            'Body') and response_data.get('Envelope').get('Body').get(
            'CreateShipmentWithLabelsResponse') and response_data.get('Envelope').get('Body').get(
            'CreateShipmentWithLabelsResponse').get('CreateShipmentWithLabelsResult')
        if not result:
            raise ValidationError(_("Label Data not found in response {}".format(response_data)))
        parcel_number = result and result.get('shipments') and result.get('shipments').get('Shipment') and result.get(
            'shipments').get('Shipment').get('parcelnumber')
        dpd_label = result.get('labels') and result.get('labels').get('Label')
        if dpd_label:
            for data in dpd_label:
                doc_type = data and data.get('type')
                label_data = data and data.get('label')
                binary_data = binascii.a2b_base64(str(label_data))
                pickings.message_post(body="Shipment Created!", attachments=[
                    ('DPD-%s(%s).%s' % (parcel_number, doc_type.lower(), "pdf"), binary_data)])
        shipping_data = {
            'exact_price': 0.0,
            'tracking_number': parcel_number}
        return [shipping_data]

    def prepare_dpd_fr_request_body(self, picking):
        sender_add = picking.sale_id and picking.sale_id.warehouse_id and picking.sale_id.warehouse_id.partner_id
        receiver_add = picking and picking.partner_id
        for address in [sender_add, receiver_add]:
            res = [field for field in ['zip', 'name', 'city', 'street', 'country_id'] if not address[field]]
            if res:
                raise ValidationError("Please Define {0} in {1}".format(', '.join(res), address.name))

        envelope = etree.Element('Envelope')
        envelope.attrib['xmlns'] = 'http://schemas.xmlsoap.org/soap/envelope/'
        header = etree.SubElement(envelope, 'Header')
        user_credentials = etree.SubElement(header, 'UserCredentials')
        user_credentials.attrib['xmlns'] = 'http://www.cargonet.software'
        etree.SubElement(user_credentials, 'userid').text = '{}'.format(
            self.company_id and self.company_id.dpd_fr_username)
        etree.SubElement(user_credentials, 'password').text = '{}'.format(
            self.company_id and self.company_id.dpd_fr_password)
        body = etree.SubElement(envelope, 'Body')
        create_shipment_wth_label = etree.SubElement(body, 'CreateShipmentWithLabels')
        create_shipment_wth_label.attrib['xmlns'] = "http://www.cargonet.software"
        request = etree.SubElement(create_shipment_wth_label, 'request')

        receiver_address = etree.SubElement(request, 'receiveraddress')
        etree.SubElement(receiver_address, 'countryPrefix').text = '{}'.format(
            receiver_add and receiver_add.country_id and receiver_add.country_id.code or '')
        etree.SubElement(receiver_address, 'zipCode').text = '{}'.format(receiver_add.zip or '')
        etree.SubElement(receiver_address, 'city').text = '{}'.format(receiver_add.city or '')
        etree.SubElement(receiver_address, 'street').text = '{}'.format(receiver_add.street or '')
        etree.SubElement(receiver_address, 'name').text = '{}'.format(receiver_add.name or '')
        etree.SubElement(receiver_address, 'phoneNumber').text = '{}'.format(receiver_add.phone or '')
        # etree.SubElement(receiver_address, 'faxNumber').text = ''
        # etree.SubElement(receiver_address, 'geoX').text = ''
        # etree.SubElement(receiver_address, 'geoY').text = ''

        shipper_address = etree.SubElement(request, 'shipperaddress')
        etree.SubElement(shipper_address, 'countryPrefix').text = '{}'.format(
            sender_add and sender_add.country_id and sender_add.country_id.code or '')
        etree.SubElement(shipper_address, 'zipCode').text = '{}'.format(sender_add.zip or '')
        etree.SubElement(shipper_address, 'city').text = '{}'.format(sender_add.city or '')
        etree.SubElement(shipper_address, 'street').text = '{}'.format(sender_add.street or '')
        etree.SubElement(shipper_address, 'name').text = '{}'.format(sender_add.name or '')
        etree.SubElement(shipper_address, 'phoneNumber').text = '{}'.format(sender_add.phone or '')
        # etree.SubElement(shipper_address, 'faxNumber').text = ''
        # etree.SubElement(shipper_address, 'geoX').text = ''
        # etree.SubElement(shipper_address, 'geoY').text = ''
        # we pass static value for country code, not get value from Odoo, for more information refer doc
        etree.SubElement(request, 'customer_countrycode').text = '250'
        etree.SubElement(request,
                         'customer_centernumber').text = '%s' % self.company_id and self.company_id.dpd_fr_center_number
        etree.SubElement(request,
                         'customer_number').text = '%s' % self.company_id and self.company_id.dpd_fr_customer_number

        if self.dpd_service != 'Classic':
            services_tag = etree.SubElement(request, 'services')
            contact_tag = etree.SubElement(services_tag, 'contact')
            etree.SubElement(contact_tag, 'sms').text = receiver_add.phone or ''
            etree.SubElement(contact_tag, 'email').text = receiver_add.email or ''
            if self.dpd_service == 'Predict':
                etree.SubElement(contact_tag, 'type').text = 'Predict'
            if self.dpd_service == 'Pickup':
                parcelshop_tag = etree.SubElement(services_tag, 'parcelshop')
                shopaddress_tag = etree.SubElement(parcelshop_tag, 'shopaddress')
                etree.SubElement(shopaddress_tag, 'countryPrefix').text = 'FR'
                etree.SubElement(shopaddress_tag,
                                 'zipCode').text = receiver_add.zip or ''
                etree.SubElement(shopaddress_tag,
                                 'city').text = receiver_add.city or ''
                etree.SubElement(shopaddress_tag,
                                 'street').text = receiver_add.street or ''
                etree.SubElement(shopaddress_tag,
                                 'name').text = receiver_add.name or ''
                etree.SubElement(shopaddress_tag,
                                 'shopid').text = picking.sale_id.dpd_france_location_id.pudo_id if picking.sale_id.dpd_france_location_id else ''

        etree.SubElement(request, 'weight').text = '{}'.format(picking and picking.dpd_france_default_weight or '')

        etree.SubElement(request, 'referencenumber').text = '{}'.format(picking and picking.name)
        etree.SubElement(request, 'reference2').text = '{}'.format(picking and picking.sale_id and picking.sale_id.name)

        label_type = etree.SubElement(request, 'labelType')
        etree.SubElement(label_type, 'type').text = 'PDF'

        return etree.tostring(envelope)

    def dpd_fr_cancel_shipment(self, pickings):
        raise ValidationError(_('Cancel Service not provide by DPD France'))

    def dpd_fr_get_tracking_link(self, picking):
        return "https://www.dpd.com/fr/en/"
