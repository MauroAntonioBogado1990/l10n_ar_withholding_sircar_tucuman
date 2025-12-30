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
        """
        Función principal activada por el botón 'Procesar'.
        Lee el archivo binario, lo parsea y actualiza los registros en 'tucuman.padron'.
        """
        _procesados = ""      # Acumulador de texto para mostrar qué CUITs se cargaron bien
        _noprocesados = ""    # Acumulador de texto para las líneas que dieron error
        vals = {}             # Diccionario temporal para guardar los datos antes de crear/escribir
        self.ensure_one()     # Asegura que solo se procese un registro de importación a la vez

        # --- VALIDACIONES INICIALES ---
        if not self.padron_match:
            raise ValidationError('Debe seleccionar metodo de busqueda de Clientes')
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.padron_file:
            raise ValidationError('Debe seleccionar el archivo')
        if self.state != 'draft':
            raise ValidationError('Archivo procesado!')

        # --- DECODIFICACIÓN DEL ARCHIVO ---
        # Odoo guarda los archivos en Base64; aquí lo convertimos a texto plano y dividimos por líneas
        self.file_content = base64.decodebytes(self.padron_file)
        lines = self.file_content.split('\n')

        # OPTIMIZACIÓN: Buscamos todos los CUITs de clientes existentes en Odoo.
        # Esto evita hacer una consulta a la base de datos por cada línea del archivo (mejora el rendimiento).
        partners = self.env['res.partner'].search([('vat', '!=', False), ('parent_id', '=', False)])
        cuit_partners = [c.vat for c in partners]

        # --- FUNCIONES DE AYUDA (Helpers) ---
        def _parse_float(s):
            """ Convierte strings de texto con formato argentino (coma para decimales) a números float """
            try:
                if s is None:
                    return 0.0
                s2 = str(s).strip().replace(',', '.').replace('-', '')
                if s2 == '' or all(ch == '-' for ch in str(s).strip()):
                    return 0.0
                return float(s2)
            except Exception:
                return 0.0

        def _normalize_type(tc):
            """ Normaliza las siglas del padrón: CM (Convenio Multilateral), CL (Contribuyente Local), E (Exento) """
            if not tc:
                return ''
            t = tc.strip()
            if 'E' in t: return 'E'
            if 'CM' in t: return 'CM'
            if 'CL' in t: return 'CL'
            return t

        # --- CICLO DE PROCESAMIENTO ---
        for i, line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue # Salta el encabezado si está marcado en el formulario

            line = line.strip()
            if not line:
                continue # Salta líneas vacías

            # Separamos la línea usando el delimitador configurado (generalmente ';' o ',')
            lista = line.split(self.delimiter)

            # --- CASO 1: ARCHIVO COMPLETO (Más de 11 columnas) ---
            # Este es el formato oficial de Rentas con alícuotas detalladas
            if len(lista) > 11:
                cuit = lista[3].strip()
                # Si el CUIT del archivo no está entre nuestros clientes, lo ignoramos para no llenar la DB de basura
                if not cuit or cuit not in cuit_partners:
                    continue

                # Mapeo de columnas según el estándar de Tucumán
                publication_date = lista[0]
                effective_date_from = lista[1]
                effective_date_to = lista[2]
                type_contr_insc = _normalize_type(lista[4])
                alta_baja = lista[5]
                cambio = lista[6]
                a_per = lista[7]  # Alícuota Percepción
                a_ret = lista[8]  # Alícuota Retención
                nro_grupo_perc = lista[9]
                nro_grupo_ret = lista[10]

                # Convertimos las fechas del formato DDMMYYYY a formato Odoo YYYY-MM-DD
                vals.clear()
                vals['publication_date'] = datetime.strptime(
                    (publication_date[:2] + '/' + publication_date[2:4] + '/' + publication_date[4:]), '%d/%m/%Y'
                )
                vals['effective_date_from'] = datetime.strptime(
                    (effective_date_from[:2] + '/' + effective_date_from[2:4] + '/' + effective_date_from[4:]), '%d/%m/%Y'
                )
                vals['effective_date_to'] = datetime.strptime(
                    (effective_date_to[:2] + '/' + effective_date_to[2:4] + '/' + effective_date_to[4:]), '%d/%m/%Y'
                )
                vals['name'] = cuit
                vals['type_contr_insc'] = type_contr_insc
                vals['alta_baja'] = alta_baja
                vals['a_per'] = _parse_float(a_per)
                vals['a_ret'] = _parse_float(a_ret)
                vals['cambio'] = cambio

                # PROCESAR PERCEPCIÓN (P)
                padron_existe = self.env['tucuman.padron'].search([('name', '=', cuit), ('type_alicuot', '=', 'P')])
                if padron_existe:
                    # Si ya existe el registro de percepción para este CUIT, lo actualizamos
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
                    # Si no existe, creamos un registro nuevo de tipo Percepción
                    vals['type_alicuot'] = 'P'
                    vals['a_ret'] = 0.0
                    vals['nro_grupo_perc'] = nro_grupo_perc
                    self.env['tucuman.padron'].sudo().create(vals)

                # PROCESAR RETENCIÓN (R)
                # Repetimos la lógica pero para el registro de Retención
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

            # --- CASO 2: ARCHIVO SIMPLE (Solo 2 columnas: CUIT y Nombre) ---
            elif len(lista) == 2:
                # Se utiliza cuando el cliente solo provee una lista de contribuyentes sin alícuotas
                left = lista[0].strip()
                right = lista[1].strip()
                partes_left = left.split()

                def _is_cuit(s):
                    """ Valida si el texto tiene 11 dígitos (formato CUIT) """
                    if not s: return False
                    ds = ''.join(ch for ch in s if ch.isdigit())
                    return len(ds) == 11

                cuit = None
                # Intentamos detectar cuál de las partes es el CUIT
                if len(partes_left) >= 1 and _is_cuit(partes_left[0]):
                    cuit = ''.join(ch for ch in partes_left[0] if ch.isdigit())
                
                if not cuit or cuit not in cuit_partners:
                    continue

                # Preparamos valores genéricos (alícuota 0 pero marcado como activo)
                vals.clear()
                vals['name'] = cuit
                vals['publication_date'] = datetime.today()
                vals['effective_date_from'] = datetime.today()
                vals['effective_date_to'] = datetime.today()
                vals['type_contr_insc'] = 'CM'
                vals['alta_baja'] = 'S' # S de Sujeto activo
                vals['a_per'] = 0.0
                vals['a_ret'] = 0.0

                padron_existe = self.env['tucuman.padron'].search([('name', '=', cuit)])
                if padron_existe:
                    padron_existe.sudo().write(vals)
                else:
                    vals['type_alicuot'] = 'P'
                    self.env['tucuman.padron'].sudo().create(vals)

                _procesados += "{} {}\n".format(cuit, right)

            else:
                # Si la línea no cumple con ningún formato, la mandamos a la lista de errores
                _noprocesados += "{}\n".format(line)
                continue

        # Al finalizar el bucle, informamos los resultados en el formulario
        self.clientes_cargados = _procesados
        self.not_processed_content = _noprocesados
        self.state = 'processed' # Cambiamos estado para evitar doble procesamiento
        

    
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
        """
        Calcula automáticamente cuántas filas tiene el archivo subido
        y extrae el contenido de texto para previsualizarlo.
        """
        for rec in self:
            # 1. Inicializamos el contador en cero por seguridad
            rec.lineas_archivo = 0
            
            # 2. Verificamos si realmente hay un archivo cargado
            if rec.padron_file:
                try:
                    # DECODIFICACIÓN: 
                    # Odoo guarda los archivos (Binary) en formato Base64. 
                    # Primero lo pasamos a bytes puros.
                    file_content = base64.b64decode(rec.padron_file)
                    
                    # CONVERSIÓN A TEXTO:
                    # Pasamos esos bytes a texto legible (UTF-8). 
                    # 'errors=ignore' evita que el proceso se corte si el archivo tiene caracteres extraños.
                    decoded_text = file_content.decode('utf-8', errors='ignore')
                    
                    # PROCESAMIENTO DE LÍNEAS:
                    # Dividimos el texto cada vez que encuentra un salto de línea ('\n')
                    lines = decoded_text.split('\n')
                    
                    # ASIGNACIÓN DE RESULTADOS:
                    # len(lines) nos da el total de filas. Es mucho más rápido que contar una por una.
                    rec.lineas_archivo = len(lines)
                    
                    # Guardamos el texto resultante en un campo temporal para poder verlo en la interfaz
                    rec.file_content_tmp = decoded_text
                    
                except Exception as e:
                    # MANEJO DE ERRORES:
                    # Si el archivo está corrupto o no es de texto, anotamos el error en el log del servidor
                    _logger.error("Error decodificando archivo: %s", e)
                    rec.lineas_archivo = 0
                    rec.file_content_tmp = ''
            else:
                # Si no hay archivo, el contenido y las líneas son cero
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
