{
    'name': 'FR Auto Payment',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Pagamentos automáticos para Facturas/Recibo (FR)',
    'depends': ['account'],
    'data': [
        'views/account_journal_view.xml',
        'views/account_move_view.xml',
    ],
    'installable': True,
    'application': False,
}