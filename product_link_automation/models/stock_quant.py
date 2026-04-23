from odoo import models

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    def write(self, vals):
        products = self.mapped('product_id.product_tmpl_id')

        res = super().write(vals)

        if any(field in vals for field in ['quantity', 'reserved_quantity']):
            if products:
                products._compute_alternative_products()
                products._compute_product_accessories()

        return res