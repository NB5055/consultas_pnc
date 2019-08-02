from openerp import models, fields, api
from openerp.exceptions import UserError


class ReportAsistenciaEconomica(models.TransientModel):
    _name = "report.asistencia.economica"
    _description = "Asistencia Economica"

    fecha_inicial = fields.Date(string="Fecha Inicial", required=True)
    fecha_final = fields.Date(string="Fecha Final", required=True)
    paciente_ids = fields.Many2many("ficha.paciente", string="Paciente(s) / Participante(s)")
    programa_ids = fields.Many2many("programa.programa", string="Programas")

    def _print_report(self, data):
        raise UserError('Error!')

    @api.multi
    def get_asistencias(self):
        asistencia_ids = self.env['ficha.paciente.ayuda.economica'].search([('fecha', '>=', self.fecha_inicial),
                                                                            ('fecha', '<=', self.fecha_final)],
                                                                           order="name asc,fecha asc")
        return asistencia_ids

    @api.multi
    def paciente_asistencia_ids(self, paciente_id):
        return self.get_asistencias().filtered(lambda self: self.ayuda_economica_id == paciente_id)

    def get_paciente_filtered(self, programa_id):
        return self.paciente_ids.filtered(lambda x: x.programa == programa_id)

    @api.multi
    def check_report(self):
        if not self.paciente_ids:
            self.paciente_ids = self.paciente_ids.search([], order="nombre asc")
        if not self.programa_ids:
            self.programa_ids = self.programa_ids.search([], order="name asc")
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_asistencia_economica',
            'target': 'new',
            'report_type': 'qweb-html',
        }
