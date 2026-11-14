# -*- coding: utf-8 -*-
{
    'name': 'Angola Factura/Recibo Automatic Payment & Reconciliation (FR)',
    'version': '18.0.1.1.0',
    'category': 'Accounting/Localizations',
    'summary': 'Instant Automatic Payment Creation, Receivable Reconciliation & Credit Note Reversal for Invoice-Receipts (FR)',
    'description': """
Angola Factura/Recibo Automatic Payment & Reconciliation (dl_fr_autopayment)
============================================================================

Automate the entire lifecycle of Angola **Factura-Recibo (FR)** documents in Odoo with zero manual payment steps:

Key Features
------------
* **Dedicated FR Sales Journal Configuration**: Automatically provisions the ``FR`` (Fatura-Recibo) journal with configurable ``is_fr_journal`` flag and default Bank/Cash payment method.
* **Mandatory Payment Method Enforcement**: Displays and validates the ``Forma de Pagamento`` (Bank or Cash journal) directly on the customer invoice form whenever an ``FR`` journal is selected.
* **One-Click Confirmation, Payment & Reconciliation**: Confirming an ``FR`` invoice automatically creates the inbound ``account.payment``, posts the journal entry, and reconciles the receivable lines so the invoice immediately transitions to **Paid**.
* **Credit Note (NC) Automatic Refund & Reversal**: Confirming a Credit Note (``out_refund``) against a paid ``FR`` invoice automatically generates the outbound refund payment, reconciles the credit note, and marks the original ``FR`` invoice as **Reversed**.
* **POS & AGT Electronic Invoicing Ready**: Native compatibility with Point of Sale (``is_pos_invoice``) and Angola AGT SAF-T / Electronic Invoicing (``l10n_ao_fe`` & ``dl_certification_ao``).
    """,
    'author': 'DIGITALUB, LDA',
    'website': 'https://digitalub.ao',
    'support': 'info@digitalub.ao',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'views/account_journal_view.xml',
        'views/account_move_view.xml',
    ],
    'images': [
        'static/description/banner.png',
        'static/description/icon.png',
    ],
    'post_init_hook': '_post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 0.0,
    'currency': 'EUR',
}
