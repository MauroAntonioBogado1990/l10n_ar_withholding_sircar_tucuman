# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,date,timedelta
from dateutil import relativedelta
import base64
import logging
import json
_logger = logging.getLogger(__name__)

class AccountExportTucuman(models.Model):
    _name = 'account.export.tucuman'
    _description = 'account.export.tucuman'

    name = fields.Char('Nombre')
    date_from = fields.Date('Fecha desde')
    date_to = fields.Date('Fecha hasta')
    export_agip_data_ret = fields.Text('Contenidos archivo AGIP RET', default='')
    export_agip_data_per = fields.Text('Contenidos archivo AGIP PER', default='')
    export_agip_data_nc = fields.Text('Contenidos archivo AGIP NC PER', default='')
    export_agip_data = fields.Text('Contenidos archivo AGIP', default='')
    tax_withholding = fields.Many2one('account.tax','Imp. de ret utilizado', domain=[('tax_agip_ret', '=', True)]) 
    
    @api.depends('export_agip_data')
    def _compute_files_nc(self):
        self.ensure_one()
        self.export_agip_filename = _('Agip_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.export_agip_file = base64.encodestring(self.export_agip_data.encode('ISO-8859-1'))

    export_agip_file = fields.Binary('Archivo AGIP',compute=_compute_files_nc)
    export_agip_filename = fields.Char('Archivo AGIP',compute=_compute_files_nc)
    
    @api.depends('export_agip_data_nc')
    def _compute_files_nc(self):
        self.ensure_one()
        self.export_agip_filename_nc = _('Agip_nc_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.export_agip_file_nc = base64.encodestring(self.export_agip_data_nc.encode('ISO-8859-1'))

    export_agip_file_nc = fields.Binary('Archivo AGIP',compute=_compute_files_nc)
    export_agip_filename_nc = fields.Char('Archivo AGIP',compute=_compute_files_nc)
    
    @api.depends('export_agip_data_ret')
    def _compute_files_ret(self):
        self.ensure_one()
        self.export_agip_filename_ret = _('Agip_ret_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.export_agip_file_ret = base64.encodestring(self.export_agip_data_ret.encode('ISO-8859-1'))

    export_agip_file_ret = fields.Binary('Archivo AGIP',compute=_compute_files_ret)
    export_agip_filename_ret = fields.Char('Archivo AGIP',compute=_compute_files_ret)
    
    @api.depends('export_agip_data_per')
    def _compute_files_per(self):
        self.ensure_one()
        self.export_agip_filename_per = _('Agip_per_%s_%s.txt') % (str(self.date_from),str(self.date_to))
        self.export_agip_file_per = base64.encodestring(self.export_agip_data_per.encode('ISO-8859-1'))

    export_agip_file_per = fields.Binary('Archivo AGIP',compute=_compute_files_per)
    export_agip_filename_per = fields.Char('Archivo AGIP',compute=_compute_files_per)


    def compute_agip_data(self):
        list_order_agip = []
        self.ensure_one()
        windows_line_ending = '\r' + '\n'
        payments = self.env['account.payment'].search([('payment_type','=','outbound'),('state','not in',['cancel','draft']),('date','<=',self.date_to),('date','>=',self.date_from)])
        #,('payment_date','<=',self.date_to),('payment_date','>=',self.date_from)])
        string = ''
        _logger.warning('***** payments: {0}'.format(payments))
        for payment in payments:
            if not payment.withholding_number:
                continue
                
            if payment.tax_withholding_id.id != self.tax_withholding.id:
                continue
            _alicuota_ret = payment.partner_id.alicuot_ret_agip_ids.filtered(lambda l: l.effective_date_from == self.date_from)[0].a_ret
            if not _alicuota_ret:
                raise ValidationError('No se encontro un padron en el cliente {0} de fecha {1} para calcular su alicuota de retencion'.format(payment.partner_id.name, self.date_from))
            # TXT segun formato de https://www.agip.gob.ar/agentes/agentes-de-recaudacion/ib-agentes-recaudacion/aplicativo-arciba/aclaraciones-sobre-las-adecuaciones-al-aplicativo-e-arciba-
            # 1 campo Tipo de Operación: 1: Retención / 2: Percepción
            string = string + '1'
            # 2 campo Código de Norma: Según Tipo de Operación
            string = string + self.env.user.company_id.regimen_agip_ret.zfill(3)
            # 3 campo Fecha de Retención / Percepción : dd/mm/aaaa
            string = string + str(payment.date)[8:10] + '/' + str(payment.date)[5:7] + '/' + str(payment.date)[:4]
            # 4 campo Tipo de comprobante origen de la Retención / Percepción : Según Tipo de Operación
            #Si Tipo de Operación = 1
                #01- Factura
                #02- Nota de Débito
                #03- Orden de Pago
                #04- Boleta de Depósito
                #05- Liquidación de pago
                #06- Certificado de obra
                #07- Recibo
                #08- Cont de Loc de Servic.
                #09- Otro Comprobante
                #10- Factura de Crédito Electrónica MiPyMEs.
                #11- Nota de Débito Electrónica MiPyMEs.
                #12- Orden de Pago de Comp. Electrónica MiPyMEs
                #13- Otro Comp. de Crédito Electrónicas MiPyMEs.
            #Si Tipo de Operación = 2
                #01- Factura
                #09- Otro Comprobante
                #10- Factura de Crédito Electrónica MiPyMEs.
                #13- Otro Comp de Crédito Electrónicas MiPyMEs
            string = string + '03'
            # 5 campo Letra del Comprobante
            #Operación Retenciones
                #Si Agente=R.I y Suj.Ret = R.I : Letra = A, M, B
                #Si Agente=R.I y Suj.Ret = Exento : Letra = C
                #Si Agente=R.I y Suj.Ret = Monot : Letra = C
                #Si Agente=Exento y Suj.Ret=R.I : Letra = B
                #Si Agente=Exento y Suj.Ret=Exento : Letra = C
                #Si Agente=Exento y Suj.Ret=Monot. : Letra = C
            #Operación Percepción
                #Si Agente=R.I y Suj.Perc = R.I : Letra = A, M, B
                #Si Agente=R.I y Suj.Perc = Exento : Letra = B
                #Si Agente=R.I y Suj.Perc = Monot. : Letra = A, M
                #Si Agente=R.I y Suj.Perc = No Cat. : Letra = B
                #Si Agente=Exento y Suj.Perc=R.I : Letra = C
                #Si Agente=Exento y Suj.Perc=Exento : Letra = C
                #Si Agente=Exento y Suj.Perc=Monot. : Letra = C
                #Si Agente=Exento y Suj.Perc=No Cat. : Letra = C
            #Operación Retenciones/Percepciones
                #Si Tipo Comprobante = (01,06,07) : A,B,C,M sino dejar 1 espacio en blanco
                #Si Tipo Comprobante = (10) : A,B,C sino dejar 1 espacio en blanco
            string = string + ' '
            # 6 campo Nro de comprobante: Largo: 16
            string = string + (payment.payment_group_id.display_name[-8:]).zfill(16)
            # 7 campo Fecha de Comprobante : dd/mm/aaaa
            string = string + str(payment.date)[8:10] + '/' + str(payment.date)[5:7] + '/' + str(payment.date)[:4]
            # 8 campo Monto del comprobante: Máximo: 9999999999999,99
            string = string + ("%.2f"%(payment.withholding_base_amount)).zfill(16).replace('.',',')
            # 9 campo Nro de certificado propio:
            # Si Tipo de Operación =1 se
            # carga el N° de certificado o
            # blancos.
            # Si Tipo de Operación = 2 se
            # completa con blancos. Largo: 16
            string = string + payment.withholding_number.zfill(16)
            # 10 campo Tipo de documento del Retenido / Percibido. 3: CUIT 2: CUIL 1: CDI
            if payment.partner_id.l10n_latam_identification_type_id.name == 'CUIT':
                string = string + '3'
            elif payment.partner_id.l10n_latam_identification_type_id.name == 'VAT':
                string = string + '3'
            elif payment.partner_id.l10n_latam_identification_type_id.name == 'CUIL':
                string = string + '2'
            elif payment.partner_id.l10n_latam_identification_type_id.name == 'Cédula Extranjera':
                string = string + '1'
            # 11 campo Nro de documento del Retenido / Percibido. Largo: 11
            string = string + payment.partner_id.vat
            # 12 campo Situación IB del Retenido / Percibido. 1: Local 2: Convenio Multilateral 4: No inscripto 5: Reg.Simplificado
            if not payment.partner_id.gross_income_type:
                raise ValidationError('El cliente {0} no tiene en su formulario completo el campo de "Tipo IIBB" y su correspondiente número'.format(payment.partner_id.name))
            if payment.partner_id.gross_income_type == 'local':
                string = string + '1'
            elif payment.partner_id.gross_income_type == 'multilateral':
                string = string + '2'
            elif payment.partner_id.gross_income_type == 'no_liquida':
                string = string + '4'
            elif payment.partner_id.gross_income_type == 'reg_simplificado':
                string = string + '5'
            # 13 Nro Inscripción IB del Retenido / Percibido. Si Situación IB del Retenido=4 : 00000000000
            if payment.partner_id.gross_income_type == 'no_liquida':
                string = string + '00000000000'
            else:
                if payment.partner_id.gross_income_type == 'local':
                    string = string + '0' + payment.partner_id.vat[:-1]
                else:
                    string = string + payment.partner_id.vat
            # 14 Situación frente al IVA del Retenido / Percibido. 1 - Responsable Inscripto 3 - Exento 4 - Monotributo
            situacion = ' '
            if payment.partner_id.l10n_ar_afip_responsibility_type_id.code == '1':
                situacion = '1'
            elif payment.partner_id.l10n_ar_afip_responsibility_type_id.code == '4':
                situacion = '3'
            elif payment.partner_id.l10n_ar_afip_responsibility_type_id.code == '6':
                situacion = '4'
            string = string + situacion
            # 15 Razón Social del Retenido/Percibido. Largo 30
            string = string + payment.partner_id.name[:30].ljust(30)
            # 16 Importe otros conceptos . Largo 16
            string = string + '0000000000000,00' # VERIFICAR
            # 17 Importe IVA . Largo 16. Sólo completar si emisor es R.I.
                                        #y receptor R.I. y letra del
                                        #Comprobante = (A, M.)
                                        #Si emisor es R.I. y Receptor
                                        #Monotributo, no completar
            string = string + '0000000000000,00' # VERIFICAR
            # 18 Monto Sujeto a Retención / Percepción . Largo 16. Monto Sujeto a Retención/
                                                                    #Percepción = (Monto del comp -
                                                                    #Importe Iva - Importe otros
                                                                    #conceptos)
            string = string + ("%.2f"%(payment.withholding_base_amount)).zfill(16).replace('.',',')
            # 19 Alicuota. Largo 5. Mayor a 0(cero) - Excepto Código de Norma 28 y 29. Según el Tipo de Op. ,Código de Norma y Tipo de Agente
            string = string + (("%.2f"%_alicuota_ret).zfill(5)).replace('.',',')
            # 20 Retención / Percepción Practicada. Largo 16. Retención/Percepción
                                                                #Practicada = Monto Sujeto a
                                                                #Retención/ Percepción *
                                                                #Alícuota /100
            string = string + (("%.2f"%((payment.withholding_base_amount * _alicuota_ret)/100)).zfill(16)).replace('.',',')
            # 21 Monto Total Retenido/Percibido. Largo 16. Igual a Retención / Percepción Practicada
            string = string + (("%.2f"%((payment.withholding_base_amount * _alicuota_ret)/100)).zfill(16)).replace('.',',')
            # 22 Aceptación. Largo 1. Solo en los casos de Retenciones por el "Régimen de Factura de Crédito Electrónica Mi
                                        #PyMEs" (Tipo de Comprobante = 10, 11, 12, 13), debe informar: E: Aceptación Expresa,
                                        #T: Aceptación Tácita. En los demás casos de retenciones y/o percepciones dejar 1 (un) espacio en blanco.
            string = string + ' ' # VERIFICAR
            # 23 Fecha Aceptación "Expresa". Largo 10. Formato: dd/mm/aaaa. Sí, en Orden 22, E: Aceptación Expresa, informar Fecha de "Aceptación Expresa", en caso
            #de aceptación Tacita y para el resto de las retenciones y/o percepciones, dejar 10 (diez)espacios en blanco.
            string = string + '         ' # VERIFICAR
            



            
            # CRLF
            string = string + windows_line_ending
            list_order_agip.append({'Fecha':[string[-223:-213]],'Texto':string[-227:]})
            
        _logger.warning('******* string: {0}'.format(string))
        self.export_agip_data_ret = string

        # Percepciones
        invoices = self.env['account.move'].search([('move_type','in',['out_invoice']),('state','=','posted'),('invoice_date','<=',self.date_to),('invoice_date','>=',self.date_from)],order='invoice_date asc')
        string = ''
        for invoice in invoices:
            taxes = json.loads(invoice.tax_totals_json)['groups_by_subtotal']['Importe libre de impuestos']
            for tax in taxes:
                if tax['tax_group_name'] == 'Perc IIBB CABA':
                    _alicuota_per = invoice.partner_id.alicuot_per_agip_ids.filtered(lambda l: l.effective_date_from == self.date_from)[0].a_per
                    if not _alicuota_per and _alicuota_per != 0.00:
                        raise ValidationError('No se encontro un padron en el cliente {0} de fecha {1} para calcular su alicuota de percepcion'.format(invoice.partner_id.name, self.date_from))
                    _logger.warning('**** Factura: {0}'.format(invoice.name))
                    #Multimoneda
                    if invoice.currency_id.name != 'ARS':
                        for ml in invoice.line_ids:
                            if ml.name == 'Percepción IIBB CABA Aplicada':
                                if invoice.move_type == 'out_refund':
                                    tax_group_amount = ml.debit
                                else:
                                    tax_group_amount = ml.credit
                    else:
                        tax_group_amount = tax['tax_group_amount']
                    # TXT segun formato de https://www.agip.gob.ar/agentes/agentes-de-recaudacion/ib-agentes-recaudacion/aplicativo-arciba/aclaraciones-sobre-las-adecuaciones-al-aplicativo-e-arciba-
                    # 1 campo Tipo de Operación: 1: Retención / 2: Percepción
                    string = string + '2'
                    # 2 campo Código de Norma: Según Tipo de Operación
                    if not self.env.user.company_id.regimen_agip_per:
                        raise ValidationError('Debe seleccionar un código de norma de AGIP para la compania ' + self.env.user.company_id.name)
                    string = string + self.env.user.company_id.regimen_agip_per.zfill(3)
                    # 3 campo Fecha de Retención / Percepción : dd/mm/aaaa
                    string = string + str(invoice.invoice_date)[8:10] + '/' + str(invoice.invoice_date)[5:7] + '/' + str(invoice.invoice_date)[:4]
                    # 4 campo Tipo de comprobante origen de la Retención / Percepción : Según Tipo de Operación
                    #Si Tipo de Operación = 1
                        #01- Factura
                        #02- Nota de Débito
                        #03- Orden de Pago
                        #04- Boleta de Depósito
                        #05- Liquidación de pago
                        #06- Certificado de obra
                        #07- Recibo
                        #08- Cont de Loc de Servic.
                        #09- Otro Comprobante
                        #10- Factura de Crédito Electrónica MiPyMEs.
                        #11- Nota de Débito Electrónica MiPyMEs.
                        #12- Orden de Pago de Comp. Electrónica MiPyMEs
                        #13- Otro Comp. de Crédito Electrónicas MiPyMEs.
                    #Si Tipo de Operación = 2
                        #01- Factura
                        #09- Otro Comprobante
                        #10- Factura de Crédito Electrónica MiPyMEs.
                        #13- Otro Comp de Crédito Electrónicas MiPyMEs
                    if invoice.l10n_latam_document_type_id.code == '201':
                        #10 Factura de Crédito Electrónica
                        string = string + '10'
                    else:
                        #01- Factura
                        string = string + '01'
                    # 5 campo Letra del Comprobante
                    #Operación Retenciones
                        #Si Agente=R.I y Suj.Ret = R.I : Letra = A, M, B
                        #Si Agente=R.I y Suj.Ret = Exento : Letra = C
                        #Si Agente=R.I y Suj.Ret = Monot : Letra = C
                        #Si Agente=Exento y Suj.Ret=R.I : Letra = B
                        #Si Agente=Exento y Suj.Ret=Exento : Letra = C
                        #Si Agente=Exento y Suj.Ret=Monot. : Letra = C
                    #Operación Percepción
                        #Si Agente=R.I y Suj.Perc = R.I : Letra = A, M, B
                        #Si Agente=R.I y Suj.Perc = Exento : Letra = B
                        #Si Agente=R.I y Suj.Perc = Monot. : Letra = A, M
                        #Si Agente=R.I y Suj.Perc = No Cat. : Letra = B
                        #Si Agente=Exento y Suj.Perc=R.I : Letra = C
                        #Si Agente=Exento y Suj.Perc=Exento : Letra = C
                        #Si Agente=Exento y Suj.Perc=Monot. : Letra = C
                        #Si Agente=Exento y Suj.Perc=No Cat. : Letra = C
                    #Operación Retenciones/Percepciones
                        #Si Tipo Comprobante = (01,06,07) : A,B,C,M sino dejar 1 espacio en blanco
                        #Si Tipo Comprobante = (10) : A,B,C sino dejar 1 espacio en blanco
                    string = string + invoice.l10n_latam_document_type_id.l10n_ar_letter
                    # 6 campo Nro de comprobante: Largo: 16
                    string = string + (str(invoice.name)[-14:-9] + str(invoice.name)[-8:]).zfill(16)
                    # 7 campo Fecha de Comprobante : dd/mm/aaaa
                    string = string + str(invoice.invoice_date)[8:10] + '/' + str(invoice.invoice_date)[5:7] + '/' + str(invoice.invoice_date)[:4]
                    # 8 campo Monto del comprobante: Máximo: 9999999999999,99
                    if invoice.currency_id.name != 'ARS':
                        cadena = "%.2f"%((invoice.amount_total * invoice.l10n_ar_currency_rate) - tax_group_amount)
                    else:
                        cadena = "%.2f"%(invoice.amount_total - tax_group_amount)
                    cadena = cadena.replace('.',',')
                    string = string + cadena.zfill(16)
                    # 9 campo Nro de certificado propio:
                    # Si Tipo de Operación =1 se
                    # carga el N° de certificado o
                    # blancos.
                    # Si Tipo de Operación = 2 se
                    # completa con blancos. Largo: 16
                    string = string + '                ' # Verificar
                    # 10 campo Tipo de documento del Retenido / Percibido. 3: CUIT 2: CUIL 1: CDI
                    if invoice.partner_id.l10n_latam_identification_type_id.name == 'CUIT':
                        string = string + '3'
                    elif invoice.partner_id.l10n_latam_identification_type_id.name == 'CUIL':
                        string = string + '2'
                    elif invoice.partner_id.l10n_latam_identification_type_id.name == 'Cédula Extranjera':
                        string = string + '1'
                    # 11 campo Nro de documento del Retenido / Percibido. Largo: 11
                    string = string + invoice.partner_id.vat
                    # 12 campo Situación IB del Retenido / Percibido. 1: Local 2: Convenio Multilateral 4: No inscripto 5: Reg.Simplificado
                    if invoice.partner_id.gross_income_type == 'local':
                        string = string + '1'
                    elif invoice.partner_id.gross_income_type == 'multilateral':
                        string = string + '2'
                    elif invoice.partner_id.gross_income_type == 'no_liquida':
                        string = string + '4'
                    elif invoice.partner_id.gross_income_type == 'reg_simplificado':
                        string = string + '5'
                    else:
                        raise ValidationError('El cliente {0} con cuit {1} no tiene configurada su situación IIBB en su formulario de cliente'.format(invoice.partner_id.name,invoice.partner_id.vat))
                    # 13 Nro Inscripción IB del Retenido / Percibido. Si Situación IB del Retenido=4 : 00000000000
                    if invoice.partner_id.gross_income_type == 'no_liquida':
                        string = string + '00000000000'
                    else:
                        if invoice.partner_id.gross_income_type == 'local':
                            string = string + '0' + invoice.partner_id.vat[:-1]
                        else:
                            string = string + invoice.partner_id.vat
                    # 14 Situación frente al IVA del Retenido / Percibido. 1 - Responsable Inscripto 3 - Exento 4 - Monotributo
                    if invoice.partner_id.l10n_ar_afip_responsibility_type_id.code == '1':
                        string = string + '1'
                    elif invoice.partner_id.l10n_ar_afip_responsibility_type_id.code == '4':
                        string = string + '3'
                    elif invoice.partner_id.l10n_ar_afip_responsibility_type_id.code == '6':
                        string = string + '4'
                    # 15 Razón Social del Retenido/Percibido. Largo 30
                    string = string + invoice.partner_id.name[:30].ljust(30)
                    # 16 Importe otros conceptos . Largo 16
                    iva_tmp = 0
                    for tax_iva in taxes:
                            if tax_iva['tax_group_name'] in ['IVA 27%','IVA 21%','IVA 10.5%']:
                                iva_tmp += tax_iva['tax_group_amount']
                    if invoice.currency_id.name != 'ARS':
                        otros_conceptos = (invoice.amount_total * invoice.l10n_ar_currency_rate) - (iva_tmp * invoice.l10n_ar_currency_rate) - tax_group_amount - (invoice.amount_untaxed * invoice.l10n_ar_currency_rate)
                    else:
                        otros_conceptos = invoice.amount_total - iva_tmp - tax_group_amount - invoice.amount_untaxed
                    if otros_conceptos < 0:
                        otros_conceptos = otros_conceptos * -1
                    string = string + ("%.2f"%(otros_conceptos)).replace('.',',').zfill(16)
                    # 17 Importe IVA . Largo 16. Sólo completar si emisor es R.I.
                                                #y receptor R.I. y letra del
                                                #Comprobante = (A, M.)
                                                #Si emisor es R.I. y Receptor
                                                #Monotributo, no completar
                    if invoice.partner_id.l10n_ar_afip_responsibility_type_id.code == '6':
                        string = string + '0000000000000,00' # VERIFICAR
                    elif invoice.l10n_latam_document_type_id.l10n_ar_letter in ['A','M']:
                        iva_invoice = ''
                        iva_tmp = 0
                        for tax_iva in taxes:
                            if tax_iva['tax_group_name'] in ['IVA 27%','IVA 21%','IVA 10.5%']:
                                if invoice.currency_id.name != 'ARS':
                                    iva_tmp += tax_iva['tax_group_amount'] * invoice.l10n_ar_currency_rate
                                else:
                                    iva_tmp += tax_iva['tax_group_amount']
                        iva_invoice = ("%.2f"%iva_tmp).replace('.',',').zfill(16)
                        string = string + iva_invoice.zfill(16)

                    # 18 Monto Sujeto a Retención / Percepción . Largo 16. Monto Sujeto a Retención/
                                                                            #Percepción = (Monto del comp -
                                                                            #Importe Iva - Importe otros
                                                                            #conceptos)
                    #Bandera para calculo de redondeo de base segun se corroboro para que agip no rechace el txt el calculo de 
                    # el monto sujeto (Monto total - percepcion) tiene que ser exactamente igual a monto base + otros conceptos + iva
                    if invoice.currency_id.name != 'ARS':
                        calculo = ((invoice.amount_total * invoice.l10n_ar_currency_rate) - tax_group_amount) - otros_conceptos - float(iva_invoice.replace(',','.'))
                    else:
                        calculo = (invoice.amount_total - tax_group_amount) - otros_conceptos - float(iva_invoice.replace(',','.'))
                    monto_sujeto = ("{:0>%dd}" % 15).format(int(round(abs(calculo) * 10**2, 2)))
                    #Verifico si tengo que redondear para arriba si el tercer decimal > 5
                    redondear = ("{:0>%dd}" % 15).format(int(round(abs(calculo) * 10**3, 3)))
                    if int(redondear[-1]) > 4:
                        monto_sujeto = ("{:0>%dd}" % 15).format(int(round(abs(calculo + 0.01) * 10**2, 2)))
                    _logger.warning('******** Factura: {0}'.format(invoice.name))
                    _logger.warning('******** monto_sujeto: {0}'.format(monto_sujeto[:-2]+','+monto_sujeto[-2:]))

                    string = string + monto_sujeto[:-2]+','+monto_sujeto[-2:]
                
                    # 19 Alicuota. Largo 5. Mayor a 0(cero) - Excepto Código de Norma 28 y 29. Según el Tipo de Op. ,Código de Norma y Tipo de Agente
                    string = string + (("%.2f"%_alicuota_per).zfill(5)).replace('.',',')
                    # 20 Retención / Percepción Practicada. Largo 16. Retención/Percepción
                                                                        #Practicada = Monto Sujeto a
                                                                        #Retención/ Percepción *
                                                                        #Alícuota /100
                    string = string + ("%.2f"%tax_group_amount).replace('.',',').zfill(16)
                    # 21 Monto Total Retenido/Percibido. Largo 16. Igual a Retención / Percepción Practicada
                    string = string + ("%.2f"%tax_group_amount).replace('.',',').zfill(16)
                    # 22 Aceptación. Largo 1. Solo en los casos de Retenciones por el "Régimen de Factura de Crédito Electrónica Mi
                                                #PyMEs" (Tipo de Comprobante = 10, 11, 12, 13), debe informar: E: Aceptación Expresa,
                                                #T: Aceptación Tácita. En los demás casos de retenciones y/o percepciones dejar 1 (un) espacio en blanco.
                    string = string + ' ' # VERIFICAR
                    # 23 Fecha Aceptación "Expresa". Largo 10. Formato: dd/mm/aaaa. Sí, en Orden 22, E: Aceptación Expresa, informar Fecha de "Aceptación Expresa", en caso
                    #de aceptación Tacita y para el resto de las retenciones y/o percepciones, dejar 10 (diez)espacios en blanco.
                    string = string + '         ' # VERIFICAR
                    



                    
                    # CRLF
                    string = string + windows_line_ending
                    list_order_agip.append({'Fecha':[string[-223:-213]],'Texto':string[-227:]})
                    
                _logger.warning('******* string: {0}'.format(string))
                self.export_agip_data_per = string
        
        #Ordenamos Retenciones y Percepciones en un mismo txt
        ordenado = sorted(list_order_agip, key=lambda ret : ret['Fecha'])
        string_ordenado = ''
        self.export_agip_data = ''
        for o in ordenado:
            string_ordenado = string_ordenado + o['Texto']
        self.export_agip_data = string_ordenado

        # Notas de credito
        invoices = self.env['account.move'].search([('move_type','in',['out_refund']),('state','=','posted'),('invoice_date','<=',self.date_to),('invoice_date','>=',self.date_from)],order='invoice_date asc')
        string = ''
        for invoice in invoices:
            taxes = json.loads(invoice.tax_totals_json)['groups_by_subtotal']['Importe libre de impuestos']
            for tax in taxes:
                if tax['tax_group_name'] == 'Perc IIBB CABA':
                    #Multimoneda
                    if invoice.currency_id.name != 'ARS':
                        for ml in invoice.line_ids:
                            if ml.name == 'Percepción IIBB CABA Aplicada':
                                if invoice.move_type == 'out_refund':
                                    tax_group_amount = ml.debit
                                else:
                                    tax_group_amount = ml.credit
                    else:
                        tax_group_amount = tax['tax_group_amount']
                    # TXT segun formato de https://www.agip.gob.ar/agentes/agentes-de-recaudacion/ib-agentes-recaudacion/aplicativo-arciba/aclaraciones-sobre-las-adecuaciones-al-aplicativo-e-arciba-
                    # 1 campo Tipo de Operación: 1: Retención / 2: Percepción
                    string = string + '2'
                    # 2 campo Nro. Nota de crédito
                    string = string + (str(invoice.name)[-13:-9] + str(invoice.name)[-8:]).zfill(12)
                    # 3 campo Fecha Nota de crédito : dd/mm/aaaa
                    string = string + str(invoice.invoice_date)[8:10] + '/' + str(invoice.invoice_date)[5:7] + '/' + str(invoice.invoice_date)[:4]
                    # 4 campo Monto nota de crédito 
                    if invoice.reversed_entry_id:
                        if invoice.reversed_entry_id.currency_id.name != 'ARS':
                            cadena = "%.2f"%(invoice.reversed_entry_id.amount_untaxed  * invoice.reversed_entry_id.l10n_ar_currency_rate)
                        else:
                            cadena = "%.2f"%invoice.reversed_entry_id.amount_untaxed
                        cadena = cadena.replace('.',',')
                        string = string + cadena.zfill(16)
                    else:
                        string = string + "'NC sin factura de reversion, reemplazar por nº correspondiente (16 Long)'"
                    # 5 campo Nro de certificado propio:
                    # completa con blancos. Largo: 16
                    string = string + '                ' # Verificar
                    # 6 campo Tipo de comprobante origen de la Retención / Percepción : Según Tipo de Operación
                    #Si Tipo de Operación = 1
                        #01- Factura
                        #02- Nota de Débito
                        #03- Orden de Pago
                        #04- Boleta de Depósito
                        #05- Liquidación de pago
                        #06- Certificado de obra
                        #07- Recibo
                        #08- Cont de Loc de Servic.
                        #09- Otro Comprobante
                        #10- Factura de Crédito Electrónica MiPyMEs.
                        #11- Nota de Débito Electrónica MiPyMEs.
                        #12- Orden de Pago de Comp. Electrónica MiPyMEs
                        #13- Otro Comp. de Crédito Electrónicas MiPyMEs.
                    #Si Tipo de Operación = 2
                        #01- Factura
                        #09- Otro Comprobante
                        #10- Factura de Crédito Electrónica MiPyMEs.
                        #13- Otro Comp de Crédito Electrónicas MiPyMEs
                    if invoice.l10n_latam_document_type_id.code == '201':
                        #10 Factura de Crédito Electrónica
                        string = string + '10'
                    else:
                        #01- Factura
                        string = string + '01'
                    # 7 campo Letra del Comprobante
                    #Operación Retenciones
                        #Si Agente=R.I y Suj.Ret = R.I : Letra = A, M, B
                        #Si Agente=R.I y Suj.Ret = Exento : Letra = C
                        #Si Agente=R.I y Suj.Ret = Monot : Letra = C
                        #Si Agente=Exento y Suj.Ret=R.I : Letra = B
                        #Si Agente=Exento y Suj.Ret=Exento : Letra = C
                        #Si Agente=Exento y Suj.Ret=Monot. : Letra = C
                    #Operación Percepción
                        #Si Agente=R.I y Suj.Perc = R.I : Letra = A, M, B
                        #Si Agente=R.I y Suj.Perc = Exento : Letra = B
                        #Si Agente=R.I y Suj.Perc = Monot. : Letra = A, M
                        #Si Agente=R.I y Suj.Perc = No Cat. : Letra = B
                        #Si Agente=Exento y Suj.Perc=R.I : Letra = C
                        #Si Agente=Exento y Suj.Perc=Exento : Letra = C
                        #Si Agente=Exento y Suj.Perc=Monot. : Letra = C
                        #Si Agente=Exento y Suj.Perc=No Cat. : Letra = C
                    #Operación Retenciones/Percepciones
                        #Si Tipo Comprobante = (01,06,07) : A,B,C,M sino dejar 1 espacio en blanco
                        #Si Tipo Comprobante = (10) : A,B,C sino dejar 1 espacio en blanco
                    string = string + invoice.l10n_latam_document_type_id.l10n_ar_letter
                    # 8 campo Nro de comprobante: Largo: 16
                    #string = string + (str(invoice.name)[-14:-9] + str(invoice.name)[-8:]).zfill(16)
                    if invoice.reversed_entry_id:
                        string = string + (str(invoice.reversed_entry_id.name)[-14:-9] + str(invoice.reversed_entry_id.name)[-8:]).zfill(16)
                    else: 
                        string = string + "'No se encontro numero de reversion, reemplazar esto por el correspondiente (16 campos)'"
                    # 9 campo Nro de documento del Retenido / Percibido. Largo: 11
                    string = string + invoice.partner_id.vat
                    # 10 campo Código de Norma: Según Tipo de Operación
                    if not self.env.user.company_id.regimen_agip_per:
                        raise ValidationError('Debe seleccionar un código de norma de AGIP para la compania ' + self.env.user.company_id.name)
                    string = string + self.env.user.company_id.regimen_agip_per.zfill(3)
                    # 11 campo Fecha de Retención /Percepción : dd/mm/aaaa
                    string = string + str(invoice.invoice_date)[8:10] + '/' + str(invoice.invoice_date)[5:7] + '/' + str(invoice.invoice_date)[:4]
                    # 12 Retención / Percepción a deducir . Largo 16.
                    string = string + ("%.2f"%tax_group_amount).replace('.',',').zfill(16)
                    # 13 Alícuota . Largo 5.
                    if invoice.currency_id.name != 'ARS':
                        string = string + ("%.2f"%((tax_group_amount*100) / (tax['tax_group_base_amount'] * invoice.l10n_ar_currency_rate))).replace('.',',').zfill(5)
                    else:
                        string = string + ("%.2f"%((tax_group_amount*100) / tax['tax_group_base_amount'])).replace('.',',').zfill(5)
                    
                    # CRLF
                    string = string + windows_line_ending
                    
                self.export_agip_data_nc = string
