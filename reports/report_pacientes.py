from odoo import fields, models


class ReportePacientes(models.TransientModel):
    _name = 'report.paciente'
    _description = "Listado de Participantes"

    programa_ids = fields.Many2many('programa.programa', string="Programas")

    def get_data(self, programa_id):
        return self.env['ficha.paciente'].sudo().search([('programa', 'in', programa_id.ids)])

    def check_report(self):
        if not self.programa_ids:
            self.programa_ids = self.programa_ids.search([])
        return self.env.ref('consultas_pnc.report_report_paciente').report_action(self, config=False)
