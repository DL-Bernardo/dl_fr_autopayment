from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_fr_journal = fields.Boolean(
        string="Diário de Fatura/Recibo",
        help="Marque esta opção se este diário for para Faturas/Recibo. "
             "Isto irá despoletar a criação automática de pagamentos."
    )
