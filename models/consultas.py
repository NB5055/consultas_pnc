from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class consultas_consultas(models.Model):
    _name = "consultas.consultas"
    _description = "Registro de Consultas"
    _inherit = ["mail.thread"]
    _order = "fecha desc,id desc"

    name = fields.Many2one('ficha.paciente', string='Paciente / Participante', required=True, index=True)
    programa = fields.Many2one("programa.programa", string="Programa", tracking=True, index=True,
                               help="""Programa al que pertenece la Consulta""")
    edad = fields.Integer(string="Edad", compute='_compute_edad', inverse='_inverse_edad',
                          store=True, readonly=False, tracking=True,
                          help="Edad del paciente en la fecha de la consulta")
    sexo = fields.Selection(string="Sexo", related='name.sexo', store=True, readonly=False, tracking=True)
    fecha = fields.Date(string="Fecha", default=fields.Date.context_today, required=True, tracking=True,
                        index=True)
    diagnostico = fields.One2many("consultas.diagnostico.line", 'consulta_id',
                                  string="Diagnostico / Estado / Actividad", copy=True)
    referimiento = fields.One2many("consultas.referimiento.line", 'consulta_id',
                                   string="Referimiento", copy=True)
    tratamiento = fields.One2many("consultas.tratamiento.line", 'consulta_id',
                                  string="Tratamiento / Seguimiento / Referimiento", copy=True)
    employee_id = fields.Many2one("hr.employee", string="Médico / Profesor",
                                  required=True, index=True,
                                  default=lambda self: self._get_employee(), tracking=True)
    notes = fields.Text(string="Notas", tracking=True)

    @api.depends('name.birth_date', 'name.edad', 'fecha')
    def _compute_edad(self):
        for consulta in self:
            birth_date = consulta.name.birth_date
            if birth_date and consulta.fecha:
                consulta.edad = max(relativedelta(consulta.fecha, birth_date).years, 0)
            else:
                consulta.edad = consulta.name.edad

    def _inverse_edad(self):
        # Sin fecha de nacimiento, la edad digitada en la consulta es la de la ficha.
        for consulta in self:
            paciente = consulta.name
            if paciente and not paciente.birth_date and paciente.edad != consulta.edad:
                paciente.edad = consulta.edad

    @api.model_create_multi
    def create(self, vals_list):
        consultas = super().create(vals_list)
        cita = self.env['citas.citas'].browse(self.env.context.get('pnc_cita_id')).exists()
        if cita and len(consultas) == 1:
            cita.write({'consulta_id': consultas.id, 'state': 'atendida'})
        return consultas

    @api.onchange('name')
    def set_programa(self):
        cita = self.env['citas.citas'].browse(self.env.context.get('pnc_cita_id')).exists()
        if cita and cita.paciente_id == self.name:
            self.programa = cita.programa_id
        else:
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
    _description = "Diagnosticos de Consultas y Pacientes"

    consulta_id = fields.Many2one("consultas.consultas", string="consulta_line_id",
                                  ondelete='cascade', index=True)
    paciente_id = fields.Many2one("ficha.paciente", string="Paciente / Participante",
                                  ondelete='cascade', index=True)
    name = fields.Many2one("consultas.diagnostico", string="Diagnostico", ondelete='restrict')

    _check_parent = models.Constraint('check(consulta_id IS NOT NULL OR paciente_id IS NOT NULL)',
                                      "El diagnostico debe pertenecer a una consulta o a un paciente")


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
    _description = "Referimientos de Consultas"

    name = fields.Many2one("consultas.referimiento", ondelete="restrict", string="Referimiento",
                           required=True, index=True)
    consulta_id = fields.Many2one("consultas.consultas", required=True, ondelete='cascade', index=True)
    notas = fields.Char(string="Detalle")


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

    # restrict: borrar un tratamiento del catalogo no puede llevarse su historial
    name = fields.Many2one("consultas.tratamiento", ondelete="restrict", index=True,
                           string="Tratamiento / Seguimiento")
    consulta_id = fields.Many2one("consultas.consultas", required=True, ondelete="cascade", index=True)
    paciente_id = fields.Many2one(related="consulta_id.name", store=True, index=True)
    employee_id = fields.Many2one(related="consulta_id.employee_id", store=True, index=True)
    programa = fields.Many2one(related="consulta_id.programa", store=True, index=True)
    notes = fields.Text(related="consulta_id.notes")

    edad = fields.Integer(related='consulta_id.edad', store=True)
    sexo = fields.Selection(related='consulta_id.sexo', store=True)
    fecha = fields.Date(related="consulta_id.fecha", store=True, index=True)
    tratamiento = fields.One2many(related="consulta_id.tratamiento")
    message_follower_ids = fields.One2many(related="consulta_id.message_follower_ids")
    message_ids = fields.One2many(related="consulta_id.message_ids")

    def show_consulta(self):
        self.ensure_one()
        return {
            'name': "Servicios o Atenciones",
            'res_model': 'consultas.consultas',
            'res_id': self.consulta_id.id,
            'views': [(self.env.ref('consultas_pnc.consultas_consultas_form').id, 'form')],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }


class consulta_proyeccion(models.Model):
    _name = "consultas.proyeccion"
    _inherit = ['mail.thread']
    _description = "Proyeccion Anual"

    tratamiento_id = fields.Many2one("consultas.tratamiento")
    referimiento_id = fields.Many2one("consultas.referimiento")
    proyeccion = fields.Integer(string="Proyeccion", required=True)
    programa = fields.Many2one("programa.programa", string="Programa", required=True)
    year = fields.Selection(selection='_selection_year', string='Año', required=True)

    @api.model
    def _selection_year(self):
        # hasta el año siguiente, para poder cargar la proyeccion antes de que empiece
        return [(str(num), str(num)) for num in range(2000, fields.Date.today().year + 2)]

    _unique_name = models.Constraint("unique(tratamiento_id,year,programa)", "Proyeccion Existe")
