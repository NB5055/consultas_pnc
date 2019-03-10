from openerp import models, fields, api


class Operativos(models.Model):
    _name = 'operativos'
    _description = "Operativos"
    _order = "name, fecha"

    name = fields.Many2one("consultas.tratamiento", string="Consulta", required=True)
    atendidos = fields.Integer(string="Cantidad", required=True)
    fecha = fields.Date(string="Fecha", required=True)
    programa = fields.Many2one('programa.programa', string="Programa", required=True)