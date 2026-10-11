from odoo import fields, models
from odoo.exceptions import UserError


class ReportAsistenciaEconomica(models.TransientModel):
    _name = "report.asistencia.economica"
    _description = "Asistencia Economica"

    fecha_inicial = fields.Date(string="Fecha Inicial", required=True)
    fecha_final = fields.Date(string="Fecha Final", required=True)
    paciente_ids = fields.Many2many("ficha.paciente", string="Paciente(s) / Participante(s)")
    programa_ids = fields.Many2many("programa.programa", string="Programas")

    def _print_report(self, data):
        raise UserError('Error!')

    def get_asistencias(self):
        asistencia_ids = self.env['ficha.paciente.ayuda.economica'].search([('fecha', '>=', self.fecha_inicial),
                                                                            ('fecha', '<=', self.fecha_final)],
                                                                           order="name asc,fecha asc")
        return asistencia_ids

    def paciente_asistencia_ids(self, paciente_id):
        return self.get_asistencias().filtered(lambda x: x.ayuda_economica_id == paciente_id)

    def get_paciente_filtered(self, programa_id):
        # solo los pacientes con ayudas en el periodo: el resto no imprime nada
        con_ayuda = self.get_asistencias().ayuda_economica_id
        return self.paciente_ids.filtered(lambda x: x.programa == programa_id and x in con_ayuda)

    def get_totales(self):
        totales = []
        asistencias = self.get_asistencias()
        for programa_id in self.programa_ids:
            total_programa = sum(
                asistencias.filtered(lambda x: x.ayuda_economica_id.programa == programa_id).mapped('monto'))
            totales.append({'programa': programa_id.name,
                            'total_programa': total_programa})
        return totales

    def _check_report(self, report_type):
        if not self.paciente_ids:
            self.paciente_ids = self.paciente_ids.search([], order="nombre asc")
        if not self.programa_ids:
            self.programa_ids = self.programa_ids.search([], order="name asc")
        action = self.env.ref('consultas_pnc.menu_report_asistencia_Economica').report_action(self, config=False)
        action['report_type'] = report_type
        return action

    def print_report(self):
        return self._check_report('qweb-pdf')

    def check_report(self):
        return self._check_report('qweb-html')
