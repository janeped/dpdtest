import requests
import logging
from odoo.exceptions import ValidationError
from .dpd_response import Response

_logger = logging.getLogger("DPD Benelux")


class DPDFranceRequest():

    def send_request(self, request_data=False, url=False):
        headers = {
            'SOAPAction': "http://www.cargonet.software/CreateShipmentWithLabels",
            'Content-Type': "text/xml; charset='utf-8'"
        }
        try:
            _logger.info("::: Send POST Request To {}".format(url))
            _logger.info("::: Request Data {}".format(request_data))
            response_data = requests.post(url=url, headers=headers, data=request_data)
            if response_data.status_code in [200, 201]:
                _logger.info("::: Successfully response from {}".format(url))
                _logger.info("::: Response Data {}".format(response_data.text))
                response_data = Response(response_data)
                return response_data.dict()
            else:
                raise ValidationError(response_data.text or request_data)
        except Exception as error:
            raise ValidationError(error)