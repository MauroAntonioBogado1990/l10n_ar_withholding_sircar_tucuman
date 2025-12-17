# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import logging
_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def get_amount_alicuot_tucuman(self,type_alicuot,date):
        amount_alicuot = 0.00
        if type_alicuot == 'per':
            alicuot = self.alicuot_per_tucuman_ids.filtered(lambda l: l.effective_date_from <= date and l.effective_date_to >= date)
            if len(alicuot) > 0:
                amount_alicuot = alicuot[0].a_per
        elif type_alicuot == 'ret':
            alicuot = self.alicuot_ret_tucuman_ids.filtered(lambda l: l.effective_date_from <= date and l.effective_date_to >= date)
            if len(alicuot) > 0:
                amount_alicuot = alicuot[0].a_ret
        return amount_alicuot

    alicuot_ret_tucuman_ids = fields.One2many(
        'partner.padron.tucuman.ret',
        'partner_id',
        'Alicuotas Retencion',
    )
    alicuot_per_tucuman_ids = fields.One2many(
        'partner.padron.tucuman.per',
        'partner_id',
        'Alicuotas Percepcion',
    )

class ResPartnerAlicuotRet(models.Model):
    _name = 'partner.padron.tucuman.ret'
    _order = 'create_date desc'

    partner_id = fields.Many2one(
        'res.partner',
        required=True,
        ondelete='cascade',
    )
    publication_date = fields.Date('Fecha de publicacion')
    effective_date_from = fields.Date('Vigencia desde')
    effective_date_to = fields.Date('Vigencia hasta')
    type_contr_insc = fields.Selection([
        ('CM', 'Convenio Multilatera'),
        ('CL', 'Contribuyente Local'),
        ('E', 'Exento'),
    ], 'Tipo')
    alta_baja = fields.Selection([
        ('S', 'Se incorpora al padron'),
        ('N', 'No incorpora al padron'),
        ('B', 'Baja')
    ], 'Alta/Baja')
    cambio = fields.Selection([
        ('S', 'Cambio al anterior'),
        ('N', 'Sin cambios'),
        ('B', 'Baja')
    ], 'Cambio')
    a_ret = fields.Float('Alicuota-Retencion')
    nro_grupo_ret = fields.Char('Nro Grupo Retencion')
    padron_activo = fields.Boolean('Activo')

    @api.model
    def create(self, vals):
        parent = self.env['res.partner'].search([('id','=',int(vals['partner_id'])),('parent_id','=',False)],limit=1)
        for alicuota in parent.alicuot_ret_tucuman_ids:
            if alicuota.padron_activo == True:
                alicuota.padron_activo = False
        
        vals['padron_activo'] = True
        rec = super(ResPartnerAlicuotRet, self).create(vals)
        return rec

class ResPartnerAlicuotPer(models.Model):
    _name = 'partner.padron.tucuman.per'
    _order = 'create_date desc'

    partner_id = fields.Many2one(
        'res.partner',
        required=True,
        ondelete='cascade',
    )
    publication_date = fields.Date('Fecha de publicacion')
    effective_date_from = fields.Date('Vigencia desde')
    effective_date_to = fields.Date('Vigencia hasta')
    type_contr_insc = fields.Selection([
        ('CM', 'Convenio Multilatera'),
        ('CL', 'Contribuyente Local'),
        ('E', 'Exento'),
    ], 'Tipo')
    alta_baja = fields.Selection([
        ('S', 'Se incorpora al padron'),
        ('N', 'No incorpora al padron'),
        ('B', 'Baja')
    ], 'Alta/Baja')
    cambio = fields.Selection([
        ('S', 'Cambio al anterior'),
        ('N', 'Sin cambios')
    ], 'Cambio')
    a_per = fields.Float('Alicuota-Percepcion')
    nro_grupo_per = fields.Char('Nro Grupo Percepcion')
    padron_activo = fields.Boolean('Activo')

    @api.model
    def create(self, vals):
        parent = self.env['res.partner'].search([('id','=',int(vals['partner_id'])),('parent_id','=',False)],limit=1)
        for alicuota in parent.alicuot_per_tucuman_ids:
            if alicuota.padron_activo == True:
                alicuota.padron_activo = False
        
        vals['padron_activo'] = True
        rec = super(ResPartnerAlicuotPer, self).create(vals)
        return rec
