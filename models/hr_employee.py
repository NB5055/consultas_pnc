from openerp import models, fields, api


class HrEmloyee(models.Model):
    _inherit = 'hr.employee'

    def select_items(self):
        return [(str(self.env.ref('consultas_pnc.group_categoria_a').id), 'Categoria A'),
                (str(self.env.ref('consultas_pnc.group_categoria_b').id), 'Categoria B'),
                (str(self.env.ref('consultas_pnc.group_categoria_c').id), 'Categoria C')]

    programa_id = fields.Many2one("programa.programa", string="Programa")
    provincia_id = fields.Many2one("region.provincia", string="Provincia",
                                help="Provincia a que Pertenece")
    user_name = fields.Char(string="User")
    user_password = fields.Char(string="Password")
    category_group = fields.Selection(lambda self: self.select_items(), string="Group")

    @api.model
    def create(self, vals):
        employee_id = super(HrEmloyee, self).create(vals)
        if employee_id.name and (employee_id.user_name or employee_id.work_email):
            user_id = self.env['res.users'].create({'name': employee_id.name,
                                                    'login': employee_id.user_name or employee_id.work_email,
                                                    'password': employee_id.user_password or ''})
            if employee_id.category_group:
                user_id.groups_id = [(4, int(employee_id.category_group))]
            user_id.partner_id.email = employee_id.work_email
            employee_id.user_id = user_id
        employee_id.user_password = ""
        return employee_id

    @api.multi
    def write(self, vals):
        employee_id = super(HrEmloyee, self).write(vals)
        if self.user_id:
            if 'user_password' in vals:
                self.user_id.password = vals.get('user_password')

            if 'category_group' in vals:
                self.user_id.groups_id = [(2, self.env.ref('consultas_pnc.group_categoria_a').id)]
                self.user_id.groups_id = [(2, self.env.ref('consultas_pnc.group_categoria_b').id)]
                self.user_id.groups_id = [(2, self.env.ref('consultas_pnc.group_categoria_c').id)]
                self.user_id.groups_id = [(4, int(vals.get('category_group')))]

            if 'user_name' in vals:
                self.user_id.login = vals.get('user_name')
        else:
            if self.user_name:
                user_id = self.env['res.users'].create({'name': self.name,
                                                    'login': self.user_name,
                                                    'password': self.user_password})
                if self.category_group:
                    user_id.groups_id = [(4, int(self.category_group))]
                user_id.partner_id.email = self.work_email
                self.user_id = user_id
        super(HrEmloyee, self).write({'user_password':""})
        return employee_id