# -*- coding: utf-8 -*-
from odoo import models, api, fields
from collections import defaultdict
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.exceptions import ValidationError
from datetime import date
import logging
_logger = logging.getLogger(__name__)

class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    def calculate_perceptions(self):
        if self.move_type == 'out_invoice' or self.move_type == 'out_refund':
            #Verificamos que la factura tenga fecha para luego poder calcular a que padron consultar el monto
            if not self.invoice_date:
                self.invoice_date = date.today()
            if self.invoice_line_ids:
                if self.partner_id:
                    if len(self.partner_id.alicuot_per_tucuman_ids) > 0:
                        #Busco el impuesto a utilizar para la percepcion
                        imp_per_tucuman = self.company_id.tax_per_tucuman
                        if len(imp_per_tucuman) == 0:
                            return super(AccountMoveInherit, self).calculate_perceptions()

                        # Cambio el amount del impuesto por el valor que tenga el partner en el padron
                        imp_per_tucuman.amount = self.partner_id.get_amount_alicuot_tucuman('per',self.invoice_date)
                        # Recomerremos las lineas en busca de si ya se encuentra el impuesto de percepcion, de caso contrario se agrega
                        for iline in self.invoice_line_ids:
                            _tiene_precepcion = 0

                            for tax in iline.tax_ids:
                                if str(imp_per_tucuman.id) == str(tax.id)[-2:]:
                                    _tiene_precepcion = 1
                            if not _tiene_precepcion and imp_per_tucuman.amount > 0:
                                iline.write({'tax_ids': [(4, imp_per_tucuman.id)]})

                        # Recomputamos Apuntes contables y actualizamos el valor de Cuenta a Pagar por el total de la factura
                        for lac in self.line_ids:
                            if lac.account_id.id == self.partner_id.property_account_receivable_id.id:
                                if self.move_type == 'out_invoice':
                                    if self.currency_id.name != 'ARS':
                                        debit_tmp = 0
                                        for lac_credit in self.line_ids:
                                            debit_tmp += lac_credit.credit
                                        lac.write({'debit' : debit_tmp})
                                    else:
                                        lac.write({'debit' : self.amount_total})
                                elif self.move_type == 'out_refund':
                                    if self.currency_id.name != 'ARS':
                                        credit_tmp = 0
                                        for lac_debit in self.line_ids:
                                            credit_tmp += lac_debit.debit
                                        lac.write({'credit' : credit_tmp})
                                    else:
                                        lac.write({'credit' : self.amount_total})

        return super(AccountMoveInherit, self).calculate_perceptions()