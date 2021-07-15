# -*- coding: utf-8 -*-
from datetime import datetime

from openerp import fields, models, api


class consultas_consultas(models.Model):
    _name = "consultas.consultas"
    _description = "Registro de Consultas"
    _inherit = ["mail.thread"]
    _order = "fecha desc,name"

    name = fields.Many2one('ficha.paciente', string='Paciente / Participante', required=True)
    programa = fields.Many2one("programa.programa", string="Programa", track_visibility="onchange",
                               help="""Programa al que pertenece la Consulta""")
    edad = fields.Integer(string="Edad", related='name.edad', store=True, track_visibility="onchange")
    sexo = fields.Selection(string="Sexo", related='name.sexo', store=True, track_visibility="onchange")
    fecha = fields.Date(string="Fecha", default=fields.Date.context_today, required=True, track_visibility="onchange")
    diagnostico = fields.One2many("consultas.diagnostico.line", 'consulta_id',
                                  string="Diagnostico / Estado / Actividad", copy=True, track_visibility="onchange")
    referimiento = fields.One2many("consultas.referimiento.line", 'consulta_id',
                                   string="Referimiento", copy=True)
    tratamiento = fields.One2many("consultas.tratamiento.line", 'consulta_id',
                                  string="Tratamiento / Seguimiento / Referimiento", copy=True)
    employee_id = fields.Many2one("hr.employee", string="Médico / Profesor",
                                  required=True,
                                  default=lambda self: self._get_employee(), track_visibility="onchange")
    notes = fields.Text(string="Notas", track_visibility="onchange")

    @api.onchange('name')
    def set_programa(self):
        self.programa = self.name.programa

    @api.model
    def _get_employee(self):
        return self.env["hr.employee"].search([('user_id', '=', self.env.user.id)])


class consultas_diagnostico(models.Model):
    _name = "consultas.diagnostico"
    _inherit = ['mail.thread']
    _description = ""

    name = fields.Char(string="Diagnostico", track_visibility="onchange")


class consultas_diagnostico_line(models.Model):
    _name = "consultas.diagnostico.line"
    _inherit = ['mail.thread']
    _description = ""

    consulta_id = fields.Many2one("consultas.consultas",
                                  string="consulta_line_id", track_visibility="onchange")
    paciente_id = fields.Many2one("ficha.paciente", string="Paciente / Participante", track_visibility="onchange")
    name = fields.Many2one("consultas.diagnostico", string="Diagnostico", track_visibility="onchange")


class consultas_referimiento(models.Model):
    _name = "consultas.referimiento"
    _inherit = ['mail.thread']
    _description = ""

    name = fields.Char(string="Referimiento", track_visibility="onchange")
    proyeccion = fields.One2many('consultas.proyeccion', 'referimiento_id',
                                 string="Proyeccion Anual", track_visibility="onchange")
    _sql_constraints = [
        ('unique_name', 'unique(name)', """Referimiento Existe""")
    ]


class consultas_referimiento_line(models.Model):
    _name = "consultas.referimiento.line"
    _inherit = ['mail.thread']
    _description = ""

    name = fields.Many2one("consultas.referimiento", ondelete="cascade", string="Referimiento", track_visibility="onchange")
    consulta_id = fields.Many2one("consultas.consultas", track_visibility="onchange")


class consultas_tratamiento(models.Model):
    _name = "consultas.tratamiento"
    _inherit = ['mail.thread']
    _description = ""

    name = fields.Char(string="Tratamiento", track_visibility="onchange")
    proyeccion = fields.One2many('consultas.proyeccion', 'tratamiento_id',
                                 string="Proyeccion Anual", track_visibility="onchange")
    programa_ids = fields.Many2many('programa.programa', string="Programas", track_visibility="onchange")
    discount_report = fields.Many2one('consultas.tratamiento', string="Descuenta a", track_visibility="onchange")
    category = fields.Selection([('rh', 'Rehabilitacion'), ('pc', 'Prevencion Ceguera')],
                                string="Categoria", track_visibility="onchange")

    _sql_constraints = [
        ('unique_name', 'unique(name)', """Tratamiento Existe""")
    ]


class consultas_tratamiento_line(models.Model):
    _name = "consultas.tratamiento.line"
    _description = ""

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

    @api.multi
    def show_consulta(self):
        return {
            'name': "Servicios o Atenciones",
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'consultas.consultas',
            'views': [(self.env.ref('consultas_pnc.consultas_consultas_tree').id, 'tree'),
                      (self.env.ref('consultas_pnc.consultas_consultas_form').id, 'form')],
            'target': 'current',
            'views': False,
            'type': 'ir.actions.act_window',
            # 'res_id': self.consulta_id.id,
            'domain': [(1, '=', 1)],

        }


class consulta_proyeccion(models.Model):
    _name = "consultas.proyeccion"
    _inherit = ['mail.thread']
    _description = ""

    tratamiento_id = fields.Many2one("consultas.tratamiento")
    referimiento_id = fields.Many2one("consultas.referimiento")
    proyeccion = fields.Integer(string="Proyeccion", required=True)
    programa = fields.Many2one("programa.programa", string="Programa", required=True)
    year = fields.Selection([(num, str(num)) for num in range(2000, (datetime.now().year) + 1)], string='Año',
                            required=True)

    _sql_constraints = [
        ('unique_name', "unique(tratamiento_id,year,programa)", "Proyeccion Existe")
    ]
