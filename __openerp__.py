# -*- coding: utf-8 -*-
{
    'name': 'ConsultasPNC',
    'version': '1.1',
    'author': 'Speed Solutions',
    'category': 'Consultas PNC',
    'website': 'https://www.speedsolution.com.do',
    'summary': """Sistema para manejo de pacientes y citas """
               """Patronato Nacional de Ciegos.""",
    'description': """
""",
    'depends': ['hr', 'mail', 'base'],
    'data': [
        'security/consultas_pnc_security.xml',
        'security/ir.model.access.csv',
        'views/ficha_paciente.xml',
        'views/consultas.xml',
        'views/programas.xml',
        'views/operativos_view.xml',
        'views/regiones_provincias.xml',
        'views/citas_view.xml',
        'views/hr_employee_view.xml',
        'static/regiones_provincias.xml',
        'reports/report_programa_consolidado.xml',
        'reports/report_informe_programa.xml',
        'menus/menu.xml',
        'menus/mantenimientos.xml',
        'reports/report_view.xml',
        'reports/report_proyeccion.xml',
        'reports/report_prevencion_ceguera.xml',
        'views/webclient_templates.xml',
        'reports/report_asistencia_economica.xml',
        'reports/report_informe_programa_comparativo.xml',
    ],
    'demo': [],

    'installable': True,
    'application': True,
}
