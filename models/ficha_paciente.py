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

    name = fields.Char(string="Cedula", required=True, default=0, copy=False)
    nombre = fields.Char(string="Nombre", required=True)
    apellidos = fields.Char(string="Apellidos", required=True)
    apodos = fields.Char(string="Apodos")
    sexo = fields.Selection([('m', 'Masculino'), ('f', 'Femenino')],
                            string="Sexo", default='m')
    edad = fields.Integer(string="Edad")
    direccion = fields.Char(string="Direccion")
    estado_civil = fields.Selection([('s', 'Soltero(a)'),
                                     ('c', 'Casado(a)'),
                                     ('d', 'Divorciado(a)'),
                                     ('v', 'Viudo(a)')], string="Estado Civil",
                                    default="s")
    grado_academico = fields.Char(string="Grado Academico")
    hijos = fields.Integer(string="Cant. Hijos")
    ingresos = fields.Float(string="Ingresos")
    otros = fields.Float(string="Otros Ingresos")
    cohabitantes = fields.Integer(string="Cohabitantes")
    vivienda = fields.Selection([('p', 'Propia'), ('a', 'Alquilada'), ('p', 'Prestada')], string="Vivienda",
                                default='p')
    renta = fields.Float(string='Costo Renta')
    vehiculo = fields.Selection([('s', 'Si'), ('n', 'No')], string="Vehiculo", default='n')
    trabajo = fields.Many2one('ficha.paciente.trabajo', string="Trabajo")
    seguro = fields.Many2one('ficha.paciente.seguro', string="Seguro")
    gastos_fijos = fields.One2many('ficha.paciente.gasto.fijo', 'gasto_id', string="Gastos Fijos")
    ayuda_economica = fields.One2many('ficha.paciente.ayuda.economica', 'ayuda_economica_id', string="Ayuda Economica")
    enfermedades = fields.One2many('ficha.paciente.enfermedades.line', 'enfermedad_id', string="Condiciones")
    telefonos = fields.One2many('ficha.paciente.telefono', 'telefono_id', string="Telefonos")
    lugar_nacimiento = fields.Many2one('region.provincia', string="Lugar de Nacimiento")
    display_name = fields.Char(string="Paciente", compute='_compute_display_name', search="_search_display_name")
    image = fields.Binary("Image", attachment=True, default=lambda self: self._get_default_image(True),
                          help="""This field holds the image used as avatar for this contact,"""
                               """limited to 1024x1024px""")
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
    programa = fields.Many2one("programa.programa", string="Programa a que pertenece")
    consultas = fields.One2many("consultas.consultas", "name", readonly=True)
    state = fields.Selection([('activo', 'Activo'), ('inactivo', 'Inactivo')], string='State', default="activo")
    diagnostico = fields.One2many("consultas.diagnostico.line", 'paciente_id',
                                  string="Diagnostico", copy=True)
    consultas_count = fields.Integer(compute="_compute_consultas_count")

    def _compute_consultas_count(self):
        self.consultas_count = len(self.consultas)

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
    _descripcion = 'Trabajos para Pacientes'
    _order = "name"

    name = fields.Char(string="Puestos de Trabajo", required=True)
    _sql_constraints = [
        ('unique_name', 'unique(name)', """Puesto de Trabajo Existe""")
    ]


class ficha_paciente_seguro(models.Model):
    _name = 'ficha.paciente.seguro'
    _descripcion = 'Seguros Pacientes'
    _order = "name"

    name = fields.Char(string="Aseguradora", required=True)

    _sql_constraints = [
        ('unique_name', 'unique(name)', """Seguro Existe""")
    ]


class ficha_paciente_gasto_fijo(models.Model):
    _name = 'ficha.paciente.gasto.fijo'
    _descripcion = 'Gastos Fijos de Paciente'
    _order = "name"

    gasto_id = fields.Many2one('ficha.paciente', string='Gasto ID')
    name = fields.Many2one('ficha.paciente.gasto.fijo.descripcion',
                           string='Tipo Gasto', required=True)
    monto = fields.Float(string="Monto del Gasto", required=True)


class ficha_paciente_gasto_fijo_descripcion(models.Model):
    _name = 'ficha.paciente.gasto.fijo.descripcion'
    _descripcion = 'Descripcion Gasto Fijo de Paciente'
    _order = "name"

    name = fields.Char(string="Tipo Gasto", required=True)
    _sql_constraints = [
        ('unique_name', 'unique(name)', """Gasto Existe""")
    ]


class ficha_paciente_ayuda_economica(models.Model):
    _name = 'ficha.paciente.ayuda.economica'
    _descripcion = 'Ayuda Economica del Paciente'
    _order = "fecha"

    ayuda_economica_id = fields.Many2one('ficha.paciente',
                                         string="Ayuda Economica ID")
    name = fields.Many2one('res.partner', string="Nombre Pariente", required=True,
                           help="Persona que Ofrece la ayuda")
    parentesco = fields.Many2one('ficha.paciente.parentesco', required=True,
                                 string="Parentesco")
    monto = fields.Float(string="Aporte", required=True)
    fecha = fields.Date(string="Fecha Ayuda", default=fields.Date.context_today)


class ficha_paciente_parentesco(models.Model):
    _name = 'ficha.paciente.parentesco'
    _descripcion = 'Tipos de Parientes'
    _order = "name"

    name = fields.Char(string="Tipo Pariente", required=True)
    _sql_constraints = [
        ('unique_name', 'unique(name)', """Parentesco Existe""")
    ]


class ficha_paciente_enfermedades(models.Model):
    _name = 'ficha.paciente.enfermedades'
    _descripcion = 'Enfermedades de los Pacientes'
    _order = "name"

    name = fields.Char(string="Condicion", required=True)


class ficha_paciente_enfermedades_line(models.Model):
    _name = 'ficha.paciente.enfermedades.line'
    _descripcion = 'Enfermedades de los Pacientes'
    _order = "name"

    enfermedad_id = fields.Many2one('ficha.paciente')
    name = fields.Many2one('ficha.paciente.enfermedades',
                           string="Condicion")


class ficha_paciente_telefono(models.Model):
    _name = 'ficha.paciente.telefono'
    _descripcion = 'Telefonos del Paciente'

    telefono_id = fields.Many2one('ficha.paciente',
                                  string="Telefonos Pacientes")
    name = fields.Char(string='Telefono', required=True)
    tipo = fields.Selection([('r', 'Residencial'),
                             ('c', 'Celular')], string="Tipo de Telefono",
                            required=True)
