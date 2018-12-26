from openerp import models, fields, api
from openerp.exceptions import UserError


class InformeReportConsolidado(models.TransientModel):
    _name = "informe.report.programa.consolidado"
    _description = "Informes"

    fecha_inicial = fields.Date(string="Fecha Inicial", required=True)
    fecha_final = fields.Date(string="Fecha Final", required=True)

    def _print_report(self, data):
        raise UserError('Error!')

    @api.one
    def get_consultas(self):
        query = """select ct.id,ct.name,(coalesce((select sum(atendidos) 
                        from operativos op where ct.id = op.name and 
                                     fecha >= '""" + self.fecha_inicial + """' and 
                                     fecha <= '""" + self.fecha_final + """'),0)+ 
                    (select count(cc.id) from consultas_consultas cc 
                        inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id 
                        where ctl.name = ct.id and fecha >= '""" + self.fecha_inicial + """' and 
                                                   fecha <= '""" + self.fecha_final + """')),
                    (coalesce((select sum(atendidos) from operativos op where ct.id = op.name),0)+ 
                    (select count(cc.id) from consultas_consultas cc 
                        inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id 
                        where ctl.name = ct.id))
                from consultas_tratamiento ct group by ct.id"""

        self.env.cr.execute(query)
        def getKey(item):
            return item[0]
        obj = self.env.cr.fetchall()
        return sorted(obj, key=getKey)

    @api.multi
    def check_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_programa_consolidado',
            'target': 'new',
            'report_type': 'qweb-html',
        }
