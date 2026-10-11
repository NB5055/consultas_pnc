from odoo import fields, models


class programa_programa(models.Model):
    _name = "programa.programa"
    _description = "Listado de programas del instituto"
    _inherit = ['mail.thread']
    _order = "sequence,name"

    sequence = fields.Integer()
    name = fields.Char(string="Nombre", help="Nombre del Programa",
                       required=True, tracking=True)
    encargado = fields.Many2one("hr.employee", string="Encargado del Programa", tracking=True)
    provincia = fields.One2many("region.provincia", "programa_id",
                                string="""Provincia de Ejecución""")
    participantes = fields.One2many("hr.employee", 'programa_id',
                                    string="Médico / Profesor")
    notas = fields.Text(string="Notas", tracking=True)
    paciente_id = fields.Many2one("ficha.paciente", tracking=True)
    tratamiento_ids = fields.Many2many('consultas.tratamiento', string="Tratamientos")

    proyeccion_ids = fields.One2many("consultas.proyeccion", "programa", string="Proyecciones")
    program_type = fields.Selection([('prevencion_ceguera', 'Prevencion Ceguera'),
                                     ('servicio', 'Rehabilitacion')], string="Categoria", tracking=True)

    _name_uniq = models.Constraint('unique(name)', "Este programa ya existe")


class programa_participantes(models.Model):
    _name = "programa.participantes"
    _description = "Empleados Participantes del proyecto"

    participante_id = fields.Many2one("hr.employee",
                                      string="Médico / Profesor")
    especialidad = fields.Many2one(related="participante_id.job_id",
                                   string="Especialidad / Cargo",
                                   readonly=True)
    programa_id = fields.Many2one("programa.programa", string="Programa")
