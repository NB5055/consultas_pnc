# -*- coding: utf-8 -*-

from openerp import fields, models, api


class Citas(models.Model):
    _name = "citas.citas"
    _descripcion = "Administracion de citas"

    paciente_id = fields.Many2one("ficha.paciente", string="Paciente",
                                required=True)
    fecha_desde = fields.Datetime(string="Fecha Desde", required=True)
    fecha_hasta = fields.Datetime(string="Fecha Hasta", required=True)
    programa_id = fields.Many2one("programa.programa", string="Programa",
                                required=True)