# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
import base64
import csv
from datetime import date as dt
import logging
_logger = logging.getLogger(__name__)



class ImportPadronTucuman(models.Model):
    _name = 'import.padron.tucuman'
    _description = 'import.padron.tucuman'
    
    #FUNCIÓN ORIGINAL PARA PROCESAR EL ARCHIVO
    # def btn_process(self):
    #     _procesados = ""
    #     _procesados_stock = ""  
    #     _noprocesados = ""
    #     vals={}    
    #     self.ensure_one()
    #     if not self.padron_match:
    #         raise ValidationError('Debe seleccionar metodo de busqueda de Clientes')
    #     if not self.delimiter:
    #         raise ValidationError('Debe ingresar el delimitador')
    #     if not self.padron_file:
    #         raise ValidationError('Debe seleccionar el archivo')
    #     if self.state != 'draft':
    #         raise ValidationError('Archivo procesado!')
    #     self.file_content = base64.decodebytes(self.padron_file)
    #     lines = self.file_content.split('\n')

    #     #Guardamos todos los cuit de clientes para luego consultar si el cliente existe y evitar hacer un search por cada linea de TXT
    #     partners = self.env['res.partner'].search([('vat','!=',False),('parent_id','=',False)])
    #     cuit_partners = []
    #     for c in partners:
    #         cuit_partners.append(c.vat)

    #     for i,line in enumerate(lines):
    #         if self.skip_first_line and i == 0:
    #             continue
    #         lista = line.split(self.delimiter)
    #         if len(lista) > 11:
    #             #Consultamos si existe el cliente segun el cuit sino seguimos a la siguiente linea para minimizar el proceso
    #             cuit = lista[3]
    #             if cuit not in cuit_partners:
    #                 continue
    #             publication_date = lista[0]
    #             effective_date_from = lista[1]
    #             effective_date_to = lista[2]
    #             type_contr_insc = lista[4]
    #             alta_baja = lista[5]
    #             cambio = lista[6]
    #             a_per = lista[7]
    #             a_ret = lista[8]
    #             nro_grupo_perc = lista[9]
    #             nro_grupo_ret = lista[10]

    #             vals.clear()

    #             # Carga vals
    #             if cuit != '': 
    #                 vals['publication_date'] = datetime.strptime((publication_date[:2] + '/' + publication_date[2:4] + '/' + publication_date[4:]), '%d/%m/%Y')
    #                 vals['effective_date_from'] = datetime.strptime((effective_date_from[:2] + '/' + effective_date_from[2:4] + '/' + effective_date_from[4:]), '%d/%m/%Y')
    #                 vals['effective_date_to'] = datetime.strptime((effective_date_to[:2] + '/' + effective_date_to[2:4] + '/' + effective_date_to[4:]), '%d/%m/%Y')
    #                 vals['name'] = cuit
    #                 vals['type_contr_insc'] = type_contr_insc
    #                 vals['alta_baja'] = alta_baja
    #                 vals['a_per'] = float(a_per.replace(',','.'))
    #                 vals['a_ret'] = float(a_ret.replace(',','.'))
    #                 vals['cambio'] = cambio

    #                 #Consultamos si el padron ya existe para Percepcion
    #                 padron_existe = self.env['tucuman.padron'].search([('name','=',cuit),('type_alicuot','=','P')])
    #                 if len(padron_existe) > 0:
    #                     padron_existe.sudo().write({
    #                         'a_per' : vals['a_per'],
    #                         'a_ret' : 0.00,
    #                         'publication_date' : vals['publication_date'],
    #                         'effective_date_from' : vals['effective_date_from'],
    #                         'effective_date_to' : vals['effective_date_to'],
    #                         'alta_baja' : vals['alta_baja'],
    #                         'type_contr_insc' : vals['type_contr_insc']
    #                     })
    #                 else:
    #                     # Creamos el padron de Percepcion
    #                     vals['type_alicuot'] = 'P'
    #                     vals['a_per'] = float(a_per.replace(',','.'))
    #                     vals['a_ret'] = 0.0
    #                     vals['nro_grupo_perc'] = nro_grupo_perc
    #                     self.env['tucuman.padron'].sudo().create(vals)

    #                 #Consultamos si el padron ya existe para Retenciones
    #                 padron_existe = self.env['tucuman.padron'].search([('name','=',cuit),('type_alicuot','=','R')])
    #                 if len(padron_existe) > 0:
    #                     padron_existe.sudo().write({
    #                         'a_per' : 0.00,
    #                         'a_ret' : vals['a_ret'],
    #                         'publication_date' : vals['publication_date'],
    #                         'effective_date_from' : vals['effective_date_from'],
    #                         'effective_date_to' : vals['effective_date_to'],
    #                         'alta_baja' : vals['alta_baja'],
    #                         'type_contr_insc' : vals['type_contr_insc']
    #                     })
    #                 else:
    #                     # Creamos el padron de Retencion
    #                     vals['type_alicuot'] = 'R'
    #                     vals['a_per'] = 0.0
    #                     vals['a_ret'] = float(a_ret.replace(',','.'))
    #                     vals['nro_grupo_ret'] = nro_grupo_ret
    #                     self.env['tucuman.padron'].sudo().create(vals)


    #                 _procesados += "{} \n".format(cuit)
                
    #             else:
    #                 _noprocesados += "{} \n".format(cuit)

    #         elif len(lista) == 1:
    #             continue
    #         else:
    #             raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. Se necesitan al menos 12 columnas".format(i, line))
    #     self.clientes_cargados = _procesados
    #     self.not_processed_content = _noprocesados
    #     self.state = 'processed'
    
    #FUNCIÓN ALTERNATIVA PARA PROCESAR EL ARCHIVO
    def btn_process(self):
        _procesados = ""
        _noprocesados = ""
        vals = {}
        self.ensure_one()

        if not self.padron_match:
            raise ValidationError('Debe seleccionar metodo de busqueda de Clientes')
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.padron_file:
            raise ValidationError('Debe seleccionar el archivo')
        if self.state != 'draft':
            raise ValidationError('Archivo procesado!')

        self.file_content = base64.decodebytes(self.padron_file)
        lines = self.file_content.split('\n')

        # Guardamos todos los CUIT de clientes para evitar search por cada línea
        partners = self.env['res.partner'].search([('vat', '!=', False), ('parent_id', '=', False)])
        cuit_partners = [c.vat for c in partners]

        def _parse_float(s):
            try:
                if s is None:
                    return 0.0
                s2 = str(s).strip().replace(',', '.').replace('-', '')
                # si era '-----' o similar, devolver 0.0
                if s2 == '' or all(ch == '-' for ch in str(s).strip()):
                    return 0.0
                return float(s2)
            except Exception:
                return 0.0

        def _normalize_type(tc):
            if not tc:
                return ''
            t = tc.strip()
            # prioritizar Exento si aparece
            if 'E' in t:
                return 'E'
            if 'CM' in t:
                return 'CM'
            if 'CL' in t:
                return 'CL'
            return t

        for i, line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue

            line = line.strip()
            if not line:
                continue

            # --- Caso CSV largo (más de 11 columnas) ---
            lista = line.split(self.delimiter)
            if len(lista) > 11:
                cuit = lista[3].strip()
                if not cuit or cuit not in cuit_partners:
                    continue

                publication_date = lista[0]
                effective_date_from = lista[1]
                effective_date_to = lista[2]
                type_contr_insc = _normalize_type(lista[4])
                alta_baja = lista[5]
                cambio = lista[6]
                a_per = lista[7]
                a_ret = lista[8]
                nro_grupo_perc = lista[9]
                nro_grupo_ret = lista[10]

                vals.clear()
                vals['publication_date'] = datetime.strptime(
                    (publication_date[:2] + '/' + publication_date[2:4] + '/' + publication_date[4:]),
                    '%d/%m/%Y'
                )
                vals['effective_date_from'] = datetime.strptime(
                    (effective_date_from[:2] + '/' + effective_date_from[2:4] + '/' + effective_date_from[4:]),
                    '%d/%m/%Y'
                )
                vals['effective_date_to'] = datetime.strptime(
                    (effective_date_to[:2] + '/' + effective_date_to[2:4] + '/' + effective_date_to[4:]),
                    '%d/%m/%Y'
                )
                vals['name'] = cuit
                vals['type_contr_insc'] = type_contr_insc
                vals['alta_baja'] = alta_baja
                vals['a_per'] = _parse_float(a_per)
                vals['a_ret'] = _parse_float(a_ret)
                vals['cambio'] = cambio

                # Percepción
                padron_existe = self.env['tucuman.padron'].search([('name', '=', cuit), ('type_alicuot', '=', 'P')])
                if padron_existe:
                    padron_existe.sudo().write({
                        'a_per': vals['a_per'],
                        'a_ret': 0.00,
                        'publication_date': vals['publication_date'],
                        'effective_date_from': vals['effective_date_from'],
                        'effective_date_to': vals['effective_date_to'],
                        'alta_baja': vals['alta_baja'],
                        'type_contr_insc': vals['type_contr_insc']
                    })
                else:
                    vals['type_alicuot'] = 'P'
                    vals['a_ret'] = 0.0
                    vals['nro_grupo_perc'] = nro_grupo_perc
                    self.env['tucuman.padron'].sudo().create(vals)

                # Retención
                padron_existe = self.env['tucuman.padron'].search([('name', '=', cuit), ('type_alicuot', '=', 'R')])
                if padron_existe:
                    padron_existe.sudo().write({
                        'a_per': 0.00,
                        'a_ret': vals['a_ret'],
                        'publication_date': vals['publication_date'],
                        'effective_date_from': vals['effective_date_from'],
                        'effective_date_to': vals['effective_date_to'],
                        'alta_baja': vals['alta_baja'],
                        'type_contr_insc': vals['type_contr_insc']
                    })
                else:
                    vals['type_alicuot'] = 'R'
                    vals['a_per'] = 0.0
                    vals['nro_grupo_ret'] = nro_grupo_ret
                    self.env['tucuman.padron'].sudo().create(vals)

                _procesados += "{}\n".format(cuit)

            # --- Caso TXT simple (CUIT + denominación) ---
            elif len(lista) == 2:
                # Caso frecuente: archivo con 2 columnas separadas por ';' -> CUIT/TIPO/Denom | Denominacion parte 2
                left = lista[0].strip()
                right = lista[1].strip()
                partes_left = left.split()

                def _is_cuit(s):
                    if not s:
                        return False
                    ds = ''.join(ch for ch in s if ch.isdigit())
                    return len(ds) == 11

                cuit = None
                denominacion = ''
                type_contr = ''

                if len(partes_left) >= 1 and _is_cuit(partes_left[0]):
                    cuit = ''.join(ch for ch in partes_left[0] if ch.isdigit())
                    if len(partes_left) >= 2:
                        type_contr = _normalize_type(partes_left[1])
                    # resto de la denominacion puede estar en left y right
                    denom_left = ' '.join(partes_left[2:]).strip() if len(partes_left) > 2 else ''
                    if denom_left:
                        denominacion = (denom_left + ' ' + right).strip()
                    else:
                        denominacion = right
                else:
                    # Fallback: intentar extraer cuit de la primera parte de la linea completa
                    ambas = (left + ' ' + right).split()
                    if len(ambas) >= 2 and _is_cuit(ambas[0]):
                        cuit = ''.join(ch for ch in ambas[0] if ch.isdigit())
                        denominacion = ' '.join(ambas[1:]).strip()

                if not cuit:
                    # no pudimos parsear, continuar sin procesar esta linea
                    _noprocesados += "{}\n".format(line)
                    continue

                if cuit not in cuit_partners:
                    continue

                vals.clear()
                vals['name'] = cuit
                vals['publication_date'] = datetime.today()
                vals['effective_date_from'] = datetime.today()
                vals['effective_date_to'] = datetime.today()
                vals['type_contr_insc'] = type_contr if type_contr else 'CM'
                vals['alta_baja'] = 'S'
                vals['a_per'] = 0.0
                vals['a_ret'] = 0.0
                vals['cambio'] = ''

                padron_existe = self.env['tucuman.padron'].search([('name', '=', cuit)])
                if padron_existe:
                    padron_existe.sudo().write(vals)
                else:
                    vals['type_alicuot'] = 'P'
                    self.env['tucuman.padron'].sudo().create(vals)

                _procesados += "{} {}\n".format(cuit, denominacion)

            elif len(lista) == 1:
                # dividir por espacios
                partes = line.split()
                if len(partes) >= 2:
                    cuit = partes[0].strip()
                    denominacion = " ".join(partes[1:]).strip()

                    if cuit not in cuit_partners:
                        continue

                    vals.clear()
                    vals['name'] = cuit
                    vals['publication_date'] = datetime.today()
                    vals['effective_date_from'] = datetime.today()
                    vals['effective_date_to'] = datetime.today()
                    vals['type_contr_insc'] = 'CM'
                    vals['alta_baja'] = 'S'
                    vals['a_per'] = 0.0
                    vals['a_ret'] = 0.0
                    vals['cambio'] = ''

                    padron_existe = self.env['tucuman.padron'].search([('name', '=', cuit)])
                    if padron_existe:
                        padron_existe.sudo().write(vals)
                    else:
                        vals['type_alicuot'] = 'P'
                        self.env['tucuman.padron'].sudo().create(vals)

                    _procesados += "{} {}\n".format(cuit, denominacion)
                else:
                    continue

            else:
                # línea mal formada: registramos en no procesados y continuamos
                _noprocesados += "{}\n".format(line)
                continue

        self.clientes_cargados = _procesados
        self.not_processed_content = _noprocesados
        self.state = 'processed'
        

    
    @api.depends('padron_file')
    def compute_lineas_archivo(self):
        #original
        # for rec in self:
        #     if rec.padron_file != False:
        #         rec.file_content_tmp = base64.decodebytes(rec.padron_file)
        #         lines = rec.file_content_tmp.split('\n')
        #         for i,line in enumerate(lines):
        #             rec.lineas_archivo += 1


        #     else:
        #         rec.lineas_archivo = 0
        # pass
        #SE AGREGA ESTA FUNCIÓN
        for rec in self:
            rec.lineas_archivo = 0
            if rec.padron_file:
                try:
                    # Odoo guarda Binary en base64, así que decodificamos UNA sola vez
                    file_content = base64.b64decode(rec.padron_file)
                    lines = file_content.decode('utf-8', errors='ignore').split('\n')
                    rec.lineas_archivo = len(lines)
                    rec.file_content_tmp = file_content.decode('utf-8', errors='ignore')
                except Exception as e:
                    _logger.error("Error decodificando archivo: %s", e)
                    rec.lineas_archivo = 0
                    rec.file_content_tmp = ''


    name = fields.Char('Nombre')
    padron_file = fields.Binary('Archivo')
    delimiter = fields.Char('Delimitador',default=";")
    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado')],string='Estado',default='draft')
    file_content = fields.Text('Texto archivo')
    file_content_tmp = fields.Text('Texto archivo')
    not_processed_content = fields.Text('Texto no procesado')
    clientes_cargados = fields.Text('Clientes cargados')
    skip_first_line = fields.Boolean('Saltear primera linea',default=True)
    padron_match = fields.Selection(selection=[('cuit','CUIT')],string='Buscar clientes por...',default='cuit')
    lineas_archivo = fields.Integer(compute=compute_lineas_archivo, store=True)
