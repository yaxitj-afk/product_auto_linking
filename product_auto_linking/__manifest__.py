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
    'depends': ['base','stock','sale',],

    # Views
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_view.xml',
        'views/product_brand_vts_view.xml',
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
