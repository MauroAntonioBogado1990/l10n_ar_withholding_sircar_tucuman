# -*- coding: utf-8 -*-
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class Padron(models.Model):
    """
    Este modelo representa una línea del padrón de Tucumán.
    Guarda la información de alícuotas de un CUIT específico para un periodo dado.
    """
    _name = 'tucuman.padron'
    _description = 'Registros del Padrón de Tucumán'

    # --- CAMPOS DEL MODELO ---
    name = fields.Char('CUIT')  # Nombre técnico del campo es 'name' pero contiene el CUIT
    publication_date = fields.Date('Fecha de publicacion')
    effective_date_from = fields.Date('Fecha de vigencia desde')
    effective_date_to = fields.Date('Fecha de vigencia hasta')
    
    # Diferencia si este registro es para aplicar en VENTAS (Percepción) o COMPRAS (Retención)
    type_alicuot = fields.Selection([
        ('P', 'Percepcion'),
        ('R', 'Retencion')
    ], 'Tipo', required=True)
    
    # Situación del contribuyente ante Ingresos Brutos
    type_contr_insc = fields.Selection([
        ('CM', 'Convenio Multilateral'),
        ('CL', 'Contribuyente Local'),
        ('E', 'Exento'),
    ], 'Tipo')

    # Estados informados por Rentas
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

    # Porcentajes de impuestos
    a_per = fields.Float('Alicuota-Percepcion')
    a_ret = fields.Float('Alicuota-Retencion')
    
    # Identificadores de grupo asignados por el fisco
    nro_grupo_perc = fields.Char('Nro Grupo Percepcion')
    nro_grupo_ret = fields.Char('Nro Grupo Retencion')

    @api.model
    def create(self, vals):
        """
        SOBREESCRITURA DEL MÉTODO CREATE:
        Cada vez que se crea un registro en el padrón, este código busca al Cliente 
        en Odoo y le actualiza su ficha automáticamente.
        """
        # 1. Crear el registro en este modelo (tucuman.padron)
        padron = super(Padron, self).create(vals)
        
        # 2. Buscar si el CUIT que acabamos de cargar existe en nuestra base de Clientes/Proveedores
        partner = self.env['res.partner'].search([('vat','=',padron.name),('parent_id','=',False)], limit=1)
        
        if len(partner) > 0:
            # CASO RETENCIÓN: Si el registro es tipo 'R', actualizamos la tabla de retenciones del cliente
            if padron.type_alicuot == 'R':
                # Desactivamos cualquier alícuota anterior para que no haya dos "activas" al mismo tiempo
                for alicuota in partner.alicuot_ret_tucuman_ids:
                    if alicuota.padron_activo == True:
                        alicuota.padron_activo = False
                
                # Insertamos la nueva alícuota en la ficha del contacto
                partner.sudo().update({'alicuot_ret_tucuman_ids' : [(0, 0, {
                    'partner_id': partner.id, 
                    'publication_date': padron.publication_date,
                    'effective_date_from': padron.effective_date_from,
                    'effective_date_to': padron.effective_date_to,
                    'type_contr_insc': padron.type_contr_insc,
                    'alta_baja': padron.alta_baja,
                    'cambio': padron.cambio,
                    'a_ret': padron.a_ret,
                    'nro_grupo_ret': padron.nro_grupo_ret,
                    'padron_activo': True  # Esta queda como la vigente
                })]})
            
            # CASO PERCEPCIÓN: Si el registro es tipo 'P', actualizamos la tabla de percepciones
            elif padron.type_alicuot == 'P':
                for alicuota in partner.alicuot_per_tucuman_ids:
                    if alicuota.padron_activo == True:
                        alicuota.padron_activo = False
                
                partner.sudo().update({'alicuot_per_tucuman_ids' : [(0, 0, {
                    'partner_id': partner.id, 
                    'publication_date': padron.publication_date,
                    'effective_date_from': padron.effective_date_from,
                    'effective_date_to': padron.effective_date_to,
                    'type_contr_insc': padron.type_contr_insc,
                    'alta_baja': padron.alta_baja,
                    'cambio': padron.cambio,
                    'a_per': padron.a_per,
                    'nro_grupo_per': padron.nro_grupo_perc,
                    'padron_activo': True
                })]})
        return padron

    def write(self, variables):
        """
        SOBREESCRITURA DEL MÉTODO WRITE (Editar):
        Si alguien edita a mano un valor del padrón (ej. la alícuota), 
        el sistema también actualiza la ficha del cliente vinculado.
        """
        # Lista de campos que, si cambian, disparan la actualización del contacto
        campos_criticos = ['publication_date', 'effective_date_from', 'effective_date_to', 'alta_baja', 'a_per', 'a_ret']
        
        # Si alguno de esos campos está en las variables que se están editando:
        if any(campo in variables for campo in campos_criticos):
            res = super(Padron, self).write(variables)
            partner = self.env['res.partner'].search([('vat','=',self.name),('parent_id','=',False)], limit=1)
            
            if len(partner) > 0:
                # La lógica es idéntica al create: desactivar vieja y crear nueva línea activa
                if self.type_alicuot == 'R':
                    for alicuota in partner.alicuot_ret_tucuman_ids:
                        if alicuota.padron_activo == True:
                            alicuota.padron_activo = False
                    partner.alicuot_ret_tucuman_ids = [(0, 0, {
                        'partner_id': partner.id, 
                        'publication_date': self.publication_date,
                        'effective_date_from': self.effective_date_from,
                        'effective_date_to': self.effective_date_to,
                        'type_contr_insc': self.type_contr_insc,
                        'alta_baja': self.alta_baja,
                        'cambio': self.cambio,
                        'a_ret': self.a_ret,
                        'nro_grupo_ret': self.nro_grupo_ret,
                        'padron_activo': True
                    })]
                elif self.type_alicuot == 'P':
                    for alicuota in partner.alicuot_per_tucuman_ids:
                        if alicuota.padron_activo == True:
                            alicuota.padron_activo = False
                    partner.alicuot_per_tucuman_ids = [(0, 0, {
                        'partner_id': partner.id, 
                        'publication_date': self.publication_date,
                        'effective_date_from': self.effective_date_from,
                        'effective_date_to': self.effective_date_to,
                        'type_contr_insc': self.type_contr_insc,
                        'alta_baja': self.alta_baja,
                        'cambio': self.cambio,
                        'a_per': self.a_per,
                        'nro_grupo_per': self.nro_grupo_perc,
                        'padron_activo': True
                    })]
            return res
        
        # Si lo que se editó no era crítico, solo guarda sin actualizar al cliente
        return super(Padron, self).write(variables)


    
