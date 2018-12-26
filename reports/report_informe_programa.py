from openerp import models, fields, api
from openerp.exceptions import UserError


def no_operations(self, obj, programa):
    departamento = []
    for ob in obj:
        departamento.append(ob[0])
    for t in self.env['consultas.tratamiento'].search([]):
        if t.name not in departamento:
            obj.append(tuple((t.name, 0, programa, t.id, 0, 0, 0)))


class InformeReport(models.TransientModel):
    _name = "informe.report.programa"
    _description = "Informes"
    # Informe General

    fecha_inicial = fields.Date(string="Fecha Inicial", required=True)
    fecha_final = fields.Date(string="Fecha Final", required=True)
    programa_ids = fields.Many2many('programa.programa', string="Programas", required=True)
    comparativo = fields.Boolean(string="Comparativo", default=False)

    def _print_report(self, data):
        raise UserError('Error!')

    @api.one
    def get_consultas(self, programa):
        year = fields.date.today().year
        query = """(select ct.name as tratamiento,count(ct.name) as sumatoria,pp.id as programa,ct.id as consulta_id,
                           (select count(ct2.name) from consultas_consultas cc
                    	inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                    	inner join consultas_tratamiento ct2 on ctl.name = ct2.id
                    	left join programa_programa pp on cc.programa = pp.id
                    	where programa = """ + str(programa) + """ and ct2.id = ct.id
                    	 and extract(year from fecha) = '""" + str(year) + """'
                    	group by ct.name) as year,
                    	(coalesce((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = '""" + str(year) + """'),0)) as proyeccion_year,
                    	(coalesce(((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = '""" + str(year) + """') / 10),0)) as proyeccion_mes
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
                                and extract(year from fecha) = '""" + str(year) + """') as year,
                            (coalesce((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = '""" + str(year) + """'),0)) as proyeccion_year,
                    	(coalesce(((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = '""" + str(year) + """') / 10),0)) as proyeccion_mes
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
        no_operations(self, obj, programa)
        return sorted(obj, key=getKey)

    def get_tratamientos(self):
        return self.env['consultas.tratamiento'].search([], order="name")

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