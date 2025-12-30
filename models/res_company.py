# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    """
    Se hereda res.company para agregar la configuración específica de Tucumán
    que la empresa (el usuario) necesita para sus impuestos.
    """
    _inherit = "res.company"

    # Este campo permite seleccionar cuál de todos los impuestos creados en Odoo
    # es el que corresponde a la Percepción de Tucumán.
    # El domain filtra para que solo aparezcan impuestos de Ventas y con código AFIP 07 (IIBB).
    tax_per_tucuman = fields.Many2one(
        'account.tax',
        'Impuesto de Percepción Tucuman',
        domain=[('type_tax_use', '=', 'sale'),('tax_group_id.l10n_ar_tribute_afip_code','=','07')], 
        company_dependent=True  # Permite tener un valor distinto si hay varias empresas en la misma base
    )
    l10n_ar_tucuman_porcentaje_general = fields.Float(
        string='Porcentaje General Tucumán', 
        digits=(16, 2),
        default=0.0,
        help="Alícuota a aplicar si el partner no está en el padrón.",
        company_dependent=True
    )

    # --- CONFIGURACIÓN DE REGÍMENES (Para exportaciones de datos/SIFERE) ---
    
    # Define el código de régimen que se usará para las RETENCIONES (Compras)
    # Nota: Aunque las descripciones mencionan AGIP (CABA), estos campos están 
    # siendo preparados para mapear los códigos de Tucumán.
    regimen_tucuman_ret = fields.Selection([
        ('1','1 - COMPAÑIAS DE SEGUROS'),
        ('2','2 - ORD. 40434 PROVEEDORES GCBA – RESOLUCIÓN Nº 200/AGIP/2002'),
        ('3','3 - OBRAS Y SERVICIOS SOCIALES, MUTUALES Y MEDICINA PREPAGA'),
        ('4','4 - TARJETAS CRÉDITO, COMPRA, DÉBITO Y SIMILARES'),
        ('5','5 - SERVICIOS DE TICKETS, VALES ALIMENTOS (Vigente hasta el 31/12/2019)'),
        ('6','6 - MARTILLEROS Y DEMÁS INTERMEDIARIOS'),
        ('7','7 - COMISIONISTAS, REPRESENTANTES, CONSIGNATARIOS O CUALQUIER OTRO INTERMEDIARIO PERSONA O ENTIDAD'),
        ('8','8 - REGIMEN GENERAL - (Vigente hasta el 31/10/2016 - Aplicable solo para DDJJ Originales y Rectificativas Períodos: 10-2016 y anteriores)'),
        ('16','16 - PADRÓN DE RIESGO FISCAL - (Vigente hasta el 31/12/2019)'),
        ('18','18 - RÉGIMEN SIMPLIFICADO - MAGNITUDES SUPERADAS - (Vigente hasta el 31/12/2019)'),
        ('19','19 - RETENCIÓN PARCIAL - REGIMEN SIMPLIFICADO - MAGNITUDES SUPERADAS - (Vigente hasta el 31/12/2019)'),
        ('20','20 - IMPOSIBILIDAD DE RETENER - REGIMEN SIMPLIFICADO - MAGNITUDES SUPERADAS - (Vigente hasta el 31/12/2019)'),
        ('25','25 - CONTRATACIÓN DE SERVICIOS  SUSCRIPCIÓN ON-LINE, PELÍCULAS, TV Y OTROS - (RES. 593/AGIP/2014, y Modif.) - (Régimen suspendido por Resolución Nº 26-AGIP/2015).'),
        ('26','26 - ACTIVIDADES CULTURALES Y ARTISTAS - EXTRANJEROS (Res. 594/AGIP/2014, y Modif.) - (Régimen suspendido por Resolución Nº 624-AGIP/2014)'),
        ('28','28 - PADRÓN DE ALICUOTAS DIFERENCIALES - REGÍMENES  PARTICULARES '),
        ('29','29 - PADRÓN DE REGÍMENES GENERALES'),
        ('31','31 - SERVICIOS DE GESTIÓN Y/O PROCESAMIENTO DE PAGOS PLATAFORMAS Y APLICACIONES INFORMÁTICAS - (Vigente desde 01/02/2020)'),
    ],'Regimen Retenciones Tucumán', company_dependent=True)
    
    # Define el código de régimen que se usará para las PERCEPCIONES (Ventas)
    # Estos códigos suelen ser requeridos para generar el archivo TXT para Rentas o SIFERE.
    regimen_tucuman_per = fields.Selection([
        ('10', '10 - PRODUCTORES DE COMBUSTIBLES LÍQUIDOS, GAS NATURAL y COMERCIALIZADORES MAYORISTAS'),
        ('11', '11 - VENTAS DE PRODUCTOS DERIVADOS DEL PETRÓLEO (ACEITES, LUBRICANTES, ETC)'),
        ('12', '12 - PRODUCCIÓN ELABORACIÓN Y FABRICACIÓN DE PRODUCTOS COMESTIBLES Y BEBIDAS'),
        ('14', '14 - RÉGIMEN GENERAL - (Vigente hasta el 31/10/2016)'),
        ('15', '15 - TERMINALES AUTOMOTRICES Y MOTOCICLETAS'),
        ('16', '16 - PADRÓN DE RIESGO FISCAL  - (Vigente hasta el 31/12/2019)'),
        ('17', '17 - CANONES Y ALQUILERES SHOPPING - (Vigente hasta el 31/12/2019)'),
        ('18', '18 - RÉGIMEN SIMPLIFICADO - MAGNITUDES SUPERADAS - (Vigente hasta el 31/12/2019)'),
        ('19', '19 - PERCEPCIÓN PARCIAL - RÉGIMEN SIMPLIFICADO - MAGNITUDES SUPERADAS - (Vigente hasta el 31/12/2019)'),
        ('20', '20 - IMPOSIBILIDAD DE PERCEPCIÓN - RÉGIMEN SIMPLIFICADO - MAGNITUDES SUPERADAS - (Vigente hasta el 31/12/2019)'),
        ('21', '21 - CONTRATOS DE FRANQUICIAS - (Vigente hasta el 31/12/2019)'),
        ('22', '22 - VENTA  AL CONTADO Y EFECTIVO - IMPORTE SUPERIOR A $ 1.000,00'),
        ('23', '23 - PORTALES DE SUBASTAS ON-LINE - CON INSCRIPTOS  EN ISIB'),
        ('24', '24 - PORTALES DE SUBASTAS ON-LINE  CON NO INSCRIPTOS EN ISIB'),
        ('27', '27 - FABRICANTES Y MAYORISTAS DE TABACO Y AFINES'),
        ('28', '28 - PADRÓN DE ALICUOTAS DIFERENCIALES - REGÍMENES PARTICULARES'),
        ('29', '29 - PADRÓN DE REGÍMENES GENERALES'),
        ('30', '30 - VENTA DIRECTA - (Vigente a partir del 01/01/2020)'),
    ],'Regimen Percepciones Tucumán', company_dependent=True)