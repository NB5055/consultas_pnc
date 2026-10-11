from odoo import fields, models
from odoo.exceptions import UserError


class PrevencionCegueraReport(models.TransientModel):
    _name = "informe.report.prevencion.ceguera"
    _description = "Informes"

    fecha_inicial = fields.Date(string="Fecha Inicial", required=True)
    fecha_final = fields.Date(string="Fecha Final", required=True)

    def _print_report(self, data):
        raise UserError('Error!')

    def get_data(self):
        self.ensure_one()
        programa_ids = self.env['programa.programa'].search_read([], ['name'])
        data = []
        self.env.flush_all()
        for programa in programa_ids:
            query = """select cr.name,count(*),sum(o.atendidos)
                          from operativos o
                          join consultas_tratamiento cr on o.name = cr.id
                          where fecha >= %s and
                                fecha <= %s and
                                programa = %s
                          group by cr.name;"""
            self.env.cr.execute(query, (self.fecha_inicial, self.fecha_final, programa.get('id')))

            def getKey(item):
                return item[0] or ''

            obj = self.env.cr.fetchall()
            if obj:
                data.append({'programa': programa.get('name'),
                             'data': sorted(obj, key=getKey)})
        return data

    def check_report(self):
        action = self.env.ref('consultas_pnc.menu_report_prevencion_ceguera').report_action(self, config=False)
        action['report_type'] = 'qweb-html'
        return action

    def print_report(self):
        return self.env.ref('consultas_pnc.menu_report_prevencion_ceguera').report_action(self, config=False)
