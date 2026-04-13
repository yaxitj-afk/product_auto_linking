from odoo import models, api, fields
from collections import defaultdict

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one(
        'product.brand.vts',
        string="Product Brand",
        help="Name of the brand"
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # records._compute_alternative_products()
        records._compute_product_accessories()
        return records

    def write(self, vals):
        res = super().write(vals)

        # if not self.env.context.get('skip_alternative_sync'):
        #     if any(field in vals for field in ['list_price','categ_id','attribute_line_ids',]):
        #         self._compute_alternative_products()

        if not self.env.context.get('skip_accessory_sync'):
            if any(field in vals for field in ['categ_id','attribute_line_ids','product_brand_id','list_price']):
                self._compute_product_accessories()
        return res

# ==================================================================================================================


    def create_product_logs(self, log,operation_type,product,related_product,message):
        self.env['product.log.line.vts'].sudo().create_log_line(log,'alternative',operation_type,product,related_product,message)

    def _compute_alternative_products(self):
        rule = self.env['ir.config_parameter'].sudo().get_param(
            'product_auto_linking.alternative_product_rule', default='category'
        )

        for product in self:
            old_alternatives = product.alternative_product_ids

            domain = [
                ('id', '!=', product.id),
                ('categ_id', '=', product.categ_id.id),
                ('sale_ok', '=', True),
                ('active', '=', True),
            ]

            if rule == 'price':
                min_price = product.list_price * 0.9
                max_price = product.list_price * 1.1
                domain += [
                    ('list_price', '>=', min_price),
                    ('list_price', '<=', max_price)
                ]

            elif rule == 'brand':
                if product.product_brand_id:
                    domain.append(('product_brand_id', '=', product.product_brand_id.id))

            elif rule == 'attributes':
                attr_value_ids = product.attribute_line_ids.mapped('value_ids').ids
                if attr_value_ids:
                    domain.append(('attribute_line_ids.value_ids', 'in', attr_value_ids))

            alternative_products = self.env['product.template'].search(domain)

            # alternative_products = alternative_products.filtered(
            #     lambda p: any(v.qty_available > 0 for v in p.product_variant_ids)
            # )

            alternative_products = alternative_products.sorted(
                key=lambda p: abs((p.list_price) - (product.list_price))
            )[:10]

            product.with_context(skip_alternative_sync=True).write({
                'alternative_product_ids': [(6, 0, alternative_products.ids)]
            })

            new_alternatives = product.alternative_product_ids

            added = new_alternatives - old_alternatives
            removed = old_alternatives - new_alternatives

            # ✅ MAIN PRODUCT LOG
            log_id = self.env['product.log.vts'].generate_log(relation_type='alternative',operation_type='update',product=product,message='Alternative products updated')

            if added or removed:
                for alt in added:
                    self.create_product_logs(log_id,operation_type='add',product=product,related_product=alt,message=f"Product {alt.display_name} added as alternative product")

                for alt in removed:
                    self.create_product_logs(log_id,operation_type='remove',product=product,related_product=alt,message=f"Product {alt.display_name} removed from alternative product")

            # ✅ REVERSE SYNC + LOG
            for alt in added:
                if product.id not in alt.alternative_product_ids.ids:
                    alt.with_context(skip_alternative_sync=True).write({
                        'alternative_product_ids': [(4, product.id)]
                    })
                    self.create_product_logs(log_id,operation_type='add',product=alt,related_product=product,message=f"Product {product.display_name} added as alternative product")


            for alt in removed:
                if product.id in alt.alternative_product_ids.ids:
                    remaining_ids = alt.alternative_product_ids.ids.copy()
                    remaining_ids.remove(product.id)

                    alt.with_context(skip_alternative_sync=True).write({
                        'alternative_product_ids': [(6, 0, remaining_ids)]
                    })
                    self.create_product_logs(log_id,operation_type='remove',product=alt,related_product=product,message=f"Product {product.display_name} removed from alternative product")

    # ----------------------------------------------------------------------------------------------------------
    #                         Product Accessories Code
    # ----------------------------------------------------------------------------------------------------------

    def _compute_product_accessories(self):

        SaleLine = self.env['sale.order.line']
        BomLine = self.env['mrp.bom.line']

        rule = self.env['ir.config_parameter'].sudo().get_param(
            'product_auto_linking.accessory_product_rule'
        )

        for product in self:

            score_map = defaultdict(int)

            # 1. BOM RULE
            if rule == 'bom':

                bom_lines = BomLine.search([
                    ('product_tmpl_id', '=', product.id)
                ])

                for line in bom_lines:
                    acc = line.product_id.product_tmpl_id
                    if acc and acc.id != product.id:
                        score_map[acc.id] += 100

            # 2. SALES RULE
            if rule == 'sales':

                sale_lines = SaleLine.search([
                    ('product_template_id', '=', product.id)
                ])

                orders = sale_lines.mapped('order_id')

                if orders:
                    co_lines = SaleLine.search([
                        ('order_id', 'in', orders.ids)
                    ])

                    for line in co_lines:
                        acc = line.product_template_id
                        if acc and acc.id != product.id:
                            score_map[acc.id] += 50

            # 3. TAGS RULE
            if rule == 'attributes':

                tag_ids = product.attribute_line_ids.mapped('value_ids.id')
                if tag_ids:
                    tag_products = self.search([
                        ('attribute_line_ids.value_ids', 'in', tag_ids),
                        ('id', '!=', product.id),
                    ])

                    for acc in tag_products:
                        score_map[acc.id] += 20

            # 4. CATEGORY RULE
            if rule == 'category':

                category_products = self.search([
                    ('categ_id', '=', product.categ_id.id),
                    ('id', '!=', product.id),
                    ('sale_ok', '=', True),
                    ('active', '=', True),
                ])

                for acc in category_products:
                    score_map[acc.id] += 10

            # FINAL RESULT
            sorted_products = sorted(score_map.items(),key=lambda x: x[1],reverse=True)[:10]
            accessory_products = self.browse([pid for pid, score in sorted_products])

            # WRITE RESULT
            product.with_context(skip_accessory_sync=True).write({'accessory_product_ids': [(6, 0, accessory_products.ids)]})