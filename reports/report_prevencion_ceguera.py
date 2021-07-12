from openerp import models, fields, api
from openerp.exceptions import UserError


class PrevencionCegueraReport(models.TransientModel):
    _name = "informe.report.prevencion.ceguera"
    _description = "Informes"

    fecha_inicial = fields.Date(string="Fecha Inicial", required=True)
    fecha_final = fields.Date(string="Fecha Final", required=True)

    def _print_report(self, data):
        raise UserError('Error!')

    @api.one
    def get_data(self):
        programa_ids = self.env['programa.programa'].search_read([], ['name'])
        data = []
        for programa in programa_ids:
            query = """select cr.name,count(*),sum(o.atendidos) 
                          from operativos o 
                          join consultas_tratamiento cr on o.name = cr.id
                          where fecha >= '%s' and 
                                fecha <= '%s' and 
                                programa = %s  
                          group by cr.name;""" % (self.fecha_inicial, self.fecha_final, programa.get('id'))
            self.env.cr.execute(query)

            def getKey(item):
                return item[0]

            obj = self.env.cr.fetchall()
            if obj:
                data.append({'programa': programa.get('name'),
                             'data': sorted(obj, key=getKey)})
        return data

    @api.multi
    def check_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_prevencion_ceguera',
            'target': 'new',
            'report_type': 'qweb-html',
        }

    @api.multi
    def print_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_prevencion_ceguera',
            'target': 'new',
            'report_type': 'qweb-pdf',
        }