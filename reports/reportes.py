# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import UserError
from datetime import datetime
import calendar


def no_operations(self, obj, programa):
    departamento = []
    for ob in obj:
        departamento.append(ob[0])
    for t in self.env['consultas.tratamiento'].search([]):
        if t.name not in departamento:
            obj.append(tuple((t.name, 0, programa, t.id, 0)))


def _get_operativos(self, programa, tratamiento_id, data, month, proyeccion, year):
    last_day = calendar.monthrange(int(year), int(month))[1]
    date_start = year + '-' + month + '-01'
    atendidos = 0.0
    operativo_month_ids = self.env['operativos'].search([('name', '=', tratamiento_id.id),
                                                         ('programa', '=', programa),
                                                         ('fecha', '>=', date_start),
                                                         ('fecha', '<=',
                                                          year + '-' + month + '-' + str(last_day))])
    if operativo_month_ids:
        for operativo_id in operativo_month_ids:
            atendidos += operativo_id.atendidos
        if data.get(tratamiento_id.name):
            data[tratamiento_id.name] += atendidos
        else:
            proyeccion[tratamiento_id.name] = self.env['consultas.proyeccion'].search([('year', '=', year),
                                                                                       ('tratamiento_id', '=',
                                                                                        tratamiento_id.id),
                                                                                       ("programa", "=",
                                                                                        programa)]).proyeccion or 0
            data[tratamiento_id.name] = atendidos


class InformeReport(models.TransientModel):
    _name = "informe.report.programa"
    _description = "Informes"
    # Informe General

    fecha_inicial = fields.Date(string="Fecha Inicial", required=True)
    fecha_final = fields.Date(string="Fecha Final", required=True)
    programa_ids = fields.Many2many('programa.programa', string="Programas", required=True)

    def _print_report(self, data):
        raise UserError('Error!')

    @api.one
    def get_consultas(self, programa):
        year = datetime.strptime(self.fecha_inicial, '%Y-%m-%d').date().year
        query = """(select ct.name,count(ct.name),pp.id,ct.id,
                           (select count(ct2.name) from consultas_consultas cc
                    	inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                    	inner join consultas_tratamiento ct2 on ctl.name = ct2.id
                    	left join programa_programa pp on cc.programa = pp.id
                    	where programa = """ + str(programa) + """ and ct2.id = ct.id
                    	group by ct.name)
                    from consultas_consultas cc
                    	inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                    	inner join consultas_tratamiento ct on ctl.name = ct.id
                    	left join programa_programa pp on cc.programa = pp.id
                    	where fecha >= '""" + self.fecha_inicial + """' and fecha <= '""" + self.fecha_final + """'
                    	and programa = """ + str(programa) + """
                    	group by ct.name,pp.id,ct.id order by ct.name,pp.id)
                union
                    (select cr.name,count(*),programa,cr.id,sum(o.atendidos)
                          from operativos o
                          join consultas_tratamiento cr on o.name = cr.id
                          where fecha >= '""" + self.fecha_inicial + """' and
                                fecha <= '""" + self.fecha_final + """' and
                                programa = """ + str(programa) + """
                          group by cr.name,programa,cr.id)
                """

        self.env.cr.execute(query)

        def getKey(item):
            return item[0]

        obj = self.env.cr.fetchall()
        no_operations(self, obj, programa)

        return sorted(obj, key=getKey)

    @api.multi
    def check_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_programa',
            'target': 'new',
            'report_type': 'qweb-html',
        }


class ProyeccionReport(models.TransientModel):
    _name = "proyeccion.report.programa"
    _description = "Informes"
    # Informe Resultado

    month = fields.Selection([('1', 'Enero'),
                              ('2', 'Febrero'),
                              ('3', 'Marzo'),
                              ('4', 'Abril'),
                              ('5', 'Mayo'),
                              ('6', 'Junio'),
                              ('7', 'Julio'),
                              ('8', 'Agosto'),
                              ('9', 'Septiembre'),
                              ('10', 'Octubre'),
                              ('11', 'Noviembre'),
                              ('12', 'Diciembre')], string="Mes", required=True, default=str(datetime.now().month))
    year = fields.Selection([(num, str(num)) for num in range(2000, (datetime.now().year) + 1)], string='Año',
                            required=True, default=datetime.now().year)
    programa_ids = fields.Many2many('programa.programa', string="Programas", required=True)
    month_string = fields.Char(string='Month String')

    def _print_report(self, data):
        raise UserError('Error!')

    @api.one
    def get_consultas(self, programa):
        consulta_obj = self.env['consultas.consultas']
        data = {}
        data_month = {}
        proyeccion = {}
        result = []
        tratamiento_ids = self.env['consultas.tratamiento'].search([])
        consulta_data = consulta_obj.search([('programa', '=', programa),
                                             ('fecha', '>=', str(self.year) + '-01-01')])
        for consulta_id in consulta_data:
            self._get_data_proyeccion(consulta_id, 'tratamiento', data, data_month, proyeccion, programa)
        for tratamiento_id in tratamiento_ids:
            _get_operativos(self, programa, tratamiento_id, data_month, str(self.month), proyeccion, str(self.year))
            _get_operativos(self, programa, tratamiento_id, data, "01", proyeccion, str(self.year))
        for a in data:
            proyeccion_mensual = proyeccion.get(a, 1) / 12
            obj = {
                'description': a,
                'month': int(data_month.get(a, 0)),
                'year': int(data.get(a, 0)),
                'proyection_month': proyeccion_mensual,
                'proyection_year': proyeccion.get(a, 0),
                'percent_month': ("{:,.2f}".format(
                    (float(data_month.get(a, 0)) / float(proyeccion_mensual)) * 100)) if proyeccion_mensual != 0 else 0,
                'percent_year': (
                    "{:,.2f}".format((float(data.get(a, 0)) / float(proyeccion.get(a, 0))) * 100)) if proyeccion.get(
                    a) != 0 else 0
            }
            result.append(obj)

        def getKey(item):
            return item.get('description')

        return sorted(result, key=getKey)

    def _get_data_proyeccion(self, consulta_id, param, data, data_month, proyeccion, programa):
        if consulta_id[param]:
            for consulta_param in consulta_id[param]:
                if data.get(consulta_param.name.name):
                    if datetime.strptime(consulta_id.fecha, '%Y-%m-%d').month <= int(self.month):
                        data[consulta_param.name.name] += 1.0
                    if datetime.strptime(consulta_id.fecha, '%Y-%m-%d').month == int(self.month):
                        if consulta_param.name.name in data_month:
                            data_month[consulta_param.name.name] += 1.0
                        else:
                            data_month[consulta_param.name.name] = 1.0
                else:
                    if datetime.strptime(consulta_id.fecha, '%Y-%m-%d').month <= int(self.month):
                        data[consulta_param.name.name] = 1.0
                    if datetime.strptime(consulta_id.fecha, '%Y-%m-%d').month == int(self.month):
                        data_month[consulta_param.name.name] = 1.0
                if consulta_param.name:
                    proyeccion[consulta_param.name.name] = consulta_param.name.proyeccion.search(
                        [('year', '=', self.year),
                         (param + '_id', '=',
                          consulta_param.name.id),
                         ("programa", "=",
                          programa)]).proyeccion or 0
                else:
                    proyeccion[consulta_param.name.name] = 0

    @api.multi
    def check_report(self):
        labels = self.fields_get(["month"])['month']['selection']
        self.month_string = [x[1] for x in labels if x[0] == self.month][0]
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_proyeccion',
            'target': 'new',
            'report_type': 'qweb-html',
        }
