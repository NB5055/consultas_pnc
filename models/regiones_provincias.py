from odoo import fields, models


class region_region(models.Model):
    _name = "region.region"
    _description = "Listado de Regiones del Pais"

    name = fields.Char(string="Nombre", help="Nombre de la Region",
                       required=True)


class region_subregion(models.Model):
    _name = "region.subregion"
    _description = "Listado de Sub Regiones del Pais"

    name = fields.Char(string="Nombre", help="Nombre de la Sub Region",
                       required=True)
    region = fields.Many2one('region.region', string="Region",
                             help="Region a que pertenece", required=True)


class region_provincia(models.Model):
    _name = "region.provincia"
    _description = "Listado de Provincias del Pais"

    name = fields.Char(string="Nombre", help="Nombre de la Provincia",
                       required=True)
    subregion = fields.Many2one("region.subregion", string="Sub-Region",
                                help="Sub-Region a que Pertenece", required=True)
    programa_id = fields.Many2one('programa.programa')
