from odoo import api, fields, models


class ficha_paciente(models.Model):
    _name = "ficha.paciente"
    _description = "ficha evaluacion socio economica"
    _inherit = ['mail.thread']
    _order = "apellidos,nombre,name"
    _rec_names_search = ['apellidos', 'nombre', 'name']

    @api.depends('nombre', 'apellidos', 'name')
    def _compute_display_name(self):
        for paciente in self:
            paciente.display_name = ' '.join(
                filter(None, [paciente.apellidos, paciente.nombre, " (", paciente.name, ")"]))

    name = fields.Char(string="Cedula", required=True, default='0', copy=False, tracking=True)
    nombre = fields.Char(string="Nombre", required=True, tracking=True)
    apellidos = fields.Char(string="Apellidos", required=True, tracking=True)
    apodos = fields.Char(string="Apodos", tracking=True)
    sexo = fields.Selection([('m', 'Masculino'), ('f', 'Femenino')],
                            string="Sexo", default='m', tracking=True)
    edad = fields.Integer(string="Edad", compute="compute_age", store=True, readonly=False, tracking=True)
    direccion = fields.Char(string="Direccion", tracking=True)
    estado_civil = fields.Selection([('s', 'Soltero(a)'),
                                     ('c', 'Casado(a)'),
                                     ('d', 'Divorciado(a)'),
                                     ('v', 'Viudo(a)')], string="Estado Civil",
                                    default="s", tracking=True)
    grado_academico = fields.Char(string="Grado Academico", tracking=True)
    hijos = fields.Integer(string="Cant. Hijos", tracking=True)
    ingresos = fields.Float(string="Ingresos", tracking=True)
    otros = fields.Float(string="Otros Ingresos", tracking=True)
    cohabitantes = fields.Integer(string="Cohabitantes", tracking=True)
    vivienda = fields.Selection([('p', 'Propia'), ('a', 'Alquilada'), ('r', 'Prestada')], string="Vivienda",
                                default='p', tracking=True)
    renta = fields.Float(string='Costo Renta', tracking=True)
    vehiculo = fields.Selection([('s', 'Si'), ('n', 'No')], string="Vehiculo", default='n', tracking=True)
    trabajo = fields.Many2one('ficha.paciente.trabajo', string="Trabajo", tracking=True)
    seguro = fields.Many2one('ficha.paciente.seguro', string="Seguro", tracking=True)
    gastos_fijos = fields.One2many('ficha.paciente.gasto.fijo', 'gasto_id', string="Gastos Fijos")
    ayuda_economica = fields.One2many('ficha.paciente.ayuda.economica', 'ayuda_economica_id', string="Ayuda Economica")
    enfermedades = fields.One2many('ficha.paciente.enfermedades.line', 'enfermedad_id', string="Condiciones")
    telefonos = fields.One2many('ficha.paciente.telefono', 'telefono_id', string="Telefonos")
    lugar_nacimiento = fields.Many2one('region.provincia', string="Lugar de Nacimiento", tracking=True)
    image = fields.Image("Image", max_width=1024, max_height=1024,
                         help="""This field holds the image used as avatar for this contact,"""
                              """limited to 1024x1024px""")
    image_128 = fields.Image("Image 128", related="image", max_width=128, max_height=128, store=True)
    programa = fields.Many2one("programa.programa", string="Programa a que pertenece", tracking=True)
    consultas = fields.One2many("consultas.consultas", "name", readonly=True)
    state = fields.Selection([('activo', 'Activo'), ('inactivo', 'Inactivo')], string='State', default="activo")
    diagnostico = fields.One2many("consultas.diagnostico.line", 'paciente_id',
                                  string="Diagnostico", copy=True)
    consultas_count = fields.Integer(compute="_compute_consultas_count")
    birth_date = fields.Date(string="Fecha Nacimiento", tracking=True)

    @api.depends('birth_date')
    def compute_age(self):
        today = fields.Date.today()
        for paciente in self:
            if paciente.birth_date:
                paciente.edad = abs(today.year - paciente.birth_date.year)
            else:
                paciente.edad = paciente.edad

    def _compute_consultas_count(self):
        for consulta in self:
            consulta.consultas_count = len(consulta.consultas)

    def show_complete_history(self):
        return {
            'name': 'Historial',
            'res_model': 'consultas.consultas',
            'type': 'ir.actions.act_window',
            'domain': [('name', '=', self.id)],
            'views': [(self.env.ref('consultas_pnc.consultas_consultas_history_tree').id, 'list'),
                      (self.env.ref('consultas_pnc.consultas_consultas_history_form').id, 'form')]
        }

    _unique_name_ced = models.Constraint('unique(name,nombre,apellidos)',
                                         "Este Paciente/Participante esta duplicado")


class ficha_paciente_trabajo(models.Model):
    _name = 'ficha.paciente.trabajo'
    _inherit = ['mail.thread']
    _description = 'Trabajos para Pacientes'
    _order = "name"

    name = fields.Char(string="Puestos de Trabajo", required=True, tracking=True)

    _unique_name = models.Constraint('unique(name)', "Puesto de Trabajo Existe")


class ficha_paciente_seguro(models.Model):
    _name = 'ficha.paciente.seguro'
    _inherit = ['mail.thread']
    _description = 'Seguros Pacientes'
    _order = "name"

    name = fields.Char(string="Aseguradora", required=True, tracking=True)

    _unique_name = models.Constraint('unique(name)', "Seguro Existe")


class ficha_paciente_gasto_fijo(models.Model):
    _name = 'ficha.paciente.gasto.fijo'
    _inherit = ['mail.thread']
    _description = 'Gastos Fijos de Paciente'
    _order = "name"

    gasto_id = fields.Many2one('ficha.paciente', string='Gasto ID', tracking=True)
    name = fields.Many2one('ficha.paciente.gasto.fijo.descripcion',
                           string='Tipo Gasto', required=True, tracking=True)
    monto = fields.Float(string="Monto del Gasto", required=True, tracking=True)


class ficha_paciente_gasto_fijo_descripcion(models.Model):
    _name = 'ficha.paciente.gasto.fijo.descripcion'
    _inherit = ['mail.thread']
    _description = 'Descripcion Gasto Fijo de Paciente'
    _order = "name"

    name = fields.Char(string="Tipo Gasto", required=True, tracking=True)

    _unique_name = models.Constraint('unique(name)', "Gasto Existe")


class ficha_paciente_ayuda_economica(models.Model):
    _name = 'ficha.paciente.ayuda.economica'
    _inherit = ['mail.thread']
    _description = 'Ayuda Economica del Paciente'
    _order = "fecha"

    ayuda_economica_id = fields.Many2one('ficha.paciente',
                                         string="Ayuda Economica ID", tracking=True)
    name = fields.Many2one('res.partner', string="Nombre Pariente", required=True,
                           help="Persona que Ofrece la ayuda", tracking=True)
    parentesco = fields.Many2one('ficha.paciente.parentesco', required=True,
                                 string="Parentesco", tracking=True)
    monto = fields.Float(string="Aporte", required=True, tracking=True)
    fecha = fields.Date(string="Fecha Ayuda", default=fields.Date.context_today, required=True, tracking=True)

    _check_amount = models.Constraint('check(monto > 0)', 'El aporte debe ser mayor de 0')


class ficha_paciente_parentesco(models.Model):
    _name = 'ficha.paciente.parentesco'
    _description = 'Tipos de Parientes'
    _inherit = ['mail.thread']
    _order = "name"

    name = fields.Char(string="Tipo Pariente", required=True, tracking=True)

    _unique_name = models.Constraint('unique(name)', "Parentesco Existe")


class ficha_paciente_enfermedades(models.Model):
    _name = 'ficha.paciente.enfermedades'
    _inherit = ['mail.thread']
    _description = 'Enfermedades de los Pacientes'
    _order = "name"

    name = fields.Char(string="Condicion", required=True, tracking=True)


class ficha_paciente_enfermedades_line(models.Model):
    _name = 'ficha.paciente.enfermedades.line'
    _inherit = ['mail.thread']
    _description = 'Condiciones del Paciente'
    _order = "name"

    enfermedad_id = fields.Many2one('ficha.paciente', tracking=True)
    name = fields.Many2one('ficha.paciente.enfermedades',
                           string="Condicion", tracking=True)


class ficha_paciente_telefono(models.Model):
    _name = 'ficha.paciente.telefono'
    _inherit = ['mail.thread']
    _description = 'Telefonos del Paciente'

    telefono_id = fields.Many2one('ficha.paciente',
                                  string="Telefonos Pacientes", tracking=True)
    name = fields.Char(string='Telefono', required=True, tracking=True)
    tipo = fields.Selection([('r', 'Residencial'),
                             ('c', 'Celular')], string="Tipo de Telefono",
                            required=True, tracking=True)
