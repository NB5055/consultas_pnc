from datetime import datetime

from odoo import api, fields, models


class consultas_consultas(models.Model):
    _name = "consultas.consultas"
    _description = "Registro de Consultas"
    _inherit = ["mail.thread"]
    _order = "fecha desc,name"

    name = fields.Many2one('ficha.paciente', string='Paciente / Participante', required=True)
    programa = fields.Many2one("programa.programa", string="Programa", tracking=True,
                               help="""Programa al que pertenece la Consulta""")
    edad = fields.Integer(string="Edad", related='name.edad', store=True, readonly=False, tracking=True)
    sexo = fields.Selection(string="Sexo", related='name.sexo', store=True, readonly=False, tracking=True)
    fecha = fields.Date(string="Fecha", default=fields.Date.context_today, required=True, tracking=True)
    diagnostico = fields.One2many("consultas.diagnostico.line", 'consulta_id',
                                  string="Diagnostico / Estado / Actividad", copy=True)
    referimiento = fields.One2many("consultas.referimiento.line", 'consulta_id',
                                   string="Referimiento", copy=True)
    tratamiento = fields.One2many("consultas.tratamiento.line", 'consulta_id',
                                  string="Tratamiento / Seguimiento / Referimiento", copy=True)
    employee_id = fields.Many2one("hr.employee", string="Médico / Profesor",
                                  required=True,
                                  default=lambda self: self._get_employee(), tracking=True)
    notes = fields.Text(string="Notas", tracking=True)

    @api.onchange('name')
    def set_programa(self):
        self.programa = self.name.programa

    @api.model
    def _get_employee(self):
        return self.env["hr.employee"].search([('user_id', '=', self.env.user.id)], limit=1)


class consultas_diagnostico(models.Model):
    _name = "consultas.diagnostico"
    _inherit = ['mail.thread']
    _description = "Diagnosticos"

    name = fields.Char(string="Diagnostico", tracking=True)


class consultas_diagnostico_line(models.Model):
    _name = "consultas.diagnostico.line"
    _inherit = ['mail.thread']
    _description = "Diagnosticos de Consultas y Pacientes"

    consulta_id = fields.Many2one("consultas.consultas",
                                  string="consulta_line_id", tracking=True)
    paciente_id = fields.Many2one("ficha.paciente", string="Paciente / Participante", tracking=True)
    name = fields.Many2one("consultas.diagnostico", string="Diagnostico", tracking=True)


class consultas_referimiento(models.Model):
    _name = "consultas.referimiento"
    _inherit = ['mail.thread']
    _description = "Referimientos"

    name = fields.Char(string="Referimiento", tracking=True)
    proyeccion = fields.One2many('consultas.proyeccion', 'referimiento_id',
                                 string="Proyeccion Anual")

    _unique_name = models.Constraint('unique(name)', "Referimiento Existe")


class consultas_referimiento_line(models.Model):
    _name = "consultas.referimiento.line"
    _inherit = ['mail.thread']
    _description = "Referimientos de Consultas"

    name = fields.Many2one("consultas.referimiento", ondelete="cascade", string="Referimiento", tracking=True)
    consulta_id = fields.Many2one("consultas.consultas", tracking=True)


class consultas_tratamiento(models.Model):
    _name = "consultas.tratamiento"
    _inherit = ['mail.thread']
    _description = "Tratamientos"

    name = fields.Char(string="Tratamiento", tracking=True)
    proyeccion = fields.One2many('consultas.proyeccion', 'tratamiento_id',
                                 string="Proyeccion Anual")
    programa_ids = fields.Many2many('programa.programa', string="Programas")
    discount_report = fields.Many2one('consultas.tratamiento', string="Descuenta a", tracking=True)
    category = fields.Selection([('rh', 'Rehabilitacion'), ('pc', 'Prevencion Ceguera')],
                                string="Categoria", tracking=True)

    _unique_name = models.Constraint('unique(name)', "Tratamiento Existe")


class consultas_tratamiento_line(models.Model):
    _name = "consultas.tratamiento.line"
    _description = "Tratamientos de Consultas"

    name = fields.Many2one("consultas.tratamiento", ondelete="cascade",
                           string="Tratamiento / Seguimiento")
    consulta_id = fields.Many2one("consultas.consultas", ondelete="cascade")
    paciente_id = fields.Many2one(related="consulta_id.name", store=True)
    employee_id = fields.Many2one(related="consulta_id.employee_id", store=True)
    programa = fields.Many2one(related="consulta_id.programa", store=True)
    notes = fields.Text(related="consulta_id.notes")

    edad = fields.Integer(related='consulta_id.edad', store=True)
    sexo = fields.Selection(related='consulta_id.sexo', store=True)
    fecha = fields.Date(related="consulta_id.fecha", store=True)
    tratamiento = fields.One2many(related="consulta_id.tratamiento")
    message_follower_ids = fields.One2many(related="consulta_id.message_follower_ids")
    message_ids = fields.One2many(related="consulta_id.message_ids")

    def show_consulta(self):
        return {
            'name': "Servicios o Atenciones",
            'view_mode': 'form,list',
            'res_model': 'consultas.consultas',
            'target': 'current',
            'views': [(False, 'form'), (False, 'list')],
            'type': 'ir.actions.act_window',
            'domain': [(1, '=', 1)],
        }


class consulta_proyeccion(models.Model):
    _name = "consultas.proyeccion"
    _inherit = ['mail.thread']
    _description = "Proyeccion Anual"

    tratamiento_id = fields.Many2one("consultas.tratamiento")
    referimiento_id = fields.Many2one("consultas.referimiento")
    proyeccion = fields.Integer(string="Proyeccion", required=True)
    programa = fields.Many2one("programa.programa", string="Programa", required=True)
    year = fields.Selection([(str(num), str(num)) for num in range(2000, (datetime.now().year) + 1)], string='Año',
                            required=True)

    _unique_name = models.Constraint("unique(tratamiento_id,year,programa)", "Proyeccion Existe")
