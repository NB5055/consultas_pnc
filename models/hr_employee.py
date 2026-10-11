from odoo import api, fields, models
from odoo.fields import Command

CATEGORY_GROUPS = {
    'a': 'consultas_pnc.group_categoria_a',
    'b': 'consultas_pnc.group_categoria_b',
    'c': 'consultas_pnc.group_categoria_c',
}


class HrEmloyee(models.Model):
    _inherit = 'hr.employee'

    programa_id = fields.Many2one("programa.programa", string="Programa")
    provincia_id = fields.Many2one("region.provincia", string="Provincia",
                                   help="Provincia a que Pertenece")
    user_name = fields.Char(string="User Name", groups="hr.group_hr_user")
    user_password = fields.Char(string="Password", store=False, groups="hr.group_hr_user")
    category_group = fields.Selection([('a', 'Categoria A'),
                                       ('b', 'Categoria B'),
                                       ('c', 'Categoria C')], string="Group", groups="hr.group_hr_user")

    def _create_category_user(self, login, password):
        self.ensure_one()
        vals = {'name': self.name, 'login': login}
        if password:
            vals['password'] = password
        user_id = self.env['res.users'].create(vals)
        if self.category_group:
            user_id.group_ids = [Command.link(self.env.ref(CATEGORY_GROUPS[self.category_group]).id)]
        user_id.partner_id.email = self.work_email
        self.user_id = user_id

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [dict(vals) for vals in vals_list]
        passwords = [vals.pop('user_password', False) for vals in vals_list]
        employees = super(HrEmloyee, self.with_context(pnc_user_sync=False)).create(vals_list)
        employees = employees.with_context(pnc_user_sync=True)
        for employee_id, password in zip(employees, passwords):
            if not employee_id.user_id and employee_id.name and (employee_id.user_name or employee_id.work_email):
                employee_id._create_category_user(employee_id.user_name or employee_id.work_email, password)
        return employees

    def write(self, vals):
        vals = dict(vals)
        password = vals.pop('user_password', False)
        res = super().write(vals)
        if not self.env.context.get('pnc_user_sync', True):
            return res
        for employee_id in self:
            if employee_id.user_id:
                if password:
                    employee_id.user_id.password = password

                if 'category_group' in vals:
                    commands = [Command.unlink(self.env.ref(xmlid).id) for xmlid in CATEGORY_GROUPS.values()]
                    if vals.get('category_group'):
                        commands.append(Command.link(self.env.ref(CATEGORY_GROUPS[vals['category_group']]).id))
                    employee_id.user_id.group_ids = commands

                if vals.get('user_name'):
                    employee_id.user_id.login = vals['user_name']
            elif employee_id.user_name:
                employee_id._create_category_user(employee_id.user_name, password)
        return res


class HrEmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    programa_id = fields.Many2one("programa.programa", readonly=True)
    provincia_id = fields.Many2one("region.provincia", readonly=True)
