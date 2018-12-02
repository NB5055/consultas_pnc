# -*- coding: utf-8 -*-
from openerp import fields, models, api
from datetime import datetime


class consultas_consultas(models.Model):
    _name = "consultas.consultas"
    _description = "Registro de Consultas"
    _inherit = ["mail.thread"]
    _order = "fecha desc,name"

    name = fields.Many2one('ficha.paciente', string='Paciente / Participante', required=True)
    programa = fields.Many2one("programa.programa", string="Programa",
                               help="""Programa al que """
                                    """pertenece la Consulta""")
    edad = fields.Integer(related='name.edad', required=True)
    sexo = fields.Selection(related='name.sexo', required=True)
    fecha = fields.Date(string="Fecha", default=fields.Date.context_today, required=True)
    diagnostico = fields.One2many("consultas.diagnostico.line", 'consulta_id',
                                  string="Diagnostico / Estado / Actividad", copy=True)
    referimiento = fields.One2many("consultas.referimiento.line", 'consulta_id',
                                   string="Referimiento", copy=True)
    tratamiento = fields.One2many("consultas.tratamiento.line", 'consulta_id',
                                  string="Tratamiento / Seguimiento", copy=True)
    employee_id = fields.Many2one("hr.employee", string="Médico / Profesor",
                                  default=lambda self: self._get_employee())

    @api.onchange('name')
    def set_programa(self):
        self.programa = self.name.programa

    @api.model
    def _get_employee(self):
        return self.env["hr.employee"].search([('user_id', '=', self.env.user.id)])


class consultas_diagnostico(models.Model):
    _name = "consultas.diagnostico"
    _description = ""

    name = fields.Char(string="Diagnostico")


class consultas_diagnostico_line(models.Model):
    _name = "consultas.diagnostico.line"
    _description = ""

    consulta_id = fields.Many2one("consultas.consultas",
                                  string="consulta_line_id")
    paciente_id = fields.Many2one("ficha.paciente", string="Paciente / Participante")
    name = fields.Many2one("consultas.diagnostico", string="Diagnostico")


class consultas_referimiento(models.Model):
    _name = "consultas.referimiento"
    _description = ""

    name = fields.Char(string="Referimiento")
    proyeccion = fields.One2many('consultas.proyeccion', 'referimiento_id',
                                 string="Proyeccion Anual")
    _sql_constraints = [
        ('unique_name', 'unique(name)', """Referimiento Existe""")
    ]


class consultas_referimiento_line(models.Model):
    _name = "consultas.referimiento.line"
    _description = ""

    name = fields.Many2one("consultas.referimiento", ondelete="cascade", string="Referimiento")
    consulta_id = fields.Many2one("consultas.consultas")


class consultas_tratamiento(models.Model):
    _name = "consultas.tratamiento"
    _description = ""

    name = fields.Char(string="Tratamiento")
    proyeccion = fields.One2many('consultas.proyeccion', 'tratamiento_id',
                                 string="Proyeccion Anual")
    _sql_constraints = [
        ('unique_name', 'unique(name)', """Tratamiento Existe""")
    ]


class consultas_tratamiento_line(models.Model):
    _name = "consultas.tratamiento.line"
    _description = ""

    name = fields.Many2one("consultas.tratamiento", ondelete="cascade",
                           string="Tratamiento / Seguimiento")
    consulta_id = fields.Many2one("consultas.consultas")


class consulta_proyeccion(models.Model):
    _name = "consultas.proyeccion"
    _description = ""

    tratamiento_id = fields.Many2one("consultas.tratamiento")
    referimiento_id = fields.Many2one("consultas.referimiento")
    proyeccion = fields.Integer(string="Proyeccion")
    programa = fields.Many2one("programa.programa", string="Programa")
    year = fields.Selection([(num, str(num)) for num in range(2000, (datetime.now().year) + 1)], string='Año')

    _sql_constraints = [
        ('unique_name', "unique(tratamiento_id,referimiento_id,proyeccion,year,programa)","Proyeccion Existe")
    ]
