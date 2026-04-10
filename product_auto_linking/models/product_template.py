from odoo import models, api, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one(
        'product.brand.vts',
        string="Product brand",
        help="Name of the brand"
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._compute_alternative_products()
        return records

    def write(self, vals):
        res = super().write(vals)

        if not self.env.context.get('skip_alternative_sync'):
            if any(field in vals for field in ['list_price','categ_id','attribute_line_ids',]):
                self._compute_alternative_products()
        return res

    def _compute_alternative_products(self):
        for product in self:

            base_price = product.list_price or 0.0
            min_price = base_price * 0.8
            max_price = base_price * 1.2

            domain = [
                # same category
                ('categ_id', '=', product.categ_id.id),
                ('id', '!=', product.id),
                ('active', '=', True),

                # price range
                ('list_price', '>=', min_price),
                ('list_price', '<=', max_price),
                ('sale_ok', '=', True),
            ]

            alternative_products = self.env['product.template'].search(domain)

            # quantity available in stock
            alternative_products = alternative_products.filtered(
                lambda p: any(variant.qty_available > 0 for variant in p.product_variant_ids)
            )

            # Attributes and its value checking
            alternative_products = alternative_products.filtered(
                lambda p: p.attribute_line_ids
            )

            if product.attribute_line_ids:
                alternative_products = alternative_products.filtered(
                    lambda p: any(
                        line.attribute_id.id in p.attribute_line_ids.mapped('attribute_id').ids
                        and any(
                            val.id in p.attribute_line_ids.filtered(
                                lambda l: l.attribute_id.id == line.attribute_id.id
                            ).mapped('value_ids').ids
                            for val in line.value_ids
                        )
                        for line in product.attribute_line_ids
                    )
                )

            alternative_products = alternative_products.sorted(
                key=lambda p: abs((p.list_price or 0.0) - base_price)
            )[:10]

            if alternative_products:
                product.with_context(skip_alternative_sync=True).write({
                    'alternative_product_ids': [(6, 0, alternative_products.ids)]
                })

                for alt in alternative_products:
                    existing = set(alt.alternative_product_ids.ids)
                    updated = list(existing | {product.id})

                    alt.with_context(skip_alternative_sync=True).write({
                        'alternative_product_ids': [(6, 0, updated)]
                    })