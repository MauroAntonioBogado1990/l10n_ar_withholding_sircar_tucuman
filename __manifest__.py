{
    'name': 'Export TXT RET/PER AGIP',
    'license': 'AGPL-3',
    'author': 'ADHOC SA, Moldeo Interactive, Exemax, Codize',
    'category': 'Accounting & Finance',
    'data': [
        'views/account_export_agip_view.xml',
        'views/agip_padron.xml',
        'views/import_padron_agip_view.xml',
        'views/res_partner_view.xml',
        'views/account_tax_inherit_view.xml',
        'views/res_company_view.xml',
        'security/ir.model.access.csv',
    ],
    'depends': [
        'base',
        'account',
        'l10n_ar',
        'l10n_ar_withholding',
    ],
    'installable': True,
    'version': '16.0.1.0.0',
}
