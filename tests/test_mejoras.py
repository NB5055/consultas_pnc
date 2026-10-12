from datetime import date, datetime, timedelta

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, tagged
from odoo.tools import mute_logger

from .common import ConsultasPncCommon


@tagged('post_install', '-at_install')
class TestMejoras(ConsultasPncCommon):

    def _ficha(self, cedula, nombre='Ana', apellidos='Lopez', **vals):
        return self.env['ficha.paciente'].create(dict(vals, name=cedula, nombre=nombre, apellidos=apellidos))

    # ------------------------------------------------------------ cedula
    def test_cedula_se_normaliza(self):
        self.assertEqual(self.paciente.name, '001-0000000-1')
        self.assertEqual(self._ficha('402 2222222 3').name, '402-2222222-3')

    def test_cedula_sin_numero(self):
        self.assertEqual(self._ficha('').name, '0')
        self.assertEqual(self._ficha('0', nombre='Otro').name, '0')
        self.assertEqual(self._ficha('MENOR M-12', nombre='Nino').name, 'MENOR M-12')

    def test_cedula_incompleta(self):
        with self.assertRaises(ValidationError):
            self._ficha('001-123456-7')
        with self.assertRaises(ValidationError):
            self.paciente.name = '123'

    def test_cedula_repetida_no_se_puede_crear(self):
        with self.assertRaises(ValidationError):
            self._ficha('00100000001', nombre='Otro', apellidos='Distinto')
        otro = self._ficha('00100000002')
        with self.assertRaises(ValidationError):
            otro.name = '001-0000000-1'

    def test_cedula_repetida_historica(self):
        """Las repetidas que ya existen se pueden seguir editando y se encuentran con el filtro."""
        otro = self._ficha('00100000002')
        self.env.cr.execute("UPDATE ficha_paciente SET name = '00100000001' WHERE id = %s", [otro.id])
        otro.invalidate_recordset()
        otro.direccion = 'Calle 2'
        otro.name = '00100000001'
        repetidas = self.env['ficha.paciente'].search([('cedula_repetida', '=', True)])
        self.assertEqual(repetidas, self.paciente | otro)
        self.assertTrue(otro.cedula_repetida)
        self.assertNotIn(self.paciente, self.env['ficha.paciente'].search([('cedula_repetida', '=', False)]))

    # ------------------------------------------------------------ edad
    def test_edad_exacta(self):
        today = date.today()
        manana = today + timedelta(days=1)
        paciente = self._ficha('0', birth_date=manana.replace(year=manana.year - 40))
        self.assertEqual(paciente.edad, 39)

    def test_edad_de_la_consulta_es_la_de_su_fecha(self):
        consulta = self._create_consulta(date(date.today().year - 10, 6, 1), [self.terapia])
        self.assertEqual(consulta.edad, 20)
        self.assertEqual(consulta.tratamiento.edad, 20)
        self.assertEqual(self.paciente.edad, 30)

    def test_edad_sin_fecha_de_nacimiento_se_digita_en_la_consulta(self):
        paciente = self._ficha('0')
        consulta = self._create_consulta(date.today(), [self.terapia], paciente=paciente)
        consulta.edad = 45
        self.assertEqual(paciente.edad, 45)

    def test_cron_actualiza_edades(self):
        self.env.cr.execute("UPDATE ficha_paciente SET edad = 3 WHERE id = %s", [self.paciente.id])
        self.paciente.invalidate_recordset()
        self.env['ficha.paciente']._cron_actualizar_edades()
        self.assertEqual(self.paciente.edad, 30)

    # ------------------------------------------------------------ integridad
    def test_no_se_borra_un_tratamiento_con_historial(self):
        self._create_consulta(date.today(), [self.terapia])
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'), self.env.cr.savepoint():
            self.terapia.unlink()
        self.assertTrue(self.terapia.exists())

    def test_lineas_se_borran_con_su_ficha(self):
        paciente = self._ficha('0', telefonos=[(0, 0, {'name': '809', 'tipo': 'c'})])
        telefono = paciente.telefonos
        paciente.unlink()
        self.assertFalse(telefono.exists())

    def test_diagnostico_necesita_consulta_o_paciente(self):
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'), self.env.cr.savepoint():
            self.env['consultas.diagnostico.line'].create({'name': self.diagnostico.id})

    def test_contador_de_consultas(self):
        self._create_consulta(date.today(), [self.terapia])
        self._create_consulta(date.today(), [self.terapia])
        self.paciente.invalidate_recordset()
        self.assertEqual(self.paciente.consultas_count, 2)

    def test_ver_consulta_desde_la_linea(self):
        consulta = self._create_consulta(date.today(), [self.terapia])
        self.assertEqual(consulta.tratamiento.show_consulta()['res_id'], consulta.id)

    def test_proyeccion_del_anio_siguiente(self):
        siguiente = str(date.today().year + 1)
        self.assertIn(siguiente, dict(self.env['consultas.proyeccion']._selection_year()))
        self.env['consultas.proyeccion'].create({
            'tratamiento_id': self.terapia.id, 'programa': self.programa.id, 'year': siguiente, 'proyeccion': 10})

    # ------------------------------------------------------------ permisos
    def _user(self, login, group):
        return self.env['res.users'].with_context(no_reset_password=True).create({
            'name': login, 'login': login,
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref(group).id])]})

    def test_operativos_categoria_c_no_borra(self):
        user_c = self._user('mejoras_c', 'consultas_pnc.group_categoria_c')
        operativo = self.env['operativos'].with_user(user_c).create({
            'name': self.operativo.id, 'atendidos': 5, 'fecha': date.today(), 'programa': self.programa.id})
        with self.assertRaises(AccessError):
            operativo.unlink()
        operativo.with_user(self._user('mejoras_b', 'consultas_pnc.group_categoria_b')).unlink()

    def test_reportes_solo_usuarios_del_modulo(self):
        interno = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'sin categoria', 'login': 'mejoras_sin', 'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        with self.assertRaises(AccessError):
            self.env['report.paciente'].with_user(interno).create({})
        with self.assertRaises(AccessError):
            self.env['operativos'].with_user(interno).search([])
        user_c = self._user('mejoras_c2', 'consultas_pnc.group_categoria_c')
        wizard = self.env['report.paciente'].with_user(user_c).create({'programa_ids': [(6, 0, self.programa.ids)]})
        self.assertIn(self.paciente, wizard.get_data(self.programa))

    def test_participantes_del_programa_sin_permisos_de_rrhh(self):
        self.employee.programa_id = self.programa
        user_c = self._user('mejoras_c3', 'consultas_pnc.group_categoria_c')
        programa = self.programa.with_user(user_c)
        programa.invalidate_recordset()
        self.assertEqual(programa.participantes.mapped('name'), ['Medico Prueba'])

    # ------------------------------------------------------------ citas
    def _cita(self, inicio, env=None, **vals):
        return (env or self.env)['citas.citas'].create(dict({
            'paciente_id': self.paciente.id, 'programa_id': self.programa.id, 'employee_id': self.employee.id,
            'fecha_desde': inicio, 'fecha_hasta': inicio + timedelta(minutes=30)}, **vals))

    def test_cita_a_consulta(self):
        inicio = datetime.now().replace(microsecond=0) + timedelta(days=1)
        cita = self._cita(inicio)
        self.assertEqual(cita.state, 'pendiente')
        action = cita.action_registrar_consulta()
        consulta = self.env['consultas.consultas'].with_context(action['context']).create({
            'tratamiento': [(0, 0, {'name': self.terapia.id})]})
        self.assertEqual(consulta.name, self.paciente)
        self.assertEqual(consulta.programa, self.programa)
        self.assertEqual(consulta.employee_id, self.employee)
        self.assertEqual(cita.state, 'atendida')
        self.assertEqual(cita.consulta_id, consulta)
        with self.assertRaises(UserError):
            cita.action_registrar_consulta()
        self.paciente.invalidate_recordset()
        self.assertEqual(self.paciente.citas_count, 1)

    def test_cita_a_consulta_conserva_programa(self):
        # En el formulario, el programa de la cita manda sobre el de la ficha.
        cita = self._cita(datetime.now().replace(microsecond=0) + timedelta(days=3),
                          programa_id=self.programa_2.id)
        action = cita.action_registrar_consulta()
        form = Form(self.env['consultas.consultas'].with_context(action['context']),
                    view='consultas_pnc.consultas_consultas_form')
        self.assertEqual(form.programa, self.programa_2)
        form.name = self.paciente
        self.assertEqual(form.programa, self.programa_2)

    def test_cita_validaciones(self):
        inicio = datetime.now().replace(microsecond=0) + timedelta(days=1)
        cita = self._cita(inicio)
        with self.assertRaises(ValidationError):
            self._cita(inicio + timedelta(minutes=10))
        with self.assertRaises(ValidationError):
            self._cita(inicio + timedelta(days=1), fecha_hasta=inicio)
        cita.action_cancelar()
        self._cita(inicio + timedelta(minutes=10))
        cita.action_ausente()
        self.assertEqual(cita.state, 'ausente')

    def test_cita_categoria_c_agenda(self):
        user_c = self._user('mejoras_c4', 'consultas_pnc.group_categoria_c')
        cita = self._cita(datetime.now().replace(microsecond=0) + timedelta(days=2), env=self.env(user=user_c))
        cita.action_cancelar()
        with self.assertRaises(AccessError):
            cita.unlink()

    # ------------------------------------------------------------ referimientos y gastos
    def test_referimiento_en_la_consulta(self):
        referimiento = self.env['consultas.referimiento'].create({'name': 'Oftalmologia'})
        consulta = self._create_consulta(date.today(), [self.terapia])
        consulta.referimiento = [(0, 0, {'name': referimiento.id, 'notas': 'Evaluar'})]
        linea = consulta.referimiento
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'), self.env.cr.savepoint():
            referimiento.unlink()
        consulta.unlink()
        self.assertFalse(linea.exists())

    def test_gastos_fijos_categoria_c(self):
        tipo = self.env['ficha.paciente.gasto.fijo.descripcion'].create({'name': 'Luz'})
        user_c = self._user('mejoras_c5', 'consultas_pnc.group_categoria_c')
        self.paciente.with_user(user_c).gastos_fijos = [(0, 0, {'name': tipo.id, 'monto': 500})]
        self.assertEqual(self.paciente.gastos_fijos.monto, 500)
