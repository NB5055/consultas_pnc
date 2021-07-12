# -*- coding: utf-8 -*-
from openerp import fields, models


class programa_programa(models.Model):
    _name = "programa.programa"
    _description = "Listado de programas del instituto"
    _inherit = ['mail.thread']
    _order = "sequence,name"

    sequence = fields.Integer()
    name = fields.Char(string="Nombre", help="Nombre del Programa",
                       required=True, placeholder="Nombre", track_visibility="onchange")
    encargado = fields.Many2one("hr.employee", string="Encargado del Programa", track_visibility="onchange")
    provincia = fields.One2many("region.provincia", "programa_id",
                                string="""Provincia de Ejecución""", track_visibility="onchange")
    participantes = fields.One2many("hr.employee", 'programa_id',
                                    string="Médico / Profesor", track_visibility="onchange")
    notas = fields.Text(string="Notas", track_visibility="onchange")
    paciente_id = fields.Many2one("ficha.paciente", track_visibility="onchange")
    tratamiento_ids = fields.Many2many('consultas.tratamiento', string="Tratamientos", track_visibility="onchange")

    proyeccion_ids = fields.One2many("consultas.proyeccion", "programa", string="Proyecciones", track_visibility="onchange")
    program_type = fields.Selection([('prevencion_ceguera', 'Pregencion Ceguera'),
                                     ('servicio', 'Rehabilitacion')], string="Categoria", track_visibility="onchange")

    _sql_constraints = [
        ('name_uniq', 'unique(name)', "Este programa ya existe")
    ]


class programa_participantes(models.Model):
    _name = "programa.participantes"
    _description = "Empleados Participantes del proyecto"

    participante_id = fields.Many2one("hr.employee",
                                      string="Médico / Profesor", track_visibility="onchange")
    especialidad = fields.Many2one(related="participante_id.job_id",
                                   string="Especialidad / Cargo",
                                   readonly=True, track_visibility="onchange")
    programa_id = fields.Many2one("programa.programa", string="Programa", track_visibility="onchange")
