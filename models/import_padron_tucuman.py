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

    def btn_process(self):
        _procesados = ""
        _procesados_stock = ""
        _noprocesados = ""
        vals={}    
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

        #Guardamos todos los cuit de clientes para luego consultar si el cliente existe y evitar hacer un search por cada linea de TXT
        partners = self.env['res.partner'].search([('vat','!=',False),('parent_id','=',False)])
        cuit_partners = []
        for c in partners:
            cuit_partners.append(c.vat)

        for i,line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            if len(lista) > 11:
                #Consultamos si existe el cliente segun el cuit sino seguimos a la siguiente linea para minimizar el proceso
                cuit = lista[3]
                if cuit not in cuit_partners:
                    continue
                publication_date = lista[0]
                effective_date_from = lista[1]
                effective_date_to = lista[2]
                type_contr_insc = lista[4]
                alta_baja = lista[5]
                cambio = lista[6]
                a_per = lista[7]
                a_ret = lista[8]
                nro_grupo_perc = lista[9]
                nro_grupo_ret = lista[10]

                vals.clear()

                # Carga vals
                if cuit != '': 
                    vals['publication_date'] = datetime.strptime((publication_date[:2] + '/' + publication_date[2:4] + '/' + publication_date[4:]), '%d/%m/%Y')
                    vals['effective_date_from'] = datetime.strptime((effective_date_from[:2] + '/' + effective_date_from[2:4] + '/' + effective_date_from[4:]), '%d/%m/%Y')
                    vals['effective_date_to'] = datetime.strptime((effective_date_to[:2] + '/' + effective_date_to[2:4] + '/' + effective_date_to[4:]), '%d/%m/%Y')
                    vals['name'] = cuit
                    vals['type_contr_insc'] = type_contr_insc
                    vals['alta_baja'] = alta_baja
                    vals['a_per'] = float(a_per.replace(',','.'))
                    vals['a_ret'] = float(a_ret.replace(',','.'))
                    vals['cambio'] = cambio

                    #Consultamos si el padron ya existe para Percepcion
                    padron_existe = self.env['tucuman.padron'].search([('name','=',cuit),('type_alicuot','=','P')])
                    if len(padron_existe) > 0:
                        padron_existe.sudo().write({
                            'a_per' : vals['a_per'],
                            'a_ret' : 0.00,
                            'publication_date' : vals['publication_date'],
                            'effective_date_from' : vals['effective_date_from'],
                            'effective_date_to' : vals['effective_date_to'],
                            'alta_baja' : vals['alta_baja'],
                            'type_contr_insc' : vals['type_contr_insc']
                        })
                    else:
                        # Creamos el padron de Percepcion
                        vals['type_alicuot'] = 'P'
                        vals['a_per'] = float(a_per.replace(',','.'))
                        vals['a_ret'] = 0.0
                        vals['nro_grupo_perc'] = nro_grupo_perc
                        self.env['tucuman.padron'].sudo().create(vals)

                    #Consultamos si el padron ya existe para Retenciones
                    padron_existe = self.env['tucuman.padron'].search([('name','=',cuit),('type_alicuot','=','R')])
                    if len(padron_existe) > 0:
                        padron_existe.sudo().write({
                            'a_per' : 0.00,
                            'a_ret' : vals['a_ret'],
                            'publication_date' : vals['publication_date'],
                            'effective_date_from' : vals['effective_date_from'],
                            'effective_date_to' : vals['effective_date_to'],
                            'alta_baja' : vals['alta_baja'],
                            'type_contr_insc' : vals['type_contr_insc']
                        })
                    else:
                        # Creamos el padron de Retencion
                        vals['type_alicuot'] = 'R'
                        vals['a_per'] = 0.0
                        vals['a_ret'] = float(a_ret.replace(',','.'))
                        vals['nro_grupo_ret'] = nro_grupo_ret
                        self.env['tucuman.padron'].sudo().create(vals)


                    _procesados += "{} \n".format(cuit)
                
                else:
                    _noprocesados += "{} \n".format(cuit)

            elif len(lista) == 1:
                continue
            else:
                raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}. Se necesitan al menos 12 columnas".format(i, line))
        self.clientes_cargados = _procesados
        self.not_processed_content = _noprocesados
        self.state = 'processed'
    
    @api.depends('padron_file')
    def compute_lineas_archivo(self):
        for rec in self:
            if rec.padron_file != False:
                rec.file_content_tmp = base64.decodebytes(rec.padron_file)
                lines = rec.file_content_tmp.split('\n')
                for i,line in enumerate(lines):
                    rec.lineas_archivo += 1


            else:
                rec.lineas_archivo = 0
        pass

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
