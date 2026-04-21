from odoo import models, fields
import json

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    alternative_product_rule_ids = fields.Many2many(
        'product.rule.vts',
        string="Alternate Product Rule"
    )

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param('product_link_automation.alternative_product_rule_ids',
            json.dumps(self.alternative_product_rule_ids.ids))
    #
    def get_values(self):
        res = super().get_values()
        param = self.env['ir.config_parameter'].sudo().get_param('product_link_automation.alternative_product_rule_ids','[]')
        ids = json.loads(param)
        res.update(alternative_product_rule_ids=[(6, 0, ids)])
        return res