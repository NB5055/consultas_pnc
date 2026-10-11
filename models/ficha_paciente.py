import re

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


def solo_digitos(value):
    return re.sub(r'\D', '', value or '')


class ficha_paciente(models.Model):
    _name = "ficha.paciente"
    _description = "ficha evaluacion socio economica"
    _inherit = ['mail.thread']
    _order = "apellidos,nombre,name"
    _rec_names_search = ['apellidos', 'nombre', 'name', 'cedula_digitos']

    @api.depends('nombre', 'apellidos', 'name')
    def _compute_display_name(self):
        for paciente in self:
            paciente.display_name = ' '.join(
                filter(None, [paciente.apellidos, paciente.nombre, " (", paciente.name, ")"]))

    name = fields.Char(string="Cedula", required=True, default='0', copy=False, tracking=True, index=True)
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
    programa = fields.Many2one("programa.programa", string="Programa a que pertenece", tracking=True, index=True)
    consultas = fields.One2many("consultas.consultas", "name", readonly=True)
    state = fields.Selection([('activo', 'Activo'), ('inactivo', 'Inactivo')], string='State', default="activo")
    diagnostico = fields.One2many("consultas.diagnostico.line", 'paciente_id',
                                  string="Diagnostico", copy=True)
    consultas_count = fields.Integer(compute="_compute_consultas_count")
    citas = fields.One2many("citas.citas", "paciente_id", string="Citas")
    citas_count = fields.Integer(compute="_compute_citas_count")
    cedula_digitos = fields.Char(string="Cedula sin guiones", compute="_compute_cedula_digitos",
                                 store=True, index=True)
    cedula_repetida = fields.Boolean(string="Cedula Repetida", compute="_compute_cedula_repetida",
                                     search="_search_cedula_repetida",
                                     help="Otra ficha tiene esta misma cedula")
    birth_date = fields.Date(string="Fecha Nacimiento", tracking=True)

    @api.depends('birth_date')
    def compute_age(self):
        today = fields.Date.context_today(self)
        for paciente in self:
            if paciente.birth_date:
                paciente.edad = max(relativedelta(today, paciente.birth_date).years, 0)
            else:
                paciente.edad = paciente.edad

    @api.model
    def _cron_actualizar_edades(self):
        """La edad se guarda para poder agrupar y buscar; se refresca a diario.

        Va por SQL para no tocar la fecha de modificacion de la ficha: no es un
        cambio hecho por nadie.
        """
        self.env.flush_all()
        self.env.cr.execute(
            """UPDATE ficha_paciente
                  SET edad = greatest(date_part('year', age(%(hoy)s, birth_date)), 0)
                WHERE birth_date IS NOT NULL
                  AND edad IS DISTINCT FROM greatest(date_part('year', age(%(hoy)s, birth_date)), 0)""",
            {'hoy': fields.Date.context_today(self)})
        self.env.invalidate_all()

    @api.model
    def _corregir_edades_historicas(self):
        """Deja la edad de cada consulta en la que tenia el paciente ese dia (y sus lineas igual)."""
        self._cron_actualizar_edades()
        self.env.cr.execute(
            """UPDATE consultas_consultas c
                  SET edad = greatest(date_part('year', age(c.fecha, f.birth_date)), 0)
                 FROM ficha_paciente f
                WHERE f.id = c.name AND f.birth_date IS NOT NULL
                  AND c.edad IS DISTINCT FROM greatest(date_part('year', age(c.fecha, f.birth_date)), 0)""")
        self.env.cr.execute(
            """UPDATE consultas_tratamiento_line l SET edad = c.edad, sexo = c.sexo
                 FROM consultas_consultas c
                WHERE c.id = l.consulta_id AND (l.edad IS DISTINCT FROM c.edad OR l.sexo IS DISTINCT FROM c.sexo)""")
        self.env.invalidate_all()

    def _compute_consultas_count(self):
        counts = dict(self.env['consultas.consultas']._read_group(
            [('name', 'in', self.ids)], ['name'], ['__count']))
        for paciente in self:
            paciente.consultas_count = counts.get(paciente, 0)

    def _compute_citas_count(self):
        counts = dict(self.env['citas.citas']._read_group(
            [('paciente_id', 'in', self.ids)], ['paciente_id'], ['__count']))
        for paciente in self:
            paciente.citas_count = counts.get(paciente, 0)

    # ------------------------------------------------------------ cedula
    @api.depends('name')
    def _compute_cedula_digitos(self):
        """Solo los digitos de una cedula completa: busca con o sin guiones y detecta repetidas."""
        for paciente in self:
            digits = solo_digitos(paciente.name)
            es_cedula = len(digits) == 11 and not re.search(r'[^\W\d_]', paciente.name or '')
            paciente.cedula_digitos = digits if es_cedula else False

    @api.model
    def _normalizar_cedula(self, value):
        """11 digitos -> 000-0000000-0. Sin cedula: 0 o un texto (p. ej. menor de edad)."""
        value = (value or '').strip()
        if re.search(r'[^\W\d_]', value):
            return value
        digits = solo_digitos(value)
        if not digits.strip('0'):
            return '0'
        if len(digits) != 11:
            raise ValidationError(
                "La cedula debe tener 11 digitos (se recibieron %s: %s). "
                "Si el paciente no tiene cedula, deje 0." % (len(digits), value))
        return '%s-%s-%s' % (digits[:3], digits[3:10], digits[10])

    def _check_cedula_unica(self):
        for paciente in self.filtered('cedula_digitos'):
            otra = self.search([('id', '!=', paciente.id), ('cedula_digitos', '=', paciente.cedula_digitos)], limit=1)
            if otra:
                raise ValidationError(
                    "Ya existe una ficha con la cedula %s: %s" % (paciente.name, otra.display_name))

    @api.model
    def _ids_cedula_repetida(self):
        self.flush_model(['cedula_digitos'])
        self.env.cr.execute(
            """SELECT unnest(array_agg(id)) FROM ficha_paciente
                WHERE cedula_digitos IS NOT NULL GROUP BY cedula_digitos HAVING count(*) > 1""")
        return [row[0] for row in self.env.cr.fetchall()]

    def _compute_cedula_repetida(self):
        repetidas = set(self._ids_cedula_repetida())
        for paciente in self:
            paciente.cedula_repetida = paciente.id in repetidas

    def _search_cedula_repetida(self, operator, value):
        if operator not in ('=', '!=', 'in', 'not in'):
            return NotImplemented
        positive = (operator in ('=', 'in')) == bool(value if operator in ('=', '!=') else True in value)
        return [('id', 'in' if positive else 'not in', self._ids_cedula_repetida())]

    @api.model_create_multi
    def create(self, vals_list):
        # carga de datos historicos: las cedulas entran tal como estaban
        if self.env.context.get('pnc_carga_historica'):
            return super().create(vals_list)
        for vals in vals_list:
            if 'name' in vals:
                vals['name'] = self._normalizar_cedula(vals['name'])
        pacientes = super().create(vals_list)
        pacientes._check_cedula_unica()
        return pacientes

    def write(self, vals):
        changed = self.browse()
        if 'name' in vals and not self.env.context.get('pnc_carga_historica'):
            vals = dict(vals, name=self._normalizar_cedula(vals['name']))
            # cambiar solo el formato de una cedula historica no cuenta como cambiarla
            changed = self.filtered(lambda paciente: solo_digitos(paciente.name) != solo_digitos(vals['name']))
        res = super().write(vals)
        if changed:
            changed._check_cedula_unica()
        return res

    def show_citas(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('consultas_pnc.act_citas')
        action['domain'] = [('paciente_id', '=', self.id)]
        action['context'] = {'default_paciente_id': self.id, 'default_programa_id': self.programa.id}
        return action

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
    _description = 'Gastos Fijos de Paciente'
    _order = "name"

    gasto_id = fields.Many2one('ficha.paciente', string='Gasto ID', required=True, ondelete='cascade', index=True)
    name = fields.Many2one('ficha.paciente.gasto.fijo.descripcion',
                           string='Tipo Gasto', required=True)
    monto = fields.Float(string="Monto del Gasto", required=True)


class ficha_paciente_gasto_fijo_descripcion(models.Model):
    _name = 'ficha.paciente.gasto.fijo.descripcion'
    _inherit = ['mail.thread']
    _description = 'Descripcion Gasto Fijo de Paciente'
    _order = "name"

    name = fields.Char(string="Tipo Gasto", required=True, tracking=True)

    _unique_name = models.Constraint('unique(name)', "Gasto Existe")


class ficha_paciente_ayuda_economica(models.Model):
    _name = 'ficha.paciente.ayuda.economica'
    _description = 'Ayuda Economica del Paciente'
    _order = "fecha"

    ayuda_economica_id = fields.Many2one('ficha.paciente', string="Ayuda Economica ID",
                                         required=True, ondelete='cascade', index=True)
    name = fields.Many2one('res.partner', string="Nombre Pariente", required=True,
                           help="Persona que Ofrece la ayuda")
    parentesco = fields.Many2one('ficha.paciente.parentesco', required=True,
                                 string="Parentesco")
    monto = fields.Float(string="Aporte", required=True)
    fecha = fields.Date(string="Fecha Ayuda", default=fields.Date.context_today, required=True)

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
    _description = 'Condiciones del Paciente'
    _order = "name"

    enfermedad_id = fields.Many2one('ficha.paciente', required=True, ondelete='cascade', index=True)
    name = fields.Many2one('ficha.paciente.enfermedades',
                           string="Condicion")


class ficha_paciente_telefono(models.Model):
    _name = 'ficha.paciente.telefono'
    _description = 'Telefonos del Paciente'

    telefono_id = fields.Many2one('ficha.paciente', string="Telefonos Pacientes",
                                  required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Telefono', required=True)
    tipo = fields.Selection([('r', 'Residencial'),
                             ('c', 'Celular')], string="Tipo de Telefono",
                            required=True)
