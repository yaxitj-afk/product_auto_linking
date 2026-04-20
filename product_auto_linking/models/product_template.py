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

        # ----------------------------------------------------------------------------------------------------------
        #                         Product Alternate Code
        # ----------------------------------------------------------------------------------------------------------

    def _filter_by_attribute_match(self, product, alternative_products):
        product_attr_map = {}

        for line in product.attribute_line_ids:
            product_attr_map[line.attribute_id.id] = set(line.value_ids.ids)

        filtered_products = self.env['product.template']
        if not product_attr_map:
            return filtered_products

        total_attributes = len(product_attr_map)
        required_match = max(1, round(total_attributes * 0.5))

        for alternative_product in alternative_products:
            matched_attribute_count = 0
            for line in alternative_product.attribute_line_ids:
                attr_id = line.attribute_id.id
                if attr_id in product_attr_map:

                    product_values = product_attr_map[attr_id]
                    alternative_values = set(line.value_ids.ids)

                    if product_values & alternative_values:
                        matched_attribute_count += 1
            if matched_attribute_count >= required_match:
                filtered_products |= alternative_product

        return filtered_products

    @api.constrains('list_price', 'categ_id','attribute_line_ids','product_brand_id','product_tag_ids','company_id')
    def _compute_alternative_products(self):
        alternate_rule = self.env['ir.config_parameter'].sudo().get_param(
            'product_auto_linking.alternative_product_rule_ids', '[]'
        )
        alternate_rule_ids = json.loads(alternate_rule)

        alternate_rule_records = self.env['product.rule.vts'].browse(alternate_rule_ids)
        alternate_rule_codes = alternate_rule_records.mapped('code')

        for product in self:
            old_alternatives = product.alternative_product_ids
            #Default Domain
            domain = [
                ('id', '!=', product.id),
                ('categ_id', '=', product.categ_id.id),
                ('sale_ok', '=', True),
                ('active', '=', True),
                ('company_id', '=', product.company_id.id)
            ]
            #Price
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

            #Stock
            if 'in_stock' in alternate_rule_codes:
                domain.append(('qty_available', '>', 0))

            #TAGS
            if 'tags' in alternate_rule_codes:
                if product.product_tag_ids:
                    domain.append(('product_tag_ids', 'in', product.product_tag_ids.ids))

            alternative_products = self.env['product.template'].search(domain)

            #Apply attribute strict filtering
            if 'attributes' in alternate_rule_codes and alternative_products:
                filtered_products = self._filter_by_attribute_match(
                    product, alternative_products)
                if filtered_products:
                    alternative_products = filtered_products
                else:
                    alternative_products = self.env['product.template']

            product.with_context(skip_alternative_sync=True).write({
                'alternative_product_ids': [(6, 0, alternative_products.ids)]
            })

            new_alternatives = product.alternative_product_ids
            if old_alternatives:
                added = new_alternatives - old_alternatives
                removed = old_alternatives - new_alternatives
            else:
                added = new_alternatives
                removed = []

            #MAIN PRODUCT LOG
            if added or removed:
                log_id = self.env['product.log.vts'].generate_log(relation_type='alternative', operation_type='update',
                                                                  product=product,message='Alternative products updated')
                for alt in added:
                    self.create_product_logs(log_id,relation_type='alternative',operation_type='add',product=product,related_product=alt,message=f"Product {alt.display_name} added as alternative product")

                    #REVERSE SYNC + LOG
                    if product.id not in alt.alternative_product_ids.ids:
                        alt.with_context(skip_alternative_sync=True).write({
                            'alternative_product_ids': [(4, product.id)]
                        })
                        self.create_product_logs(log_id, relation_type='alternative', operation_type='add', product=alt,
                                                 related_product=product,
                                               message=f"Product {product.display_name} added as alternative product")

                for alt in removed:
                    self.create_product_logs(log_id,relation_type='alternative',operation_type='remove',product=product,related_product=alt,message=f"Product {alt.display_name} removed from alternative product")

                    #REVERSE SYNC + LOG
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

        return domain

    @api.constrains('list_price', 'categ_id', 'attribute_line_ids','product_brand_id','product_tag_ids','company_id')
    def _compute_product_accessories(self):
        accessory_rules = self.env['product.accessory.vts'].search([])

        for product in self:
            matched_accessory_rule = False

            for rule in accessory_rules:
                if rule.category_id.id == product.categ_id.id:
                    matched_accessory_rule = rule
                    break

            if not matched_accessory_rule:
                product._update_product_accessory(product,accessory_rules)
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
                ('id', '!=', product.id),
                ('company_id', '=', product.company_id.id)
            ]

            domain = self._apply_accessory_rules(product,matched_accessory_rule.accessory_product_rule_ids,domain)

            accessory_products = self.env['product.template'].sudo().search(domain)
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
                    linked_products = self.env['product.template'].search([
                        ('accessory_product_ids.product_tmpl_id', '=', acc.id)
                    ])

                    for linked in linked_products:
                        if acc.product_variant_id.id in linked.accessory_product_ids.ids:
                            linked.with_context(skip_accessory_sync=True).write({
                                'accessory_product_ids': [(3, acc.product_variant_id.id)]
                            })

                            self.create_product_logs(log_id,'accessory','remove',linked,acc,
                                message=f"Product {acc.display_name} removed from accessory product")

                    self.create_product_logs(log_id,'accessory','remove',product,acc,
                        message=f"Product {acc.display_name} removed from accessory product")



    def _update_product_accessory(self, product, rules):
        """
        product :- Accessories Product for updation on other product has accessories
        rule :-  rule set at the accessories categories based on main category an accessories category

        this method is used for updating
        """
        Product = self.env['product.template'].sudo()
        product_variant_id = product.product_variant_id.id
        #need at the time of duplicating the product from the action
        if not product.product_variant_id:
            return
        ########################

        main_products = Product.search([
            ('accessory_product_ids', 'in', product_variant_id),
            ('company_id', '=', product.company_id.id)
        ])
        for rule in rules:
            if product.categ_id.id not in rule.accessory_category_ids.ids:
                continue
            domain = [('id', '!=', product.id),('categ_id','=',rule.category_id.id)]

            filter_domain = product._apply_accessory_rules(product,rule.accessory_product_rule_ids,domain)

            accessory_products = Product.search(filter_domain)
            allowed_ids = accessory_products.ids

            # Removing Accessories from the main product
            log_id = False
            if main_products or accessory_products:
                log_id = self.env['product.log.vts'].generate_log(relation_type='accessory', operation_type='update',
                                                                  product=product, message='Accessory products updated')
            for main in main_products:
                if main.id not in allowed_ids:
                    main.with_context(skip_accessory_sync=True).write({
                        'accessory_product_ids': [(3, product_variant_id)]})
                    self.create_product_logs(
                        log_id, 'accessory', 'remove', main, product,
                        message=f"Product {product.display_name} removed from accessory product")

            # Adding Accessories in the main product
            for acc in accessory_products:
                acc_ids = acc.accessory_product_ids.ids
                if product_variant_id not in acc_ids:
                    acc.with_context(skip_accessory_sync=True).write({
                        'accessory_product_ids': [(4, product_variant_id)]
                    })
                    self.create_product_logs(log_id, 'accessory', 'add', acc, product,
                        message=f"Product {product.display_name} added as accessory product")