# -*- coding: utf-8 -*-pack
{
    # App information
    'name': 'DPD France Shipping Integration',
    'category': 'Website',
    'version': '15.0.26.09.22',
    'summary': """Integrate & Manage DPD France shipping operations from Odoo by using Odoo DPD France Integration.Export Order While Validate Delivery Order.Import Tracking From DPD France to odoo.Generate Label in odoo.We are providing following modules odoo shipping connector,gls,mrw,colissimo,dbschenker.""",
    'description': """""",
    'depends': ['delivery'],
    'live_test_url': 'http://www.vrajatechnologies.com/contactus',
    'data': [
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/stock_picking.xml',
        'views/sale_view.xml',
        'views/delivery_carrier_view.xml'
    ],
    'images': ['static/description/cover.jpg'],
    'author': 'Vraja Technologies',
    'maintainer': 'Vraja Technologies',
    'website': 'www.vrajatechnologies.com',
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': "149",
    'currency': 'EUR',
    'license': 'OPL-1',
}
#Version Log
#15.0.26.09.22 initial version

