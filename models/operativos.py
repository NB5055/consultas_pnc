from openerp import models, fields, api


class Operativos(models.Model):
    _name = 'operativos'
    _description = "Operativos"
    _order = "name, fecha"

    name = fields.Many2one("consultas.referimiento", string="Consulta")
    atendidos = fields.Integer(string="Cantidad")
    fecha = fields.Date(string="Fecha")
    programa = fields.Many2one('programa.programa', string="Programa")
