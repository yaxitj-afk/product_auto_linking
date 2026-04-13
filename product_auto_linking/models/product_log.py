from odoo import models, fields, api


class ProductRelationLog(models.Model):
    _name = 'product.log.vts'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product Log'
    _order = 'id DESC'

    name = fields.Char("Name")

    relation_type = fields.Selection([
        ('alternative', 'Alternative Product'),
        ('accessory', 'Accessory Product')
    ], string="Relation Type")

    operation_type = fields.Selection([
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete')
    ], string="Operation")

    product_id = fields.Many2one('product.template', string="Main Product")

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id
    )

    log_line_ids = fields.One2many(
        'product.log.line.vts',
        'log_id',
        string="Log Lines",
        ondelete='cascade'
    )

    message = fields.Char("Message")

    create_date = fields.Datetime("Created On")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'product.log.vts'
            ) or '/'
        return super().create(vals)

    def generate_log(self, relation_type, operation_type, product, message=None):
        return self.create({
            'relation_type': relation_type,
            'operation_type': operation_type,
            'product_id': product.id,
            'message': message,
        })


class ProductRelationLogLine(models.Model):
    _name = 'product.log.line.vts'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Product Relation Log Line'
    _order = 'id DESC'

    log_id = fields.Many2one(
        'product.log.vts',
        string="Log",
        ondelete='cascade'
    )

    relation_type = fields.Selection([
        ('alternative', 'Alternative'),
        ('accessory', 'Accessory')
    ])

    operation_type = fields.Selection([
        ('add', 'Add'),
        ('remove', 'Remove')
    ])

    product_id = fields.Many2one(
        'product.template',
        string="Main Product"
    )

    related_product_id = fields.Many2one(
        'product.template',
        string="Related Product"
    )

    is_error = fields.Boolean("Error")

    message = fields.Char("Message")

    create_date = fields.Datetime("Created On")

    def create_log_line(self,log,relation_type,operation_type,product,related_product,message=None,is_error=False):
        print('hello')
        return self.create({
            'log_id': log.id,
            'relation_type': relation_type,
            'operation_type': operation_type,
            'product_id': product.id,
            'related_product_id': related_product.id,
            'message': message,
            'is_error': is_error,
        })