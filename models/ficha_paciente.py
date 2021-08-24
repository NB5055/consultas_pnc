# -*- coding: utf-8 -*-

from openerp import api, tools, fields, models
import openerp


class ficha_paciente(models.Model):
    _name = "ficha.paciente"
    _description = "ficha evaluacion socio economica"
    _rec_name = "display_name"
    _inherit = ['mail.thread']
    _order = "apellidos,nombre,name"

    @api.one
    @api.depends('nombre', 'apellidos', 'name')
    def _compute_display_name(self):
        self.display_name = ' '.join(filter(None, [self.apellidos, self.nombre, " (", self.name, ")"]))

    name = fields.Char(string="Cedula", required=True, default=0, copy=False, track_visibility="onchange")
    nombre = fields.Char(string="Nombre", required=True, track_visibility="onchange")
    apellidos = fields.Char(string="Apellidos", required=True, track_visibility="onchange")
    apodos = fields.Char(string="Apodos", track_visibility="onchange")
    sexo = fields.Selection([('m', 'Masculino'), ('f', 'Femenino')],
                            string="Sexo", default='m', track_visibility="onchange")
    edad = fields.Integer(string="Edad", compute="compute_age", store=True, track_visibility="onchange")
    direccion = fields.Char(string="Direccion", track_visibility="onchange")
    estado_civil = fields.Selection([('s', 'Soltero(a)'),
                                     ('c', 'Casado(a)'),
                                     ('d', 'Divorciado(a)'),
                                     ('v', 'Viudo(a)')], string="Estado Civil",
                                    default="s", track_visibility="onchange")
    grado_academico = fields.Char(string="Grado Academico", track_visibility="onchange")
    hijos = fields.Integer(string="Cant. Hijos", track_visibility="onchange")
    ingresos = fields.Float(string="Ingresos", track_visibility="onchange")
    otros = fields.Float(string="Otros Ingresos", track_visibility="onchange")
    cohabitantes = fields.Integer(string="Cohabitantes", track_visibility="onchange")
    vivienda = fields.Selection([('p', 'Propia'), ('a', 'Alquilada'), ('p', 'Prestada')], string="Vivienda",
                                default='p', track_visibility="onchange")
    renta = fields.Float(string='Costo Renta', track_visibility="onchange")
    vehiculo = fields.Selection([('s', 'Si'), ('n', 'No')], string="Vehiculo", default='n', track_visibility="onchange")
    trabajo = fields.Many2one('ficha.paciente.trabajo', string="Trabajo", track_visibility="onchange")
    seguro = fields.Many2one('ficha.paciente.seguro', string="Seguro", track_visibility="onchange")
    gastos_fijos = fields.One2many('ficha.paciente.gasto.fijo', 'gasto_id', string="Gastos Fijos", track_visibility="onchange")
    ayuda_economica = fields.One2many('ficha.paciente.ayuda.economica', 'ayuda_economica_id', string="Ayuda Economica", track_visibility="onchange")
    enfermedades = fields.One2many('ficha.paciente.enfermedades.line', 'enfermedad_id', string="Condiciones", track_visibility="onchange")
    telefonos = fields.One2many('ficha.paciente.telefono', 'telefono_id', string="Telefonos", track_visibility="onchange")
    lugar_nacimiento = fields.Many2one('region.provincia', string="Lugar de Nacimiento", track_visibility="onchange")
    display_name = fields.Char(string="Paciente", compute='_compute_display_name', search="_search_display_name")
    image = fields.Binary("Image", attachment=True, default=lambda self: self._get_default_image(True),
                          help="""This field holds the image used as avatar for this contact,"""
                               """limited to 1024x1024px""", track_visibility="onchange")
    image_medium = fields.Binary("Medium-sized image",
                                 compute='_compute_images', inverse='_inverse_image_medium',
                                 store=True, attachment=True,
                                 help="""Medium-sized image of this contact. """
                                      """It is automatically resized as a 128x128px image, with """
                                      """aspect ratio preserved."""
                                      """Use this field in form views or some kanban views.""")
    image_small = fields.Binary("Small-sized image",
                                compute='_compute_images', inverse='_inverse_image_small',
                                store=True, attachment=True,
                                help="""Small-sized image of this contact. It is automatically """
                                     """resized as a 64x64px image, with aspect ratio preserved. """
                                     """Use this field anywhere a small image is required.""")
    programa = fields.Many2one("programa.programa", string="Programa a que pertenece", track_visibility="onchange")
    consultas = fields.One2many("consultas.consultas", "name", readonly=True, track_visibility="onchange")
    state = fields.Selection([('activo', 'Activo'), ('inactivo', 'Inactivo')], string='State', default="activo")
    diagnostico = fields.One2many("consultas.diagnostico.line", 'paciente_id',
                                  string="Diagnostico", copy=True, track_visibility="onchange")
    consultas_count = fields.Integer(compute="_compute_consultas_count", track_visibility="onchange")
    birth_date = fields.Date(string="Fecha Nacimiento", track_visibility="onchange")

    @api.multi
    @api.depends('birth_date')
    def compute_age(self):
        for paciente in self:
            if paciente.birth_date:
                birth_date = fields.Date.from_string(paciente.birth_date)
                today = fields.Date.from_string(fields.Date.today())
                paciente.edad = abs(today.year - birth_date.year)

    def _compute_consultas_count(self):
        for consulta in self:
            consulta.consultas_count = len(consulta.consultas)

    @api.depends('image')
    def _compute_images(self):
        for rec in self:
            rec.image_medium = tools.image_resize_image_medium(rec.image)
            rec.image_small = tools.image_resize_image_small(rec.image)

    def _inverse_image_medium(self):
        for rec in self:
            rec.image = tools.image_resize_image_big(rec.image_medium)

    def _inverse_image_small(self):
        for rec in self:
            rec.image = tools.image_resize_image_big(rec.image_small)

    @api.model
    def _get_default_image(self, colorize=False):
        img_path = openerp.modules.get_module_resource(
            'base', 'static/src/img', 'avatar.png')
        with open(img_path, 'rb') as f:
            image = f.read()
        return tools.image_resize_image_big(image.encode('base64'))

    @api.model
    def _search_display_name(self, operator, value):
        return ["|", "|", ('apellidos', operator, value),
                ('nombre', operator, value),
                ('name', operator, value)]

    @api.multi
    def show_complete_history(self):
        return {
            'name': 'Historial',
            'res_model': 'consultas.consultas',
            'type': 'ir.actions.act_window',
            'domain': [('name', '=', self.id)],
            'views': [(self.env.ref('consultas_pnc.consultas_consultas_history_tree').id, 'tree'),
                      (self.env.ref('consultas_pnc.consultas_consultas_history_form').id, 'form')]
        }

    _sql_constraints = [
        ('unique_name', 'unique(name)', """Existe otro Paciente/"""
                                        """Participante"""
                                        """con este documento"""),
        ('unique_name_ced', 'unique(name,nombre)', """Este Paciente/"""
                                                   """Participante"""
                                                   """esta duplicado""")
    ]


class ficha_paciente_trabajo(models.Model):
    _name = 'ficha.paciente.trabajo'
    _inherit = ['mail.thread']
    _descripcion = 'Trabajos para Pacientes'
    _order = "name"

    name = fields.Char(string="Puestos de Trabajo", required=True, track_visibility="onchange")
    _sql_constraints = [
        ('unique_name', 'unique(name)', """Puesto de Trabajo Existe""")
    ]


class ficha_paciente_seguro(models.Model):
    _name = 'ficha.paciente.seguro'
    _inherit = ['mail.thread']
    _descripcion = 'Seguros Pacientes'
    _order = "name"

    name = fields.Char(string="Aseguradora", required=True, track_visibility="onchange")

    _sql_constraints = [
        ('unique_name', 'unique(name)', """Seguro Existe""")
    ]


class ficha_paciente_gasto_fijo(models.Model):
    _name = 'ficha.paciente.gasto.fijo'
    _inherit = ['mail.thread']
    _descripcion = 'Gastos Fijos de Paciente'
    _order = "name"

    gasto_id = fields.Many2one('ficha.paciente', string='Gasto ID', track_visibility="onchange")
    name = fields.Many2one('ficha.paciente.gasto.fijo.descripcion',
                           string='Tipo Gasto', required=True, track_visibility="onchange")
    monto = fields.Float(string="Monto del Gasto", required=True, track_visibility="onchange")


class ficha_paciente_gasto_fijo_descripcion(models.Model):
    _name = 'ficha.paciente.gasto.fijo.descripcion'
    _inherit = ['mail.thread']
    _descripcion = 'Descripcion Gasto Fijo de Paciente'
    _order = "name"

    name = fields.Char(string="Tipo Gasto", required=True, track_visibility="onchange")
    _sql_constraints = [
        ('unique_name', 'unique(name)', """Gasto Existe""")
    ]


class ficha_paciente_ayuda_economica(models.Model):
    _name = 'ficha.paciente.ayuda.economica'
    _inherit = ['mail.thread']
    _descripcion = 'Ayuda Economica del Paciente'
    _order = "fecha"

    ayuda_economica_id = fields.Many2one('ficha.paciente',
                                         string="Ayuda Economica ID", track_visibility="onchange")
    name = fields.Many2one('res.partner', string="Nombre Pariente", required=True,
                           help="Persona que Ofrece la ayuda", track_visibility="onchange")
    parentesco = fields.Many2one('ficha.paciente.parentesco', required=True,
                                 string="Parentesco", track_visibility="onchange")
    monto = fields.Float(string="Aporte", required=True, track_visibility="onchange")
    fecha = fields.Date(string="Fecha Ayuda", default=fields.Date.context_today, required=True, track_visibility="onchange")

    _sql_constraints = [
        ('check_amount', 'check(monto > 0)', 'El aporte debe ser mayor de 0')
    ]


class ficha_paciente_parentesco(models.Model):
    _name = 'ficha.paciente.parentesco'
    _descripcion = 'Tipos de Parientes'
    _inherit = ['mail.thread']
    _order = "name"

    name = fields.Char(string="Tipo Pariente", required=True, track_visibility="onchange")
    _sql_constraints = [
        ('unique_name', 'unique(name)', """Parentesco Existe""")
    ]


class ficha_paciente_enfermedades(models.Model):
    _name = 'ficha.paciente.enfermedades'
    _inherit = ['mail.thread']
    _descripcion = 'Enfermedades de los Pacientes'
    _order = "name"

    name = fields.Char(string="Condicion", required=True, track_visibility="onchange")


class ficha_paciente_enfermedades_line(models.Model):
    _name = 'ficha.paciente.enfermedades.line'
    _inherit = ['mail.thread']
    _descripcion = 'Enfermedades de los Pacientes'
    _order = "name"

    enfermedad_id = fields.Many2one('ficha.paciente', track_visibility="onchange")
    name = fields.Many2one('ficha.paciente.enfermedades',
                           string="Condicion", track_visibility="onchange")


class ficha_paciente_telefono(models.Model):
    _name = 'ficha.paciente.telefono'
    _inherit = ['mail.thread']
    _descripcion = 'Telefonos del Paciente'

    telefono_id = fields.Many2one('ficha.paciente',
                                  string="Telefonos Pacientes", track_visibility="onchange")
    name = fields.Char(string='Telefono', required=True, track_visibility="onchange")
    tipo = fields.Selection([('r', 'Residencial'),
                             ('c', 'Celular')], string="Tipo de Telefono",
                            required=True, track_visibility="onchange")
