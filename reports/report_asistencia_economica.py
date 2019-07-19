from openerp import models, fields, api
from openerp.exceptions import UserError


class ReportAsistenciaEconomica(models.TransientModel):
    _name = "report.asistencia.economica"
    _description = "Asistencia Economica"

    fecha_inicial = fields.Date(string="Fecha Inicial", required=True)
    fecha_final = fields.Date(string="Fecha Final", required=True)
    paciente_ids = fields.Many2many("ficha.paciente", string="Paciente(s) / Participante(s)")

    def _print_report(self, data):
        raise UserError('Error!')

    @api.multi
    def get_asistencias(self):
        if not self.paciente_ids:
            self.paciente_ids = self.env['ficha.paciente'].search([], order="nombre asc")
        asistencia_ids = self.env['ficha.paciente.ayuda.economica'].search([('fecha', '>=', self.fecha_inicial),
                                                                            ('fecha', '<=', self.fecha_final)],
                                                                           order="name asc,fecha asc")
        return asistencia_ids

    @api.multi
    def paciente_asistencia_ids(self, paciente_id):
        return self.get_asistencias().filtered(lambda self:self.ayuda_economica_id == paciente_id)

    @api.multi
    def check_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_asistencia_economica',
            'target': 'new',
            'report_type': 'qweb-html',
        }
