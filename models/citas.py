from odoo import fields, models


class Citas(models.Model):
    _name = "citas.citas"
    _inherit = ['mail.thread']
    _description = "Administracion de citas"
    _rec_name = "paciente_id"

    paciente_id = fields.Many2one("ficha.paciente", string="Paciente",
                                  required=True, tracking=True)
    fecha_desde = fields.Datetime(string="Fecha Desde", required=True, tracking=True)
    fecha_hasta = fields.Datetime(string="Fecha Hasta", required=True, tracking=True)
    programa_id = fields.Many2one("programa.programa", string="Programa",
                                  required=True, tracking=True)
