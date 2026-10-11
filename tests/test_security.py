from datetime import date

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tools import mute_logger

from .common import ConsultasPncCommon


@tagged('post_install', '-at_install')
class TestSecurity(ConsultasPncCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        employees = cls.env['hr.employee'].create([
            {'name': 'Usuario A', 'user_name': 'pnc_a', 'category_group': 'a'},
            {'name': 'Usuario B', 'user_name': 'pnc_b', 'category_group': 'b'},
            {'name': 'Usuario C', 'user_name': 'pnc_c', 'category_group': 'c', 'programa_id': cls.programa.id},
            {'name': 'Otro C', 'user_name': 'pnc_c2', 'category_group': 'c'},
        ])
        cls.employee_c = employees[2]
        cls.user_a, cls.user_b, cls.user_c, cls.user_c2 = employees.mapped('user_id')
        cls.consulta_ajena = cls._create_consulta(date(2024, 3, 1), cls.terapia)
        cls.consulta_c2 = cls._create_consulta(
            date(2024, 3, 2), cls.terapia, env=cls.env(user=cls.user_c2))

    def test_categoria_c_solo_sus_consultas(self):
        env = self.env(user=self.user_c)
        Consulta = env['consultas.consultas']
        self.assertEqual(Consulta._get_employee(), self.employee_c)
        propia = Consulta.create({
            'name': self.paciente.id,
            'programa': self.programa.id,
            'fecha': date(2024, 3, 3),
            'tratamiento': [(0, 0, {'name': self.terapia.id})],
        })
        self.assertEqual(propia.employee_id, self.employee_c)
        self.assertEqual(propia.create_uid, self.user_c)
        self.assertEqual(Consulta.search([]), propia)

        propia.write({'notes': 'editada por su autor'})
        self.assertEqual(propia.notes, 'editada por su autor')
        for ajena in (self.consulta_ajena, self.consulta_c2):
            with self.assertRaises(AccessError), mute_logger('odoo.addons.base.models.ir_access'):
                ajena.with_env(env).write({'notes': 'no deberia'})
            with self.assertRaises(AccessError), mute_logger('odoo.addons.base.models.ir_access'):
                ajena.with_env(env).read(['notes'])
        with self.assertRaises(AccessError), mute_logger('odoo.addons.base.models.ir_access'):
            propia.unlink()

    def test_categoria_c_catalogos(self):
        env = self.env(user=self.user_c)
        self.assertTrue(env['consultas.tratamiento'].search([]))
        self.assertEqual(self.programa.with_env(env).encargado, env['hr.employee'])
        self.programa.with_env(env).participantes.mapped('name')
        with self.assertRaises(AccessError):
            env['consultas.tratamiento'].create({'name': 'No permitido'})
        with self.assertRaises(AccessError):
            env['consultas.proyeccion'].search([])
        with self.assertRaises(AccessError):
            self.paciente.with_env(env).unlink()
        paciente = env['ficha.paciente'].create({'name': '009', 'nombre': 'Rosa', 'apellidos': 'Mota'})
        paciente.write({'direccion': 'Calle 9'})

    def test_categoria_b_solo_sus_consultas(self):
        env = self.env(user=self.user_b)
        propia = self._create_consulta(date(2024, 3, 4), self.terapia, env=env)
        self.assertEqual(env['consultas.consultas'].search([]), propia)
        with self.assertRaises(AccessError), mute_logger('odoo.addons.base.models.ir_access'):
            self.consulta_ajena.with_env(env).write({'notes': 'no deberia'})
        propia.unlink()

    def test_categoria_a_todas_las_consultas(self):
        env = self.env(user=self.user_a)
        consultas = env['consultas.consultas'].search([])
        self.assertIn(self.consulta_ajena, consultas)
        self.assertIn(self.consulta_c2, consultas)
        self.consulta_c2.with_env(env).write({'notes': 'revisada'})
        self.assertEqual(self.consulta_c2.notes, 'revisada')
        with self.assertRaises(AccessError):
            self.consulta_c2.with_env(env).unlink()
        self.assertTrue(env['consultas.proyeccion'].search([]) is not None)

    def test_usuario_interno_sin_categoria(self):
        user = self.env['res.users'].create({'name': 'Sin Categoria', 'login': 'pnc_none'})
        env = self.env(user=user)
        with self.assertRaises(AccessError):
            env['consultas.consultas'].search([])
        with self.assertRaises(AccessError):
            env['ficha.paciente'].search([])
        self.assertTrue(env['operativos'].search([]) is not None)

    def test_administrador_acceso_total(self):
        admin = self.env.ref('base.user_admin')
        env = self.env(user=admin)
        consultas = env['consultas.consultas'].search([])
        self.assertIn(self.consulta_ajena, consultas)
        self.assertIn(self.consulta_c2, consultas)
        env['consultas.proyeccion'].create({
            'tratamiento_id': self.terapia.id, 'programa': self.programa.id, 'year': '2024', 'proyeccion': 10})
        self.consulta_c2.with_env(env).unlink()
        self.assertIn(self.env.ref('consultas_pnc.mantenimientos').id, env['ir.ui.menu']._visible_menu_ids())

    def test_menus_por_grupo(self):
        mantenimientos = self.env.ref('consultas_pnc.mantenimientos')
        self.assertEqual(mantenimientos.group_ids, self.env.ref('consultas_pnc.group_categoria_a')
                         | self.env.ref('consultas_pnc.group_categoria_b') | self.env.ref('base.group_system'))
        visibles_c = self.env['ir.ui.menu'].with_user(self.user_c)._visible_menu_ids()
        visibles_b = self.env['ir.ui.menu'].with_user(self.user_b)._visible_menu_ids()
        self.assertNotIn(mantenimientos.id, visibles_c)
        self.assertIn(mantenimientos.id, visibles_b)
        self.assertIn(self.env.ref('consultas_pnc.menu_root').id, visibles_c)
        linea_menu = self.env.ref('consultas_pnc.consultas_consultas_line_sub_menu')
        self.assertNotIn(linea_menu.id, visibles_b)
        self.assertIn(linea_menu.id, self.env['ir.ui.menu'].with_user(self.user_a)._visible_menu_ids())
