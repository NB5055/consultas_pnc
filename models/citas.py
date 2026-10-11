from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class Citas(models.Model):
    _name = "citas.citas"
    _inherit = ['mail.thread']
    _description = "Administracion de citas"
    _rec_name = "paciente_id"
    _order = "fecha_desde desc"

    paciente_id = fields.Many2one("ficha.paciente", string="Paciente",
                                  required=True, tracking=True, index=True, ondelete='cascade')
    fecha_desde = fields.Datetime(string="Fecha Desde", required=True, tracking=True, index=True)
    fecha_hasta = fields.Datetime(string="Fecha Hasta", required=True, tracking=True)
    programa_id = fields.Many2one("programa.programa", string="Programa",
                                  required=True, tracking=True, index=True)
    employee_id = fields.Many2one("hr.employee", string="Médico / Profesor", tracking=True, index=True,
                                  default=lambda self: self.env['consultas.consultas']._get_employee())
    state = fields.Selection([('pendiente', 'Pendiente'),
                              ('atendida', 'Atendida'),
                              ('ausente', 'No Asistio'),
                              ('cancelada', 'Cancelada')],
                             string="Estado", default='pendiente', required=True, tracking=True, index=True)
    notas = fields.Text(string="Motivo / Notas")
    consulta_id = fields.Many2one("consultas.consultas", string="Consulta Registrada",
                                  readonly=True, copy=False, ondelete='set null')

    @api.onchange('paciente_id')
    def _onchange_paciente_id(self):
        if self.paciente_id.programa and not self.programa_id:
            self.programa_id = self.paciente_id.programa

    @api.onchange('fecha_desde')
    def _onchange_fecha_desde(self):
        if self.fecha_desde and (not self.fecha_hasta or self.fecha_hasta <= self.fecha_desde):
            self.fecha_hasta = fields.Datetime.add(self.fecha_desde, minutes=30)

    @api.constrains('fecha_desde', 'fecha_hasta')
    def _check_fechas(self):
        for cita in self:
            if cita.fecha_hasta < cita.fecha_desde:
                raise ValidationError("La cita no puede terminar antes de empezar")

    @api.constrains('employee_id', 'fecha_desde', 'fecha_hasta', 'state')
    def _check_solape(self):
        for cita in self.filtered(lambda c: c.employee_id and c.state == 'pendiente'):
            otra = self.search([('id', '!=', cita.id), ('employee_id', '=', cita.employee_id.id),
                                ('state', '=', 'pendiente'), ('fecha_desde', '<', cita.fecha_hasta),
                                ('fecha_hasta', '>', cita.fecha_desde)], limit=1)
            if otra:
                raise ValidationError("%s ya tiene una cita en ese horario con %s" % (
                    cita.employee_id.name, otra.paciente_id.display_name))

    def action_registrar_consulta(self):
        """Abre la consulta con los datos de la cita; al guardarla la cita queda atendida."""
        self.ensure_one()
        if self.consulta_id:
            raise UserError("Esta cita ya tiene una consulta registrada")
        return {
            'name': "Registrar Atencion",
            'type': 'ir.actions.act_window',
            'res_model': 'consultas.consultas',
            'views': [(self.env.ref('consultas_pnc.consultas_consultas_form').id, 'form')],
            'target': 'current',
            'context': {
                'default_name': self.paciente_id.id,
                'default_programa': self.programa_id.id,
                'default_employee_id': self.employee_id.id,
                'default_fecha': fields.Date.context_today(self, self.fecha_desde),
                'pnc_cita_id': self.id,
            },
        }

    def action_ver_consulta(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'consultas.consultas',
            'res_id': self.consulta_id.id,
            'views': [(self.env.ref('consultas_pnc.consultas_consultas_form').id, 'form')],
        }

    def action_ausente(self):
        self.write({'state': 'ausente'})

    def action_cancelar(self):
        self.write({'state': 'cancelada'})

    def action_pendiente(self):
        self.write({'state': 'pendiente'})
