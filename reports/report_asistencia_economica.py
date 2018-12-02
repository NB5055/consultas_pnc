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

    @api.one
    def get_asistencias(self):
        data = {}
        paciente_ids = False
        if self.paciente_ids:
            paciente_ids = self.paciente_ids
        else:
            paciente_ids = self.env['ficha.paciente'].search([])
        for paciente_id in paciente_ids:
            asistencia_ids = self.env['ficha.paciente.ayuda.economica'].search([('fecha', '>=', self.fecha_inicial),
                                                                                ('fecha', '<=', self.fecha_final),
                                                                                ('ayuda_economica_id', '=',
                                                                                 paciente_id.id)],
                                                                               order="name asc,fecha asc")
            if asistencia_ids:
                data.update({paciente_id: asistencia_ids})
        return data

    @api.multi
    def check_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_asistencia_economica',
            'target': 'new',
            'report_type': 'qweb-html',
        }
