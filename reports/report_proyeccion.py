from odoo import api, fields, models
from odoo.exceptions import UserError

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
                              ('12', 'Diciembre')], string="Mes", required=True)
    year = fields.Selection(selection=lambda self: self.env['consultas.proyeccion']._selection_year(),
                            string='Año', required=True)
    programa_ids = fields.Many2many('programa.programa', string="Programas", required=True)
    month_string = fields.Char(string='Month String', compute="_get_month_string")

    def _get_month_string(self):
        labels = dict(self._fields['month']._description_selection(self.env))
        for report in self:
            report.month_string = labels.get(report.month)

    def _print_report(self, data):
        raise UserError('Error!')

    def get_consultas(self, programa):
        self.ensure_one()
        params = {
            'programa': programa,
            'year': self.year,
            'year_number': int(self.year),
            'month': int(self.month),
        }
        query = """(select ct.name as tratamiento,count(ct.name) as sumatoria,pp.id as programa_id,ct.id as consulta_id,
                           (select count(ct2.name) from consultas_consultas cc
                        inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                        inner join consultas_tratamiento ct2 on ctl.name = ct2.id
                        left join programa_programa pp on cc.programa = pp.id
                        where cc.programa = %(programa)s and ct2.id = ct.id
                         and extract(year from ctl.fecha) = %(year_number)s
                         and extract(month from ctl.fecha) <= %(month)s
                        group by ct.name) as year,
                        (coalesce((select proyeccion from consultas_proyeccion cp where cp.programa = %(programa)s
                            and tratamiento_id = ct.id and year = %(year)s),0)) as proyeccion_year,
                        (coalesce(((select proyeccion from consultas_proyeccion where programa = %(programa)s
                            and tratamiento_id = ct.id and year = %(year)s) / 10),0)) as proyeccion_mes
                    from consultas_consultas cc
                        inner join consultas_tratamiento_line ctl on ctl.consulta_id = cc.id
                        inner join consultas_tratamiento ct on ctl.name = ct.id
                        left join programa_programa pp on cc.programa = pp.id
                        where extract(month from ctl.fecha) = %(month)s and
                        extract(year from ctl.fecha) = %(year_number)s and
                        cc.programa = %(programa)s
                        group by ct.name,pp.id,ct.id order by ct.name,pp.id)
                union
                    (select ct.name  as tratamiento,sum(o.atendidos) as sumatoria,programa as programa,ct.id as consulta_id,
                            (select sum(atendidos) from operativos
                                where programa = %(programa)s and name = ct.id
                                and extract(year from fecha) = %(year_number)s
                                and extract(month from fecha) <= %(month)s) as year,
                            (coalesce((select proyeccion from consultas_proyeccion where programa = %(programa)s
                                and tratamiento_id = ct.id and year = %(year)s),0)) as proyeccion_year,
                        (coalesce(((select proyeccion from consultas_proyeccion where programa = %(programa)s
                            and tratamiento_id = ct.id and year = %(year)s) / 10),0)) as proyeccion_mes
                          from operativos o
                          join consultas_tratamiento ct on o.name = ct.id
                          where extract(month from fecha) = %(month)s and
                          extract(year from fecha) = %(year_number)s and
                                programa = %(programa)s
                          group by ct.name,programa,ct.id)
                """
        self.env.flush_all()
        self.env.cr.execute(query, params)

        def getKey(item):
            return item[0] or ''

        obj = self.env.cr.fetchall()
        no_operations(self, obj, programa, self.year, [('category', '!=', 'rh')])
        obj = discount_report_related(self, obj)
        return sorted(obj, key=getKey)

    def check_report(self):
        action = self.env.ref('consultas_pnc.menu_report_proyeccion').report_action(self, config=False)
        action['report_type'] = 'qweb-html'
        return action

    def print_report(self):
        return self.env.ref('consultas_pnc.menu_report_proyeccion').report_action(self, config=False)

    @api.onchange('programa_ids')
    def change_programa_ids(self):
        if self.programa_ids:
            self.programa_ids[len(self.programa_ids) - 1]._origin.sudo().write({"sequence": len(self.programa_ids)})
