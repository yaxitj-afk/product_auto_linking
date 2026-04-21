# -*- coding: utf-8 -*-
{
    # App information
    'name': 'Auto Alternate & Accessory Product Management',
    'category': 'Website',
    'version': '18.0.1.0',
    'summary': """  
                The Smart Product Relationship Automation module transforms how alternative and accessory products are managed in Odoo by eliminating manual linking and replacing it with rule-based automation.
                Instead of manually assigning alternatives and accessories for every product, this module automatically builds product relationships using configurable business logic. It evaluates product attributes such as category, brand, tags, attributes, and real-time stock availability to intelligently identify the most relevant products.
                With flexible rule configuration, you can control exactly how products are matched — whether by shared attributes, same category, specific brands, or custom tagging strategies. The system ensures that only meaningful and available products are linked, avoiding irrelevant suggestions.
                The module continuously updates product relationships as data changes, ensuring that alternatives and accessories always remain accurate without requiring manual maintenance.
                To maintain full transparency and control, the module includes a detailed logging system that tracks all changes made to alternative and accessory products. Users can review what was added, removed, or updated for maintaining data integrity.
                This results in faster product setup, consistent data across your catalog, and improved sales opportunities through better cross-selling and substitution suggestions.
                Whether you're managing a large product catalog or scaling an eCommerce operation, this module brings structure, automation, and accountability to product linking in Odoo.
                Automate Alternative Products in Odoo
                Automate Accessory Products in Odoo
                Smart Product Linking for Odoo
                Rule-Based Product Recommendations
                Dynamic Alternative & Accessory Suggestions
                Stock-Based Product Recommendations
                Odoo Cross-Sell & Upsell Automation
                Auto Add Accessories in Odoo
                Auto Link Products in Odoo  
                Odoo Product Suggestion Engine
                """,

    'license': 'OPL-1',
    'description': "",

    # Dependencies
    'depends': ['stock', 'website_sale'],

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
