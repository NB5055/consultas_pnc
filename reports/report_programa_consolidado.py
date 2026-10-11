import calendar
from datetime import date

from odoo import fields, models
from odoo.exceptions import UserError


def discount_report_related(self, obj):
    consulta_updated_ids = []
    for consulta_id in obj:
        discount_report = self.env['consultas.tratamiento'].search([('discount_report', '=', consulta_id[0])])
        if discount_report:
            for consulta_obj in obj:
                discount_2 = 0
                discount_3 = 0

                if consulta_obj[0] in discount_report.mapped('id'):
                    discount_2 += consulta_obj[2]
                    discount_3 += consulta_obj[3]
                consulta2 = consulta_id[2] - discount_2
                consulta3 = consulta_id[3] - discount_3

                consulta_id = (consulta_id[0],
                               consulta_id[1],
                               consulta2 if consulta2 > 0 else consulta_id[2],
                               consulta3 if consulta3 > 0 else consulta_id[3],
                               consulta_id[4],)
            consulta_updated_ids.append(consulta_id)
        else:
            consulta_updated_ids.append(consulta_id)
    return consulta_updated_ids


class InformeReportConsolidado(models.TransientModel):
    _name = "informe.report.programa.consolidado"
    _description = "Informes"

    fecha_inicial = fields.Date(string="Fecha Inicial", required=True)
    fecha_final = fields.Date(string="Fecha Final", required=True)

    def _print_report(self, data):
        raise UserError('Error!')

    def get_consultas(self):
        self.ensure_one()
        end_date = self.fecha_final
        end_day = calendar.monthrange(end_date.year, end_date.month)[1]
        params = {
            'fecha_inicial': self.fecha_inicial,
            'fecha_final': self.fecha_final,
            'year_start': date(self.fecha_inicial.year, 1, 1),
            'year_end': date(end_date.year, end_date.month, end_day),
        }

        query = """select ct.id,ct.name,(coalesce((select sum(atendidos)
                        from operativos op where ct.id = op.name and
                                     fecha >= %(fecha_inicial)s and
                                     fecha <= %(fecha_final)s),0)+
                    (select count(cc.id) from consultas_consultas cc
                        inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                        where ctl.name = ct.id and ctl.fecha >= %(fecha_inicial)s and
                                                   ctl.fecha <= %(fecha_final)s)),
                    (coalesce((select sum(atendidos) from operativos op
                        where ct.id = op.name
                        and fecha >= %(year_start)s
                         and fecha <= %(year_end)s),0)+
                    (select count(cc.id) from consultas_consultas cc
                        inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                        where ctl.name = ct.id
                        and ctl.fecha >= %(year_start)s
                         and ctl.fecha <= %(year_end)s)),ct.category
                from consultas_tratamiento ct group by ct.id"""

        self.env.flush_all()
        self.env.cr.execute(query, params)

        def getKey(item):
            return item[1] or ''

        obj = self.env.cr.fetchall()
        obj = discount_report_related(self, obj)
        return sorted(obj, key=getKey)

    def check_report(self):
        action = self.env.ref('consultas_pnc.menu_report_programa_consolidado').report_action(self, config=False)
        action['report_type'] = 'qweb-html'
        return action

    def print_report(self):
        return self.env.ref('consultas_pnc.menu_report_programa_consolidado').report_action(self, config=False)
