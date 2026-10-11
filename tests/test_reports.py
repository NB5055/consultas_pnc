import re
from datetime import date

from odoo.tests import tagged

from .common import ConsultasPncCommon

PNG = ('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
       'YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')


@tagged('post_install', '-at_install')
class TestReports(ConsultasPncCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.zeta = cls.env['consultas.tratamiento'].create({
            'name': 'Zeta', 'programa_ids': [(6, 0, cls.programa.ids)]})
        cls.env['consultas.proyeccion'].create({
            'tratamiento_id': cls.terapia.id, 'programa': cls.programa.id, 'year': '2024', 'proyeccion': 120})
        cls._create_consulta(date(2024, 1, 10), cls.terapia)
        cls._create_consulta(date(2024, 3, 5), cls.terapia)
        cls._create_consulta(date(2024, 3, 20), cls.terapia)
        cls._create_consulta(date(2024, 3, 7), cls.terapia, programa=cls.programa_2)
        cls.env['operativos'].create([
            {'name': cls.operativo.id, 'programa': cls.programa.id, 'fecha': date(2024, 2, 10), 'atendidos': 10},
            {'name': cls.operativo.id, 'programa': cls.programa.id, 'fecha': date(2024, 3, 15), 'atendidos': 40},
        ])
        cls.p1 = cls.programa.id
        cls.p2 = cls.programa_2.id
        cls.filas_p1 = [
            ('Operativo Visual', 40, cls.p1, cls.operativo.id, 50, 0, 0),
            ('Terapia', 2, cls.p1, cls.terapia.id, 3, 120, 12),
            ('Zeta', 0, cls.p1, cls.zeta.id, 0, False, 0),
        ]

    def _render(self, xmlid, wizard):
        html = self.env['ir.actions.report']._render_qweb_html(xmlid, wizard.ids)[0].decode()
        self.assertIn('Patronato Nacional de Ciegos', html)
        return html

    def _celdas(self, html):
        return [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', celda)).strip()
                for celda in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', html, re.S)]

    def _informe(self, **kwargs):
        vals = {'fecha_inicial': date(2024, 3, 1), 'fecha_final': date(2024, 3, 31),
                'programa_ids': [(6, 0, self.programa.ids)]}
        vals.update(kwargs)
        return self.env['informe.report.programa'].create(vals)

    def test_informe_programa(self):
        self.env.company.logo = PNG
        wizard = self._informe()
        filas = wizard.get_consultas(self.p1)
        self.assertEqual(filas, self.filas_p1)
        self.assertIs(filas[2][5], False)
        self.assertEqual(wizard.get_consultas(self.p2), [('Terapia', 1, self.p2, self.terapia.id, 1, 0, 0)])

        accion = wizard.check_report()
        self.assertEqual(accion['type'], 'ir.actions.report')
        self.assertEqual(accion['report_name'], 'consultas_pnc.report_programa')
        self.assertEqual(accion['report_type'], 'qweb-html')
        self.assertEqual(accion['context']['active_ids'], wizard.ids)
        self.assertEqual(wizard.print_report()['report_type'], 'qweb-pdf')

        html = self._render('consultas_pnc.menu_report_programa', wizard)
        self.assertIn('Desde', html)
        self.assertIn('01-03-2024', html)
        self.assertIn('31-03-2024', html)
        self.assertIn('data:image/png;base64,', html)
        celdas = self._celdas(html)
        inicio = celdas.index('Operativo Visual')
        self.assertEqual(celdas[inicio:inicio + 7], ['Operativo Visual', '40', '50', '0', '0', '0 %', '0 %'])
        inicio = celdas.index('Terapia')
        self.assertEqual(celdas[inicio:inicio + 7], ['Terapia', '2', '3', '12', '120', '16.67 %', '2.50 %'])
        inicio = celdas.index('Zeta')
        self.assertEqual(celdas[inicio:inicio + 7], ['Zeta', '0', '0', '0', '', '0 %', '0 %'])
        inicio = celdas.index('Totales')
        self.assertEqual(celdas[inicio:inicio + 3], ['Totales', '42', '53'])

    def test_informe_programa_descuento(self):
        baja = self.env['consultas.tratamiento'].create({
            'name': 'Baja', 'category': 'rh', 'discount_report': self.terapia.id,
            'programa_ids': [(6, 0, self.programa.ids)]})
        self._create_consulta(date(2024, 3, 25), baja)
        filas = self._informe().get_consultas(self.p1)
        self.assertEqual(filas, [
            ('Baja', 1, self.p1, baja.id, 1, 0, 0),
            ('Operativo Visual', 40, self.p1, self.operativo.id, 50, 0, 0),
            ('Terapia', 1, self.p1, self.terapia.id, 2, 120, 12),
            ('Zeta', 0, self.p1, self.zeta.id, 0, False, 0),
        ])
        consolidado = self.env['informe.report.programa.consolidado'].create({
            'fecha_inicial': date(2024, 3, 1), 'fecha_final': date(2024, 3, 31)})
        self.assertEqual(consolidado.get_consultas(), [
            (baja.id, 'Baja', 1, 1, 'rh'),
            (self.operativo.id, 'Operativo Visual', 40, 50, 'pc'),
            (self.terapia.id, 'Terapia', 2, 3, 'rh'),
            (self.zeta.id, 'Zeta', 0, 0, None),
        ])

    def test_informe_programa_comparativo(self):
        wizard = self._informe(comparativo=True, programa_ids=[(6, 0, (self.programa | self.programa_2).ids)])
        consultas = wizard.get_consultas_comparativo()
        self.assertEqual(consultas, {
            self.p1: self.filas_p1,
            self.p2: [('Terapia', 1, self.p2, self.terapia.id, 1, 0, 0)],
        })
        self.assertEqual(wizard.get_tratamientos(consultas), self.operativo | self.terapia | self.zeta)
        accion = wizard.check_report()
        self.assertEqual(accion['report_name'], 'consultas_pnc.report_programa_comparativo')
        self.assertEqual(accion['report_type'], 'qweb-html')
        self.assertEqual(wizard.print_report()['report_type'], 'qweb-pdf')

        html = self._render('consultas_pnc.menu_report_programa_comparativo', wizard)
        celdas = self._celdas(html)
        programas = wizard.programa_ids.mapped('name')
        self.assertEqual(celdas[4:7], programas + ['Total'])
        pos = {programa: indice for indice, programa in enumerate(programas)}
        uno, dos = pos['Programa Uno'] * 2, pos['Programa Dos'] * 2

        inicio = celdas.index('Terapia')
        fila = celdas[inicio + 1:inicio + 19]
        self.assertEqual(fila[uno:uno + 2], ['2.0', '3.0'])
        self.assertEqual(fila[dos:dos + 2], ['1.0', '1.0'])
        self.assertEqual(fila[4:6], ['3.0', '4.0'])
        self.assertEqual(fila[6 + uno:6 + uno + 2], ['12.0', '120.0'])
        self.assertEqual(fila[6 + dos:6 + dos + 2], ['0.0', '0.0'])
        self.assertEqual(fila[10:12], ['12.0', '120.0'])
        self.assertEqual(fila[12 + uno:12 + uno + 2], ['16.67%', '2.44%'])
        self.assertEqual(fila[12 + dos:12 + dos + 2], ['0.0%', '100.00%'])

        inicio = celdas.index('Operativo Visual')
        fila = celdas[inicio + 1:inicio + 7]
        self.assertEqual(fila[uno:uno + 2], ['40.0', '50.0'])
        self.assertEqual(fila[dos:dos + 2], ['0.0', '0.0'])
        self.assertEqual(fila[4:6], ['40.0', '50.0'])

        inicio = celdas.index('Total General')
        self.assertEqual(celdas[inicio + 5:inicio + 7], ['85.0', '107.0'])

    def test_proyeccion(self):
        wizard = self.env['proyeccion.report.programa'].create({
            'month': '3', 'year': '2024', 'programa_ids': [(6, 0, self.programa.ids)]})
        self.assertEqual(wizard.month_string, 'Marzo')
        filas = wizard.get_consultas(self.p1)
        self.assertEqual(filas, self.filas_p1)
        self.assertIs(filas[2][5], False)
        febrero = self.env['proyeccion.report.programa'].create({
            'month': '2', 'year': '2024', 'programa_ids': [(6, 0, self.programa.ids)]})
        self.assertEqual(febrero.get_consultas(self.p1), [
            ('Operativo Visual', 10, self.p1, self.operativo.id, 10, 0, 0),
            ('Zeta', 0, self.p1, self.zeta.id, 0, False, 0),
        ])
        self.assertEqual(wizard.check_report()['report_type'], 'qweb-html')
        accion = wizard.print_report()
        self.assertEqual(accion['report_type'], 'qweb-pdf')
        self.assertEqual(accion['report_name'], 'consultas_pnc.report_proyeccion')

        html = self._render('consultas_pnc.menu_report_proyeccion', wizard)
        self.assertRegex(html, r'Marzo\s*/\s*2024')
        celdas = self._celdas(html)
        inicio = celdas.index('Terapia')
        self.assertEqual(celdas[inicio:inicio + 7], ['Terapia', '2', '3', '12', '120', '16.67 %', '2.50 %'])
        inicio = celdas.index('Operativo Visual')
        self.assertEqual(celdas[inicio:inicio + 7], ['Operativo Visual', '40', '50', '0', '0', '0 %', '0 %'])
        inicio = celdas.index('Totales')
        self.assertEqual(celdas[inicio:inicio + 3], ['Totales', '42', '53'])

    def test_programa_consolidado(self):
        wizard = self.env['informe.report.programa.consolidado'].create({
            'fecha_inicial': date(2024, 3, 1), 'fecha_final': date(2024, 3, 31)})
        self.assertEqual(wizard.get_consultas(), [
            (self.operativo.id, 'Operativo Visual', 40, 50, 'pc'),
            (self.terapia.id, 'Terapia', 3, 4, 'rh'),
            (self.zeta.id, 'Zeta', 0, 0, None),
        ])
        self.assertEqual(wizard.check_report()['report_type'], 'qweb-html')
        self.assertEqual(wizard.print_report()['report_type'], 'qweb-pdf')

        html = self._render('consultas_pnc.menu_report_programa_consolidado', wizard)
        celdas = self._celdas(html)
        inicio = celdas.index('Rehabilitacion')
        self.assertEqual(celdas[inicio + 5:inicio + 11], ['Terapia', '3', '4', 'Totales', '3', '4'])
        inicio = celdas.index('Prevencion Ceguera')
        self.assertEqual(celdas[inicio + 5:inicio + 11], ['Operativo Visual', '40', '50', 'Totales', '40', '50'])
        inicio = celdas.index('Zeta')
        self.assertEqual(celdas[inicio:inicio + 6], ['Zeta', '0', '0', 'Totales', '0', '0'])

    def test_prevencion_ceguera(self):
        wizard = self.env['informe.report.prevencion.ceguera'].create({
            'fecha_inicial': date(2024, 1, 1), 'fecha_final': date(2024, 3, 31)})
        self.assertEqual(wizard.get_data(), [
            {'programa': 'Programa Uno', 'data': [('Operativo Visual', 2, 50)]}])
        self.assertEqual(wizard.check_report()['report_type'], 'qweb-html')
        self.assertEqual(wizard.print_report()['report_type'], 'qweb-pdf')

        html = self._render('consultas_pnc.menu_report_prevencion_ceguera', wizard)
        celdas = self._celdas(html)
        inicio = celdas.index('Programa Uno')
        self.assertEqual(celdas[inicio + 4:inicio + 7], ['Operativo Visual', '2', '50'])
        self.assertIn('01-01-2024', html)

    def test_asistencia_economica(self):
        patrocinador = self.env['res.partner'].create({'name': 'Patrocinador Uno'})
        parentesco = self.env['ficha.paciente.parentesco'].create({'name': 'Beca'})
        self.env['ficha.paciente.ayuda.economica'].create([
            {'ayuda_economica_id': self.paciente.id, 'name': patrocinador.id, 'parentesco': parentesco.id,
             'monto': monto, 'fecha': fecha}
            for monto, fecha in ((500, date(2024, 3, 10)), (250.5, date(2024, 3, 20)), (100, date(2024, 5, 1)))
        ])
        wizard = self.env['report.asistencia.economica'].create({
            'fecha_inicial': date(2024, 3, 1), 'fecha_final': date(2024, 3, 31)})
        accion = wizard.check_report()
        self.assertEqual(accion['report_type'], 'qweb-html')
        self.assertEqual(accion['report_name'], 'consultas_pnc.report_asistencia_economica')
        self.assertEqual(wizard.print_report()['report_type'], 'qweb-pdf')
        self.assertIn(self.paciente, wizard.paciente_ids)
        self.assertEqual(wizard.programa_ids, self.programa | self.programa_2)
        self.assertEqual(wizard.get_asistencias().mapped('monto'), [500, 250.5])
        self.assertEqual(wizard.paciente_asistencia_ids(self.paciente), wizard.get_asistencias())
        self.assertEqual(wizard.get_paciente_filtered(self.programa), self.paciente)
        self.assertEqual(sorted(wizard.get_totales(), key=lambda total: total['programa']), [
            {'programa': 'Programa Dos', 'total_programa': 0},
            {'programa': 'Programa Uno', 'total_programa': 750.5},
        ])

        html = self._render('consultas_pnc.menu_report_asistencia_Economica', wizard)
        celdas = self._celdas(html)
        inicio = celdas.index('Perez Juan ( 001-0000000-1 ) (Programa Uno)')
        self.assertEqual(celdas[inicio + 5:inicio + 8], ['1', 'Patrocinador Uno', 'Beca'])
        self.assertIn('500.00', celdas[inicio + 8])
        self.assertEqual(celdas[inicio + 9], '2024-03-10')
        self.assertIn('250.50', celdas[inicio + 13])
        inicio = celdas.index('Total :')
        self.assertEqual(celdas[inicio + 1], '750.5')
        inicio = celdas.index('Programa Uno')
        self.assertEqual(celdas[inicio + 1], '750.5')
        inicio = celdas.index('Total General')
        self.assertIn('750.50', celdas[inicio + 1])

    def test_listado_pacientes(self):
        self.paciente.write({
            'telefonos': [(0, 0, {'name': '809-555-0001', 'tipo': 'c'}), (0, 0, {'name': '809-555-0002', 'tipo': 'r'})],
            'enfermedades': [(0, 0, {'name': self.env['ficha.paciente.enfermedades'].create({'name': 'Baja vision'}).id})],
        })
        wizard = self.env['report.paciente'].create({})
        accion = wizard.check_report()
        self.assertEqual(accion['report_type'], 'qweb-html')
        self.assertEqual(accion['report_name'], 'consultas_pnc.report_paciente')
        self.assertEqual(wizard.programa_ids, self.programa | self.programa_2)
        self.assertEqual(wizard.get_data(self.programa), self.paciente)
        self.assertFalse(wizard.get_data(self.programa_2))

        html = self._render('consultas_pnc.report_report_paciente', wizard)
        celdas = self._celdas(html)
        inicio = celdas.index('Programa Uno')
        self.assertEqual(celdas[inicio + 7:inicio + 14], [
            '1', 'Perez Juan', '001-0000000-1', 'Calle 1', '809-555-0001,809-555-0002', '30', 'Baja vision'])
        self.assertNotIn('Programa Dos', celdas)

    def test_reportes_como_categoria_a(self):
        employee = self.env['hr.employee'].create({'name': 'Director', 'user_name': 'pnc_director', 'category_group': 'a'})
        env = self.env(user=employee.user_id)
        wizard = env['informe.report.programa'].create({
            'fecha_inicial': date(2024, 3, 1), 'fecha_final': date(2024, 3, 31),
            'programa_ids': [(6, 0, self.programa.ids)]})
        self.assertEqual(wizard.get_consultas(self.p1), self.filas_p1)
        html = env['ir.actions.report']._render_qweb_html('consultas_pnc.menu_report_programa', wizard.ids)[0].decode()
        self.assertIn('16.67', html)

    def test_onchange_programas_ordena_por_seleccion(self):
        wizard = self.env['informe.report.programa'].new({
            'programa_ids': [(6, 0, (self.programa_2 | self.programa).ids)]})
        wizard.change_programa_ids()
        self.assertEqual(wizard.programa_ids[-1]._origin.sequence, 2)
