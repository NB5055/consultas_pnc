from datetime import date

from psycopg2 import IntegrityError

from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import ConsultasPncCommon


@tagged('post_install', '-at_install')
class TestModels(ConsultasPncCommon):

    def test_ficha_con_lineas(self):
        patrocinador = self.env['res.partner'].create({'name': 'Patrocinador'})
        parentesco = self.env['ficha.paciente.parentesco'].create({'name': 'Tio'})
        condicion = self.env['ficha.paciente.enfermedades'].create({'name': 'Baja vision'})
        gasto = self.env['ficha.paciente.gasto.fijo.descripcion'].create({'name': 'Luz'})
        paciente = self.env['ficha.paciente'].create({
            'name': '00200000002',
            'nombre': 'Ana',
            'apellidos': 'Gomez',
            'sexo': 'f',
            'vivienda': 'r',
            'birth_date': date(date.today().year - 20, 6, 15),
            'trabajo': self.env['ficha.paciente.trabajo'].create({'name': 'Maestra'}).id,
            'seguro': self.env['ficha.paciente.seguro'].create({'name': 'ARS'}).id,
            'lugar_nacimiento': self.env['region.provincia'].search([], limit=1).id,
            'telefonos': [(0, 0, {'name': '809-555-0001', 'tipo': 'c'})],
            'enfermedades': [(0, 0, {'name': condicion.id})],
            'diagnostico': [(0, 0, {'name': self.diagnostico.id})],
            'gastos_fijos': [(0, 0, {'name': gasto.id, 'monto': 100})],
            'ayuda_economica': [(0, 0, {'name': patrocinador.id, 'parentesco': parentesco.id, 'monto': 500})],
        })
        self.assertEqual(paciente.edad, 20)
        self.assertEqual(paciente.state, 'activo')
        self.assertEqual(paciente.display_name, 'Gomez Ana  ( 00200000002 )')
        self.assertEqual(len(paciente.telefonos), 1)
        self.assertEqual(paciente.enfermedades.name, condicion)
        self.assertEqual(paciente.diagnostico.name, self.diagnostico)
        self.assertEqual(paciente.gastos_fijos.monto, 100)
        self.assertEqual(paciente.ayuda_economica.fecha, date.today())
        self.assertTrue(paciente.lugar_nacimiento)
        for term in ('Gomez', 'Ana', '00200000002'):
            self.assertIn(paciente, self.env['ficha.paciente'].search([('display_name', 'ilike', term)]))
            self.assertIn(paciente.id, [r[0] for r in self.env['ficha.paciente'].name_search(term)])

    def test_ficha_imagen(self):
        imagen = ('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk'
                  'YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')
        self.paciente.image = imagen
        self.assertTrue(self.paciente.image)
        self.assertTrue(self.paciente.image_128)
        self.assertNotIn('image_medium', self.env['ficha.paciente']._fields)
        self.assertNotIn('image_small', self.env['ficha.paciente']._fields)

    def test_ficha_edad_sin_fecha_nacimiento(self):
        paciente = self.env['ficha.paciente'].create({'name': '003', 'nombre': 'Luis', 'apellidos': 'Diaz'})
        self.assertEqual(paciente.edad, 0)
        consulta = self._create_consulta(date(2024, 3, 5), self.terapia, paciente=paciente)
        consulta.edad = 44
        self.assertEqual(paciente.edad, 44)
        paciente.nombre = 'Luis Manuel'
        self.assertEqual(paciente.edad, 44)

    def test_consulta_con_tratamientos_y_diagnosticos(self):
        consulta = self.env['consultas.consultas'].create({
            'name': self.paciente.id,
            'programa': self.programa.id,
            'fecha': date(2024, 3, 5),
            'employee_id': self.employee.id,
            'notes': 'Nota de prueba',
            'tratamiento': [(0, 0, {'name': self.terapia.id}), (0, 0, {'name': self.operativo.id})],
            'diagnostico': [(0, 0, {'name': self.diagnostico.id, 'paciente_id': self.paciente.id})],
        })
        self.assertEqual(consulta.edad, 30)
        self.assertEqual(consulta.sexo, 'm')
        self.assertEqual(len(consulta.tratamiento), 2)
        self.assertEqual(consulta.diagnostico.name, self.diagnostico)
        self.assertEqual(self.paciente.consultas_count, 1)
        self.assertIn(consulta.diagnostico, self.paciente.diagnostico)

        self.env.flush_all()
        linea = consulta.tratamiento.filtered(lambda l: l.name == self.terapia)
        self.env.cr.execute(
            "select paciente_id, employee_id, programa, edad, sexo, fecha from consultas_tratamiento_line where id = %s",
            (linea.id,))
        self.assertEqual(self.env.cr.fetchone(), (
            self.paciente.id, self.employee.id, self.programa.id, 30, 'm', date(2024, 3, 5)))
        self.assertEqual(linea.notes, 'Nota de prueba')
        self.assertEqual(linea.tratamiento, consulta.tratamiento)

        consulta.fecha = date(2024, 4, 1)
        self.assertEqual(linea.fecha, date(2024, 4, 1))

        historial = self.paciente.show_complete_history()
        self.assertEqual(self.env['consultas.consultas'].search(historial['domain']), consulta)
        self.assertEqual([view[1] for view in historial['views']], ['list', 'form'])

    def test_consulta_onchange_programa(self):
        consulta = self.env['consultas.consultas'].new({'name': self.paciente.id})
        consulta.set_programa()
        self.assertEqual(consulta.programa, self.programa)

    def test_constraints_unicidad(self):
        casos = [
            ('consultas.tratamiento', {'name': 'Terapia'}),
            ('programa.programa', {'name': 'Programa Uno'}),
            ('ficha.paciente', {'name': '00100000001', 'nombre': 'Juan', 'apellidos': 'Perez'}),
        ]
        for model in ('consultas.referimiento', 'ficha.paciente.trabajo', 'ficha.paciente.seguro',
                      'ficha.paciente.gasto.fijo.descripcion', 'ficha.paciente.parentesco'):
            self.env[model].create({'name': 'Duplicado'})
            casos.append((model, {'name': 'Duplicado'}))
        for model, vals in casos:
            with self.subTest(model=model), self.assertRaises(IntegrityError), \
                    mute_logger('odoo.sql_db'), self.env.cr.savepoint():
                self.env[model].create(vals)
                self.env.flush_all()

    def test_constraint_proyeccion(self):
        vals = {'tratamiento_id': self.terapia.id, 'programa': self.programa.id, 'year': '2024', 'proyeccion': 120}
        self.env['consultas.proyeccion'].create(vals)
        self.env['consultas.proyeccion'].create(dict(vals, year='2023'))
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'), self.env.cr.savepoint():
            self.env['consultas.proyeccion'].create(vals)
            self.env.flush_all()
        self.assertEqual(self.env['consultas.proyeccion']._fields['year'].column_type[0], 'varchar')

    def test_constraint_monto_ayuda(self):
        patrocinador = self.env['res.partner'].create({'name': 'Patrocinador'})
        parentesco = self.env['ficha.paciente.parentesco'].create({'name': 'Tio'})
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'), self.env.cr.savepoint():
            self.env['ficha.paciente.ayuda.economica'].create({
                'ayuda_economica_id': self.paciente.id, 'name': patrocinador.id,
                'parentesco': parentesco.id, 'monto': 0})
            self.env.flush_all()

    def test_empleado_crea_usuario(self):
        grupo_a = self.env.ref('consultas_pnc.group_categoria_a')
        grupo_b = self.env.ref('consultas_pnc.group_categoria_b')
        grupo_c = self.env.ref('consultas_pnc.group_categoria_c')
        employee = self.env['hr.employee'].create({
            'name': 'Profesor Uno',
            'work_email': 'profesor1@example.com',
            'user_name': 'profesor1',
            'user_password': 'clave-segura-1',
            'category_group': 'c',
            'programa_id': self.programa.id,
        })
        user = employee.user_id
        self.assertTrue(user)
        self.assertEqual(user.login, 'profesor1')
        self.assertEqual(user.name, 'Profesor Uno')
        self.assertEqual(user.partner_id.email, 'profesor1@example.com')
        self.assertIn(grupo_c, user.group_ids)
        self.assertTrue(user.has_group('base.group_user'))
        self.assertFalse(employee.user_password)
        self.assertFalse(self.env['hr.employee']._fields['user_password'].store)
        self.env.cr.execute(
            "select 1 from information_schema.columns where table_name = 'hr_employee' and column_name = 'user_password'")
        self.assertFalse(self.env.cr.fetchall())
        self.env.cr.execute("select password from res_users where id = %s", (user.id,))
        password = self.env.cr.fetchone()[0]
        self.assertTrue(password)
        self.assertNotIn('clave-segura-1', password)
        self.assertIn(employee, self.programa.participantes)

        employee.write({'category_group': 'b', 'user_name': 'profesor.uno', 'user_password': 'otra-clave-2'})
        self.assertEqual(user.login, 'profesor.uno')
        self.assertIn(grupo_b, user.group_ids)
        self.assertNotIn(grupo_c, user.group_ids)
        self.assertTrue((grupo_a | grupo_b | grupo_c).exists() == (grupo_a | grupo_b | grupo_c))
        self.env.cr.execute("select password from res_users where id = %s", (user.id,))
        self.assertNotEqual(self.env.cr.fetchone()[0], password)

    def test_empleado_multi_registro(self):
        grupo_a = self.env.ref('consultas_pnc.group_categoria_a')
        employees = self.env['hr.employee'].create([
            {'name': 'Sin Usuario'},
            {'name': 'Con Correo', 'work_email': 'correo@example.com'},
            {'name': 'Con Login', 'user_name': 'conlogin', 'category_group': 'a', 'user_password': 'clave-3'},
        ])
        self.assertFalse(employees[0].user_id)
        self.assertEqual(employees[1].user_id.login, 'correo@example.com')
        self.assertEqual(employees[2].user_id.login, 'conlogin')
        self.assertIn(grupo_a, employees[2].user_id.group_ids)

        sin_usuario = self.env['hr.employee'].create([{'name': 'Tardio Uno'}, {'name': 'Tardio Dos'}])
        sin_usuario[0].user_name = 'tardio1'
        sin_usuario[1].write({'user_name': 'tardio2', 'category_group': 'c'})
        self.assertEqual(sin_usuario.mapped('user_id.login'), ['tardio1', 'tardio2'])
        (employees[1] | employees[2]).write({'category_group': 'c'})
        grupo_c = self.env.ref('consultas_pnc.group_categoria_c')
        for employee in employees[1] | employees[2]:
            self.assertIn(grupo_c, employee.user_id.group_ids)
        self.assertNotIn(grupo_a, employees[2].user_id.group_ids)
