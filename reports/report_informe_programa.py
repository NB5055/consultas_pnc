from openerp import models, fields, api
from openerp.exceptions import UserError
from datetime import datetime as dt
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
import calendar


def no_operations(self, obj, programa, year):
    departamento = []
    for ob in obj:
        departamento.append(ob[0])
    for t in self.env['consultas.tratamiento'].search([]):
        if t.name not in departamento and programa in t.programa_ids.ids:
            acumulado = len(self.env['consultas.tratamiento.line'].search([('consulta_id.programa', '=', programa),
                                                                           ('name', '=', t.id),
                                                                           ('consulta_id.fecha', '>=',
                                                                            str(year) + '-01-01'),
                                                                           ('consulta_id.fecha', '<=',
                                                                            str(year) + '-12-31')]))
            proyeccion = t.proyeccion.filtered(lambda x: year == x.year and programa == x.programa.id)
            obj.append(tuple((t.name, 0, programa, t.id, acumulado, proyeccion.proyeccion, proyeccion.proyeccion / 10)))


def discount_report_related(self, obj):
    consulta_updated_ids = []
    for consulta_id in obj:
        tratamiento_id = self.env['consultas.tratamiento'].browse(consulta_id[3])
        if tratamiento_id.discount_report:
            for obj_id in obj:
                if obj_id[3] == tratamiento_id.discount_report.id:
                    consulta_id = (consulta_id[0],
                                   consulta_id[1] - obj_id[1],
                                   consulta_id[2],
                                   consulta_id[3],
                                   consulta_id[4] - obj_id[4],
                                   consulta_id[5] - obj_id[5],
                                   consulta_id[6] - obj_id[6],)
            consulta_updated_ids.append(consulta_id)
        else:
            consulta_updated_ids.append(consulta_id)
    return consulta_updated_ids


class InformeReport(models.TransientModel):
    _name = "informe.report.programa"
    _description = "Informes"
    # Informe General

    fecha_inicial = fields.Date(string="Fecha Inicial", required=True)
    fecha_final = fields.Date(string="Fecha Final", required=True)
    programa_ids = fields.Many2many('programa.programa', string="Programas", required=True)
    comparativo = fields.Boolean(string="Unificado Centro RBC", default=False)

    def _print_report(self, data):
        raise UserError('Error!')

    @api.one
    def get_consultas(self, programa):
        year = fields.date.today().year
        start_date = dt.strptime(self.fecha_inicial, DATE_FORMAT)
        end_date = dt.strptime(self.fecha_final, DATE_FORMAT)
        end_day = calendar.monthrange(end_date.year, end_date.month)[1]

        query = """(select ct.name as tratamiento,count(ct.name) as sumatoria,pp.id as programa,ct.id as consulta_id,
                           (select count(ct2.name) from consultas_consultas cc
                    	inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                    	inner join consultas_tratamiento ct2 on ctl.name = ct2.id
                    	left join programa_programa pp on cc.programa = pp.id
                    	where programa = """ + str(programa) + """ and ct2.id = ct.id
                    	 and fecha >= '""" + str(start_date.year) + """-01-01' 
                    	 and fecha <= '""" + str(end_date.year) + """-""" + str(end_date.month) + """-""" + str(
            end_day) + """'
                    	group by ct.name) as year,
                    	(coalesce((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = '""" + str(end_date.year) + """'),0)) as proyeccion_year,
                    	(coalesce(((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = '""" + str(end_date.year) + """') / 10),0)) as proyeccion_mes
                    from consultas_consultas cc
                    	inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                    	inner join consultas_tratamiento ct on ctl.name = ct.id
                    	left join programa_programa pp on cc.programa = pp.id
                    	where fecha >= '""" + self.fecha_inicial + """' and fecha <= '""" + self.fecha_final + """'
                    	and programa = """ + str(programa) + """
                    	group by ct.name,pp.id,ct.id order by ct.name,pp.id)
                union
                    (select ct.name  as tratamiento,sum(o.atendidos) as sumatoria,programa as programa,ct.id as consulta_id,
                            (select sum(atendidos) from operativos 
                                where programa = """ + str(programa) + """ 
                                and fecha >= '""" + str(start_date.year) + """-01-01' 
                    	 and fecha <= '""" + str(end_date.year) + """-""" + str(end_date.month) + """-""" + str(
            end_day) + """') as year,
                            (coalesce((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = '""" + str(end_date.year) + """'),0)) as proyeccion_year,
                    	(coalesce(((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = '""" + str(end_date.year) + """') / 10),0)) as proyeccion_mes
                          from operativos o
                          join consultas_tratamiento ct on o.name = ct.id
                          where fecha >= '""" + self.fecha_inicial + """' and
                                fecha <= '""" + self.fecha_final + """' and
                                programa = """ + str(programa) + """
                          group by ct.name,programa,ct.id)
                """
        self.env.cr.execute(query)

        def getKey(item):
            return item[0]

        obj = self.env.cr.fetchall()
        no_operations(self, obj, programa, end_date.year)
        obj = discount_report_related(self, obj)
        return sorted(obj, key=getKey)

    def get_tratamientos(self, consultas):
        tratamiento_ids = []
        for consulta in consultas:
            for tratamiento in consultas[consulta][0]:
                tratamiento_ids.append(tratamiento[3])
        return self.env['consultas.tratamiento'].search([('id', 'in', tratamiento_ids)], order="name")

    def get_consultas_comparativo(self):
        consultas = {}
        for programa in self.programa_ids:
            consultas[programa.id] = self.get_consultas(programa.id)
        return consultas

    @api.multi
    def check_report(self):
        if self.comparativo:
            return self.check_report_comparativo()
        else:
            return self.check_report_individual()

    @api.multi
    def check_report_individual(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_programa',
            'target': 'new',
            'report_type': 'qweb-html',
        }

    @api.multi
    def check_report_comparativo(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_programa_comparativo',
            'target': 'new',
            'report_type': 'qweb-html',
        }
