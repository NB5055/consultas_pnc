# -*- coding: utf-8 -*-
from openerp import fields, models


class programa_programa(models.Model):
    _name = "programa.programa"
    _description = "Listado de programas del instituto"
    _inherit = ['mail.thread']
    _order = "name"

    name = fields.Char(string="Nombre", help="Nombre del Programa",
                       required=True, placeholder="Nombre")
    encargado = fields.Many2one("hr.employee", string="Encargado del Programa")
    provincia = fields.One2many("region.provincia", "programa_id",
                                string="""Provincia de Ejecución""")
    participantes = fields.One2many("hr.employee", 'programa_id',
                                    string="Médico / Profesor")
    notas = fields.Text(string="Notas")
    paciente_id = fields.Many2one("ficha.paciente")
    tratamiento_ids = fields.Many2many('consultas.tratamiento', string="Tratamientos")

    proyeccion_ids = fields.One2many("consultas.proyeccion", "programa", string="Proyecciones")

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "Este programa ya existe")
    ]


class programa_participantes(models.Model):
    _name = "programa.participantes"
    _description = "Empleados Participantes del proyecto"

    participante_id = fields.Many2one("hr.employee",
                                      string="Médico / Profesor")
    especialidad = fields.Many2one(related="participante_id.job_id",
                                   string="Especialidad / Cargo",
                                   readonly=True)
    programa_id = fields.Many2one("programa.programa", string="Programa")
