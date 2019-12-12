# -*- coding: utf-8 -*-
from openerp import models, fields, api
from openerp.exceptions import UserError
from datetime import datetime
from .report_informe_programa import no_operations, discount_report_related


class ProyeccionReport(models.TransientModel):
    _name = "proyeccion.report.programa"
    _description = "Informes"

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
    month_string = fields.Char(string='Month String', compute="_get_month_string")

    def _get_month_string(self):
        labels = self.fields_get(["month"])['month']['selection']
        self.month_string = [x[1] for x in labels if x[0] == self.month][0]

    def _print_report(self, data):
        raise UserError('Error!')

    @api.one
    def get_consultas(self, programa):
        query = """(select ct.name as tratamiento,count(ct.name) as sumatoria,pp.id as programa_id,ct.id as consulta_id,
                           (select count(ct2.name) from consultas_consultas cc
                    	inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                    	inner join consultas_tratamiento ct2 on ctl.name = ct2.id
                    	left join programa_programa pp on cc.programa = pp.id
                    	where programa_id = """ + str(programa) + """ and ct2.id = ct.id
                    	 and extract(year from fecha) = """ + str(self.year) + """
                    	 and extract(month from fecha) <= """ + str(self.month) + """
                    	group by ct.name) as year,
                    	(coalesce((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = """ + str(self.year) + """),0)) as proyeccion_year,
                    	(coalesce(((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = """ + str(self.year) + """) / 10),0)) as proyeccion_mes
                    from consultas_consultas cc
                    	inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                    	inner join consultas_tratamiento ct on ctl.name = ct.id
                    	left join programa_programa pp on cc.programa = pp.id
                    	where extract(month from fecha) = """ + self.month + """ and
                    	extract(year from fecha) = """ + str(self.year) + """ and
                    	programa_id = """ + str(programa) + """
                    	group by ct.name,pp.id,ct.id order by ct.name,pp.id)
                union
                    (select ct.name  as tratamiento,sum(o.atendidos) as sumatoria,programa as programa,ct.id as consulta_id,
                            (select sum(atendidos) from operativos 
                                where programa = """ + str(programa) + """ and name = ct.id 
                                and extract(year from fecha) = """ + str(self.year) + """
                                and extract(month from fecha) <= """ + str(self.month) + """) as year,
                            (coalesce((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = """ + str(self.year) + """),0)) as proyeccion_year,
                    	(coalesce(((select proyeccion from consultas_proyeccion where programa = """ + str(
            programa) + """ and tratamiento_id = ct.id and year = """ + str(self.year) + """) / 10),0)) as proyeccion_mes
                          from operativos o
                          join consultas_tratamiento ct on o.name = ct.id
                          where extract(month from fecha) = """ + self.month + """ and
                          extract(year from fecha) = """ + str(self.year) + """ and
                                programa = """ + str(programa) + """
                          group by ct.name,programa,ct.id)
                """
        self.env.cr.execute(query)

        def getKey(item):
            return item[0]

        obj = self.env.cr.fetchall()
        no_operations(self, obj, programa, self.year)
        obj = discount_report_related(self, obj)
        return sorted(obj, key=getKey)

    @api.multi
    def check_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_proyeccion',
            'target': 'new',
            'report_type': 'qweb-html',
        }

    @api.multi
    def print_report(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'consultas_pnc.report_proyeccion',
            'target': 'new',
            'report_type': 'qweb-pdf',
        }

    @api.onchange('programa_ids')
    def change_programa_ids(self):
        if self.programa_ids:
            self.programa_ids[len(self.programa_ids)-1].sudo().write({"sequence": len(self.programa_ids)})