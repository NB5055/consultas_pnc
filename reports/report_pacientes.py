from openerp import models, fields, api


class ReportePacientes(models.TransientModel):
    _name = 'report.paciente'

    programa_ids = fields.Many2many('programa.programa', string="Programas")

    @api.multi
    def get_data(self, programa_id):
        return self.env['ficha.paciente'].sudo().search([('programa', 'in', programa_id.ids)])

    @api.multi
    def check_report(self):
        if not self.programa_ids:
            self.programa_ids = self.programa_ids.search([])
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_paciente',
            'target': 'new',
        }
