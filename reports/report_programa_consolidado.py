import calendar
from datetime import datetime as dt

from openerp import models, fields, api
from openerp.exceptions import UserError
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT


def discount_report_related(self, obj):
    consulta_updated_ids = []
    for consulta_id in obj:
        tratamiento_id = self.env['consultas.tratamiento'].browse(consulta_id[0])
        if tratamiento_id.discount_report:
            for obj_id in obj:
                if obj_id[0] == tratamiento_id.discount_report.id:
                    consulta_id = (consulta_id[0],
                                   consulta_id[1],
                                   consulta_id[2] - obj_id[2],
                                   consulta_id[3] - obj_id[3],
                                   consulta_id[4])
            consulta_updated_ids.append(consulta_id)

        else:
            consulta_updated_ids.append(consulta_id)
    return consulta_updated_ids

# def discount_report_related(self, obj):
#     consulta_updated_ids = []
#     for consulta_id in obj:
#         tratamiento_id = self.env['consultas.tratamiento'].browse(consulta_id[3])
#         discount_report = self.env['consultas.tratamiento'].search([('discount_report', '=', consulta_id[3])])
#         if discount_report:
#             for consulta_obj in obj:
#                 discount_1 = 0
#                 discount_4 = 0
#                 discount_5 = 0
#                 discount_6 = 0
#                 if consulta_obj[3] in discount_report.mapped('id'):
#                     discount_1 += consulta_obj[1]
#                     discount_4 += consulta_obj[4]
#                     discount_5 += consulta_obj[5]
#                     discount_6 += consulta_obj[6]
#                 consulta1 = consulta_id[1] - discount_1
#                 consulta4 = consulta_id[4] - discount_4
#                 consulta5 = consulta_id[5] - discount_5
#                 consulta6 = consulta_id[6] - discount_6
#                 consulta_id = (consulta_id[0],
#                                consulta1 if consulta1 > 0 else consulta_id[1],
#                                consulta_id[2],
#                                consulta_id[3],
#                                consulta4 if consulta4 > 0 else consulta_id[4],
#                                consulta5 if consulta5 > 0 else consulta_id[5],
#                                consulta6 if consulta6 > 0 else consulta_id[6],)
#             consulta_updated_ids.append(consulta_id)
#         else:
#             consulta_updated_ids.append(consulta_id)
#     return consulta_updated_ids



class InformeReportConsolidado(models.TransientModel):
    _name = "informe.report.programa.consolidado"
    _description = "Informes"

    fecha_inicial = fields.Date(string="Fecha Inicial", required=True)
    fecha_final = fields.Date(string="Fecha Final", required=True)

    def _print_report(self, data):
        raise UserError('Error!')

    @api.one
    def get_consultas(self):
        start_date = dt.strptime(self.fecha_inicial, DATE_FORMAT)
        end_date = dt.strptime(self.fecha_final, DATE_FORMAT)
        end_day = calendar.monthrange(end_date.year, end_date.month)[1]

        query = """select ct.id,ct.name,(coalesce((select sum(atendidos) 
                        from operativos op where ct.id = op.name and 
                                     fecha >= '""" + self.fecha_inicial + """' and 
                                     fecha <= '""" + self.fecha_final + """'),0)+ 
                    (select count(cc.id) from consultas_consultas cc 
                        inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id 
                        where ctl.name = ct.id and fecha >= '""" + self.fecha_inicial + """' and 
                                                   fecha <= '""" + self.fecha_final + """')),
                    (coalesce((select sum(atendidos) from operativos op 
                        where ct.id = op.name
                        and fecha >= '""" + str(start_date.year) + """-01-01' 
                    	 and fecha <= '""" + str(end_date.year) + """-""" + str(end_date.month) + """-""" + str(
            end_day) + """'),0)+ 
                    (select count(cc.id) from consultas_consultas cc 
                        inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id 
                        where ctl.name = ct.id
                        and fecha >= '""" + str(start_date.year) + """-01-01' 
                    	 and fecha <= '""" + str(end_date.year) + """-""" + str(end_date.month) + """-""" + str(
            end_day) + """')),ct.category
                from consultas_tratamiento ct group by ct.id"""

        self.env.cr.execute(query)

        def getKey(item):
            return item[1]

        obj = self.env.cr.fetchall()
        obj = discount_report_related(self, obj)
        return sorted(obj, key=getKey)

    @api.multi
    def check_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_programa_consolidado',
            'target': 'new',
            'report_type': 'qweb-html',
        }
