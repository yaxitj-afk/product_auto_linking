from odoo import fields, models,api
import json


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    main_rule_ids = fields.Many2many(
        'product.rule.vts',
        'config_setting_main_rel',
        string="Alternative Rules",
        domain=[('code', 'in', ['brand', 'category'])]
    )

    other_rule_ids = fields.Many2many(
        'product.rule.vts',
        'config_setting_other_rel',
        string="Other Rules",
        domain=[('code', 'not in', ['brand', 'category'])]
    )

    min_price_range = fields.Float(
        string="Min Price Deviation (%)",
        default=10.0
    )

    max_price_range = fields.Float(
        string="Max Price Deviation (%)",
        default=10.0
    )

    show_price_range = fields.Boolean(compute="_compute_show_price_range")

    @api.depends('other_rule_ids')
    def _compute_show_price_range(self):
        for rec in self:
            rec.show_price_range = 'price' in rec.other_rule_ids.mapped('code')

    def set_values(self):
        """Save the values to ir.config_parameter"""
        super().set_values()
        ICP = self.env['ir.config_parameter'].sudo()

        ICP.set_param('product_link_automation.main_rule_ids',json.dumps(self.main_rule_ids.ids))
        ICP.set_param('product_link_automation.other_rule_ids',json.dumps(self.other_rule_ids.ids))
        ICP.set_param('product_link_automation.min_price_range',self.min_price_range)
        ICP.set_param('product_link_automation.max_price_range',self.max_price_range)

    def get_values(self):
        res = super().get_values()
        ICP = self.env['ir.config_parameter'].sudo()

        main_param = ICP.get_param('product_link_automation.main_rule_ids', '[]') or '[]'
        other_param = ICP.get_param('product_link_automation.other_rule_ids', '[]') or '[]'

        res.update(
            main_rule_ids=[(6, 0, json.loads(main_param))],
            other_rule_ids=[(6, 0, json.loads(other_param))],
            min_price_range=float(ICP.get_param('product_link_automation.min_price_range', 10.0) or 10.0),
            max_price_range=float(ICP.get_param('product_link_automation.max_price_range', 10.0) or 10.0),
        )

        return res