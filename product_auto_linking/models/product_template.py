from odoo import models, api, fields
import json
class ProductTemplate(models.Model):
    _inherit = 'product.template'

    product_brand_id = fields.Many2one(
        'product.brand.vts',
        string="Product Brand",
        help="Name of the brand"
    )

    def create_product_logs(self, log,relation_type,operation_type,product,related_product,message):
        self.env['product.log.line.vts'].sudo().create_log_line(log,relation_type,operation_type,product,related_product,message)

    @api.constrains('list_price', 'categ_id','attribute_line_ids')
    def _compute_alternative_products(self):
        alternate_rule = self.env['ir.config_parameter'].sudo().get_param(
            'product_auto_linking.alternative_product_rule_ids', '[]'
        )
        alternate_rule_ids = json.loads(alternate_rule)
        alternate_rule_records = self.env['product.rule.vts'].browse(alternate_rule_ids)
        alternate_rule_codes = alternate_rule_records.mapped('code')

        for product in self:
            old_alternatives = product.alternative_product_ids
            # Default Domain
            domain = [
                ('id', '!=', product.id),
                ('categ_id', '=', product.categ_id.id),
                ('sale_ok', '=', True),
                ('active', '=', True),
            ]
            # Price
            if 'price' in alternate_rule_codes:
                min_price = product.list_price * 0.9
                max_price = product.list_price * 1.1
                domain += [
                    ('list_price', '>=', min_price),
                    ('list_price', '<=', max_price)
                ]

            #Brand
            if 'brand' in alternate_rule_codes:
                if product.product_brand_id:
                    domain.append(('product_brand_id', '=', product.product_brand_id.id))

            #Attributes
            if 'attributes' in alternate_rule_codes:
                attr_value_ids = product.attribute_line_ids.mapped('value_ids').ids
                if attr_value_ids:
                    domain.append(('attribute_line_ids.value_ids', 'in', attr_value_ids))

            #Stock
            if 'in_stock' in alternate_rule_codes:
                domain.append(('qty_available', '>', 0))

            # TAGS
            if 'tags' in alternate_rule_codes:
                if product.product_tag_ids:
                    domain.append(('product_tag_ids', 'in', product.product_tag_ids.ids))

            alternative_products = self.env['product.template'].search(domain)

            if not alternative_products:
                product.with_context(skip_alternative_sync=True).write({
                    'alternative_product_ids': [(5, 0, 0)]
                })
                continue

            alternative_products = alternative_products.sorted(
                key=lambda p: abs((p.list_price) - (product.list_price))
            )[:10]

            product.with_context(skip_alternative_sync=True).write({
                'alternative_product_ids': [(6, 0, alternative_products.ids)]
            })

            new_alternatives = product.alternative_product_ids
            if new_alternatives:
                log_id = self.env['product.log.vts'].generate_log(relation_type='alternative', operation_type='update',
                                                              product=product,message='Alternative products updated')
                if old_alternatives:
                    added = new_alternatives - old_alternatives
                    removed = old_alternatives - new_alternatives
                else:
                    added = new_alternatives
                    removed = []

                # ✅ MAIN PRODUCT LOG
                if added or removed:
                    for alt in added:
                        self.create_product_logs(log_id,relation_type='alternative',operation_type='add',product=product,related_product=alt,message=f"Product {alt.display_name} added as alternative product")

                    for alt in removed:
                        self.create_product_logs(log_id,relation_type='alternative',operation_type='remove',product=product,related_product=alt,message=f"Product {alt.display_name} removed from alternative product")

                # ✅ REVERSE SYNC + LOG
                for alt in added:
                    if product.id not in alt.alternative_product_ids.ids:
                        alt.with_context(skip_alternative_sync=True).write({
                            'alternative_product_ids': [(4, product.id)]
                        })
                        self.create_product_logs(log_id,relation_type='alternative',operation_type='add',product=alt,related_product=product,message=f"Product {product.display_name} added as alternative product")


                for alt in removed:
                    if product.id in alt.alternative_product_ids.ids:
                        remaining_ids = alt.alternative_product_ids.ids.copy()
                        remaining_ids.remove(product.id)

                        alt.with_context(skip_alternative_sync=True).write({
                            'alternative_product_ids': [(6, 0, remaining_ids)]
                        })
                        self.create_product_logs(log_id,relation_type='alternative',operation_type='remove',product=alt,related_product=product,message=f"Product {product.display_name} removed from alternative product")


    # ----------------------------------------------------------------------------------------------------------
    #                         Product Accessories Code
    # ----------------------------------------------------------------------------------------------------------

    def _apply_accessory_rules(self, product, rules, domain):
        """
        Apply dynamic accessory rules on domain
        """
        for rule in rules:

            if rule.code == 'brand':
                if product.product_brand_id:
                    domain.append(('product_brand_id', '=', product.product_brand_id.id))

            if rule.code == 'tags':
                if product.product_tag_ids:
                    domain.append(('product_tag_ids', 'in', product.product_tag_ids.ids))

            if rule.code == 'in_stock':
                domain.append(('qty_available', '>', 0))

            if rule.code == 'bom':
                boms = self.env['mrp.bom'].search([
                    ('product_tmpl_id', '=', product.id),
                ])
                accessory_ids = boms.mapped('bom_line_ids.product_tmpl_id').ids

                if accessory_ids:
                    domain.append(('id', 'in', accessory_ids))

        return domain

    @api.constrains('list_price', 'categ_id', 'attribute_line_ids')
    def _compute_product_accessories(self):
        accessory_rule_obj = self.env['product.accessory.vts']
        accessory_rules = accessory_rule_obj.search([])

        for product in self:
            matched_accessory_rule = False

            for rule in accessory_rules:
                if rule.category_id.id == product.categ_id.id:
                    matched_accessory_rule = rule
                    break

            if not matched_accessory_rule:
                continue

            accessory_category_ids = matched_accessory_rule.accessory_category_ids.ids

            if not accessory_category_ids:
                product.with_context(skip_accessory_sync=True).write({
                    'accessory_product_ids': [(5, 0, 0)]
                })
                continue

            domain = [
                ('categ_id', 'in', accessory_category_ids),
                ('sale_ok', '=', True),
                ('active', '=', True),
                ('id', '!=', product.id)
            ]

            domain = self._apply_accessory_rules(product,matched_accessory_rule.accessory_product_rule_ids,domain)

            accessory_products = self.env['product.template'].search(domain)
            accessory_product_variants = accessory_products.mapped('product_variant_id').exists()
            old_accessories = product.accessory_product_ids.product_tmpl_id.ids

            product.with_context(skip_accessory_sync=True).write({
                'accessory_product_ids': [(6, 0, accessory_product_variants.ids)]
            })

            new_accessories = accessory_products.ids
            product_added = list(set(new_accessories) - set(old_accessories))
            product_removed = list(set(old_accessories) - set(new_accessories))
            if product_added or product_removed:
                log_id = self.env['product.log.vts'].generate_log(relation_type='accessory',operation_type='update',product=product,
                    message='Accessory products updated')

                for acc in self.env['product.template'].browse(product_added):
                    self.create_product_logs(log_id,'accessory','add',product,acc,
                        message=f"Product {acc.display_name} added as accessory product")

                for acc in self.env['product.template'].browse(product_removed):
                    self.create_product_logs(log_id,'accessory','remove',product,acc,
                        message=f"Product {acc.display_name} removed from accessory product")


    # def _cron_auto_update_alt_acc_of_product(self):
    #     for rec in self:
    #         rec._compute_alternative_products()
    #         rec._compute_product_accessories()


    # def _compute_product_accessories(self):
    #     accessory_rule_obj = self.env['product.accessory.vts']
    #     accessory_rules = accessory_rule_obj.search([])
    #
    #     for product in self:
    #         matched_accessory_rule = False
    #
    #         for rule in accessory_rules:
    #             if rule.category_id.id == product.categ_id.id:
    #                 matched_accessory_rule = rule
    #                 break
    #
    #         if not matched_accessory_rule:
    #             continue
    #
    #         accessory_category_ids = matched_accessory_rule.accessory_category_ids.ids
    #
    #         if not accessory_category_ids:
    #             product.with_context(skip_accessory_sync=True).write({
    #                 'accessory_product_ids': [(5, 0, 0)]
    #             })
    #             continue
    #
    #         accessory_products = self.env['product.template'].search([
    #             ('categ_id', 'in', accessory_category_ids),
    #             ('sale_ok', '=', True),
    #             ('active', '=', True),
    #             ('id', '!=', product.id)
    #         ])
    #
    #         accessory_product_variants = accessory_products.mapped('product_variant_id').exists()
    #         old_accessories = product.accessory_product_ids.ids
    #
    #         product.with_context(skip_accessory_sync=True).write({
    #             'accessory_product_ids': [(6, 0, accessory_product_variants.ids)]
    #         })
    #
    #         new_accessories = accessory_products.ids
    #
    #         added = new_accessories - old_accessories
    #         removed = old_accessories - new_accessories
    #
    #         log_id = self.env['product.log.vts'].generate_log(relation_type='accessory',operation_type='update',
    #             product=product,message='Accessory products updated')
    #
    #         for acc in added:
    #             self.create_product_logs(log_id,relation_type='accessory',operation_type='add',product=product,related_product=acc,
    #                                      message=f"Product {acc.display_name} added as accessory product")
    #
    #         for acc in removed:
    #             self.create_product_logs(log_id,relation_type='accessory',operation_type='remove',product=product,related_product=acc,
    #                 message=f"Product {acc.display_name} removed from accessory product")
    #
    #         for acc in removed:
    #             if product.id in acc.accessory_product_ids.ids:
    #                 remaining_ids = acc.accessory_product_ids.ids.copy()
    #                 remaining_ids.remove(product.id)
    #                 acc.with_context(skip_accessory_sync=True).write({'accessory_product_ids': [(6, 0, remaining_ids)]})
    #                 self.create_product_logs(log_id,relation_type='accessory',operation_type='remove',product=acc,related_product=product,
    #                     message=f"Product {product.display_name} removed from accessory product")
