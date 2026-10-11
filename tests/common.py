from datetime import date

from odoo.tests.common import TransactionCase


class ConsultasPncCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.programa = cls.env['programa.programa'].create({
            'name': 'Programa Uno', 'program_type': 'servicio'})
        cls.programa_2 = cls.env['programa.programa'].create({
            'name': 'Programa Dos', 'program_type': 'prevencion_ceguera'})
        cls.terapia = cls.env['consultas.tratamiento'].create({
            'name': 'Terapia', 'category': 'rh', 'programa_ids': [(6, 0, cls.programa.ids)]})
        cls.operativo = cls.env['consultas.tratamiento'].create({
            'name': 'Operativo Visual', 'category': 'pc', 'programa_ids': [(6, 0, cls.programa.ids)]})
        cls.diagnostico = cls.env['consultas.diagnostico'].create({'name': 'Glaucoma'})
        cls.employee = cls.env['hr.employee'].create({'name': 'Medico Prueba'})
        cls.paciente = cls.env['ficha.paciente'].create({
            'name': '00100000001',
            'nombre': 'Juan',
            'apellidos': 'Perez',
            'sexo': 'm',
            'birth_date': date(date.today().year - 30, 1, 1),
            'programa': cls.programa.id,
            'direccion': 'Calle 1',
        })

    @classmethod
    def _create_consulta(cls, fecha, tratamientos, programa=None, paciente=None, env=None):
        env = env or cls.env
        return env['consultas.consultas'].create({
            'name': (paciente or cls.paciente).id,
            'programa': (programa or cls.programa).id,
            'fecha': fecha,
            'employee_id': cls.employee.id,
            'tratamiento': [(0, 0, {'name': tratamiento.id}) for tratamiento in tratamientos],
        })
