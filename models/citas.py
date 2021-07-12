# -*- coding: utf-8 -*-

from openerp import fields, models, api


class Citas(models.Model):
    _name = "citas.citas"
    _inherit = ['mail.thread']
    _descripcion = "Administracion de citas"

    paciente_id = fields.Many2one("ficha.paciente", string="Paciente",
                                required=True, track_visibility="onchange")
    fecha_desde = fields.Datetime(string="Fecha Desde", required=True, track_visibility="onchange")
    fecha_hasta = fields.Datetime(string="Fecha Hasta", required=True, track_visibility="onchange")
    programa_id = fields.Many2one("programa.programa", string="Programa",
                                required=True, track_visibility="onchange")
