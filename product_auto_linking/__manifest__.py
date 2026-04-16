# -*- coding: utf-8 -*-
{
    # App information
    'name': 'Smart Auto Related Products (Accessories & Alternatives)',
    'category': 'Website',
    'version': '18.0.0.0.1',
    'summary': """
    """,

    'license': 'OPL-1',
    'description': "",

    # Dependencies
    'depends': ['stock','sale','mrp'],

    # Views
    'data': [
        'data/product_rule.xml',
        'security/ir.model.access.csv',
        'views/product_template_view.xml',
        'views/product_brand_vts_view.xml',
        'views/res_config_setting_view.xml',
        'views/product_log_view.xml',
        'views/product_accessories_vts_view.xml',
    ],

    # Odoo Store Specific
    'images': [],

    # Author
    'author': 'Vraja Technologies',
    'website': 'http://www.vrajatechnologies.com',
    'maintainer': 'Vraja Technologies',
    'live_test_url': 'https://www.vrajatechnologies.com/contactus',

    # Technical
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': '',
    'currency': 'EUR',
}
