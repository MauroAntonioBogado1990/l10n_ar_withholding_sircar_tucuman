# -*- coding: utf-8 -*-
from odoo import models, api, fields
from collections import defaultdict
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.exceptions import ValidationError
from datetime import date
import logging

_logger = logging.getLogger(__name__)

class AccountMoveInherit(models.Model):
    """
    Extensión del modelo de Facturas (account.move) para incluir 
    la lógica de cálculo automático de Percepciones de Ingresos Brutos (Tucumán).
    """
    _inherit = "account.move"

    def calculate_perceptions(self):
        """
        Método principal que decide si se debe aplicar la percepción de Tucumán
        y actualiza las líneas de la factura con el impuesto correspondiente.
        """
        # 1. Filtro inicial: Solo procesamos facturas de cliente (out_invoice) 
        # o notas de crédito de cliente (out_refund).
        if self.move_type in ['out_invoice', 'out_refund']:
            
            # 2. Validación de fecha: El padrón de Tucumán varía por mes. 
            # Si la factura no tiene fecha, usamos la de hoy para poder consultar el padrón.
            if not self.invoice_date:
                self.invoice_date = date.today()

            # 3. Verificamos que la factura tenga productos/servicios cargados
            if self.invoice_line_ids:
                
                # 4. Verificamos si el cliente (partner_id) existe y si está 
                # presente en el padrón de alícuotas de Tucumán.
                if self.partner_id and len(self.partner_id.alicuot_per_tucuman_ids) > 0:
                    
                    # 5. Buscamos el impuesto de percepción que la empresa tiene configurado
                    imp_per_tucuman = self.company_id.tax_per_tucuman
                    
                    # Si no hay un impuesto configurado, saltamos este proceso y seguimos con lo estándar de Odoo
                    if not imp_per_tucuman:
                        return super().calculate_perceptions()

                    # 6. OBTENCIÓN DE LA ALÍCUOTA:
                    # Llamamos a una función del cliente que busca en su padrón qué porcentaje 
                    # le corresponde pagar en la fecha de la factura.
                    new_amount = self.partner_id.get_amount_alicuot_tucuman('per', self.invoice_date)
                    
                    # 7. Actualizamos el valor del impuesto con el porcentaje obtenido del padrón
                    imp_per_tucuman.amount = new_amount        
                    
                    # 8. APLICACIÓN DEL IMPUESTO A LAS LÍNEAS:
                    # Recorremos cada producto de la factura
                    for iline in self.invoice_line_ids:
                        _tiene_precepcion = False

                        # Revisamos si la línea ya tiene aplicado este impuesto
                        for tax in iline.tax_ids:
                            # Comprobación de seguridad comparando IDs
                            if str(imp_per_tucuman.id) == str(tax.id)[-2:]:
                                _tiene_precepcion = True
                        
                        # Si la línea NO tiene la percepción y el porcentaje es mayor a 0, se la agregamos
                        if not _tiene_precepcion and imp_per_tucuman.amount > 0:
                            # (4, ID) es una instrucción de Odoo para añadir un registro a una relación
                            iline.write({'tax_ids': [(4, imp_per_tucuman.id)]})

                    # 9. RECALCULO DE ASIENTO CONTABLE:
                    # Después de agregar impuestos, el "total a cobrar" cambia. 
                    # Aquí ajustamos los apuntes contables para que el debe/haber coincida con el nuevo total.
                    for lac in self.line_ids:
                        # Buscamos la línea de "Cuenta a Cobrar" del cliente
                        if lac.account_id.id == self.partner_id.property_account_receivable_id.id:
                            
                            # Si es Factura: actualizamos el DEBE (lo que nos debe)
                            if self.move_type == 'out_invoice':
                                if self.currency_id.name != 'ARS':
                                    # Caso moneda extranjera: sumamos los créditos de las otras líneas
                                    debit_tmp = sum(self.line_ids.mapped('credit'))
                                    lac.write({'debit' : debit_tmp})
                                else:
                                    # Caso pesos: usamos el total general de la factura
                                    lac.write({'debit' : self.amount_total})
                            
                            # Si es Nota de Crédito: actualizamos el HABER (lo que le devolvemos/bonificamos)
                            elif self.move_type == 'out_refund':
                                if self.currency_id.name != 'ARS':
                                    credit_tmp = sum(self.line_ids.mapped('debit'))
                                    lac.write({'credit' : credit_tmp})
                                else:
                                    lac.write({'credit' : self.amount_total})

        # Finalmente, ejecutamos la función original del sistema para asegurar que 
        # cualquier otro cálculo estándar de Odoo se realice correctamente.
        return super(AccountMoveInherit, self).calculate_perceptions()