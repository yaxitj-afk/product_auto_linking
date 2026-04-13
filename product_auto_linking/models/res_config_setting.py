from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    alternative_product_rule = fields.Selection([
        # ('category', 'Same Category'),
        ('price', 'Similar Price'),
        ('brand', 'Same Brand'),
        ('attributes', 'Same Attributes'),
    ], string="Alternative Product Rule", config_parameter='product_auto_linking.alternative_product_rule')

    accessory_product_rule = fields.Selection([
        ('category', 'Same Category Accessories'),
        ('bom', 'BOM Based Accessories'),
        ('sales', 'Frequently Bought Together'),
        ('attributes', 'Same Attributes')
    ], string="Accessory Product Rule",config_parameter='product_auto_linking.accessory_product_rule')