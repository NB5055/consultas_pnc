import calendar
from datetime import date

from odoo import api, fields, models
from odoo.exceptions import UserError


def no_operations(self, obj, programa, year, category=None):
    departamento = []
    for ob in obj:
        departamento.append(ob[0])
    year_start = date(int(year), 1, 1)
    year_end = date(int(year), 12, 31)
    for t in self.env['consultas.tratamiento'].search(category or []):
        if t.name not in departamento and programa in t.programa_ids.ids:
            acumulado = self.env['consultas.tratamiento.line'].search_count([('consulta_id.programa', '=', programa),
                                                                             ('name', '=', t.id),
                                                                             ('consulta_id.fecha', '>=', year_start),
                                                                             ('consulta_id.fecha', '<=', year_end)])

            acumulado += sum(self.env['operativos'].search([('programa', '=', programa),
                                                            ('name', '=', t.id),
                                                            ('fecha', '>=', year_start),
                                                            ('fecha', '<=', year_end)]).mapped('atendidos'))

            proyeccion = t.proyeccion.filtered(lambda x: str(year) == x.year and programa == x.programa.id)
            proyeccion_year = proyeccion.proyeccion if proyeccion else False
            obj.append(tuple((t.name, 0, programa, t.id, acumulado, proyeccion_year, (proyeccion_year or 0) // 10)))


def discount_report_related(self, obj):
    consulta_updated_ids = []
    for consulta_id in obj:
        discount_report = self.env['consultas.tratamiento'].search([('discount_report', '=', consulta_id[3])])
        if discount_report:
            for consulta_obj in obj:
                discount_1 = 0
                discount_4 = 0
                discount_5 = 0
                discount_6 = 0
                if consulta_obj[3] in discount_report.mapped('id'):
                    discount_1 += consulta_obj[1]
                    discount_4 += consulta_obj[4]
                    discount_5 += consulta_obj[5]
                    discount_6 += consulta_obj[6]
                consulta1 = consulta_id[1] - discount_1
                consulta4 = consulta_id[4] - discount_4
                consulta5 = consulta_id[5] - discount_5
                consulta6 = consulta_id[6] - discount_6
                consulta_id = (consulta_id[0],
                               consulta1 if consulta1 > 0 else 0,
                               consulta_id[2],
                               consulta_id[3],
                               consulta4 if consulta4 > 0 else 0,
                               consulta5 if consulta5 > 0 else 0,
                               consulta6 if consulta6 > 0 else 0,)
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

    def get_consultas(self, programa):
        self.ensure_one()
        end_date = self.fecha_final
        end_day = calendar.monthrange(end_date.year, end_date.month)[1]
        params = {
            'programa': programa,
            'fecha_inicial': self.fecha_inicial,
            'fecha_final': self.fecha_final,
            'year_start': date(self.fecha_inicial.year, 1, 1),
            'year_end': date(end_date.year, end_date.month, end_day),
            'year': str(end_date.year),
        }

        query = """(select ct.name as tratamiento,count(ct.name) as sumatoria,pp.id as programa_id,ct.id as consulta_id,
                           (select count(ct2.name) from consultas_consultas cc
                        inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                        inner join consultas_tratamiento ct2 on ctl.name = ct2.id
                        left join programa_programa pp on cc.programa = pp.id
                        where cc.programa = %(programa)s and ct2.id = ct.id
                         and cc.fecha >= %(year_start)s
                         and cc.fecha <= %(year_end)s
                        group by ct.name) as year,
                        (coalesce((select proyeccion from consultas_proyeccion where programa = %(programa)s
                            and tratamiento_id = ct.id and year = %(year)s),0)) as proyeccion_year,
                        (coalesce(((select proyeccion from consultas_proyeccion where programa = %(programa)s
                            and tratamiento_id = ct.id and year = %(year)s) / 10),0)) as proyeccion_mes
                    from consultas_consultas cc
                        inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                        inner join consultas_tratamiento ct on ctl.name = ct.id
                        left join programa_programa pp on cc.programa = pp.id
                        where cc.fecha >= %(fecha_inicial)s and cc.fecha <= %(fecha_final)s
                        and cc.programa = %(programa)s
                        group by ct.name,pp.id,ct.id order by ct.name,pp.id)
                union
                    (select ct.name  as tratamiento,sum(o.atendidos) as sumatoria,programa as programa,ct.id as consulta_id,
                            (select sum(atendidos) from operativos op
                                where programa = %(programa)s and ct.id = op.name
                                and fecha >= %(year_start)s
                         and fecha <= %(year_end)s) as year,
                            (coalesce((select proyeccion from consultas_proyeccion where programa = %(programa)s
                                and tratamiento_id = ct.id and year = %(year)s),0)) as proyeccion_year,
                        (coalesce(((select proyeccion from consultas_proyeccion where programa = %(programa)s
                            and tratamiento_id = ct.id and year = %(year)s) / 10),0)) as proyeccion_mes
                          from operativos o
                          join consultas_tratamiento ct on o.name = ct.id
                          where fecha >= %(fecha_inicial)s and
                                fecha <= %(fecha_final)s and
                                category != 'rh' and
                                programa = %(programa)s
                          group by ct.name,programa,ct.id)
                """
        self.env.flush_all()
        self.env.cr.execute(query, params)

        def getKey(item):
            return item[0] or ''

        obj = self.env.cr.fetchall()
        no_operations(self, obj, programa, end_date.year)
        obj = discount_report_related(self, obj)
        return sorted(obj, key=getKey)

    def get_tratamientos(self, consultas):
        tratamiento_ids = []
        for consulta in consultas:
            for tratamiento in consultas[consulta]:
                tratamiento_ids.append(tratamiento[3])
        return self.env['consultas.tratamiento'].search([('id', 'in', tratamiento_ids)], order="name")

    def get_consultas_comparativo(self):
        consultas = {}
        for programa in self.programa_ids:
            consultas[programa.id] = self.get_consultas(programa.id)
        return consultas

    def check_report(self):
        if self.comparativo:
            return self.check_report_comparativo('qweb-html')
        else:
            return self.check_report_individual('qweb-html')

    def print_report(self):
        if self.comparativo:
            return self.check_report_comparativo('qweb-pdf')
        else:
            return self.check_report_individual('qweb-pdf')

    def check_report_individual(self, report_type):
        action = self.env.ref('consultas_pnc.menu_report_programa').report_action(self, config=False)
        action['report_type'] = report_type
        return action

    def check_report_comparativo(self, report_type):
        action = self.env.ref('consultas_pnc.menu_report_programa_comparativo').report_action(self, config=False)
        action['report_type'] = report_type
        return action

    @api.onchange('programa_ids')
    def change_programa_ids(self):
        if self.programa_ids:
            self.programa_ids[len(self.programa_ids) - 1]._origin.sudo().write({"sequence": len(self.programa_ids)})
