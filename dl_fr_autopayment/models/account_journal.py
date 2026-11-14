# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    is_fr_journal = fields.Boolean(
        string="Diário de Fatura-Recibo (FR)",
        compute="_compute_is_fr_journal",
        store=True,
        readonly=False,
        help="Marque esta opção se este diário for para Faturas-Recibo (FR). "
             "Ao validar uma fatura neste diário, o pagamento e a reconciliação "
             "serão criados automaticamente.",
    )
    default_fr_payment_journal_id = fields.Many2one(
        "account.journal",
        string="Forma de Pagamento Padrão (FR)",
        domain="[('type', 'in', ('bank', 'cash'))]",
        check_company=True,
        help="Diário de Banco ou Caixa sugerido por defeito ao emitir uma Fatura-Recibo (FR).",
    )

    @api.depends("code", "type")
    def _compute_is_fr_journal(self):
        for journal in self:
            code_upper = (journal.code or "").strip().upper()
            saft_type = getattr(journal, "saft_inv_type", False)
            if journal.type == "sale" and (code_upper == "FR" or saft_type == "FR"):
                journal.is_fr_journal = True
            elif not journal.is_fr_journal:
                journal.is_fr_journal = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            code_upper = (vals.get("code") or "").strip().upper()
            if vals.get("type") == "sale" and (code_upper == "FR" or vals.get("is_fr_journal") or vals.get("saft_inv_type") == "FR"):
                vals["is_fr_journal"] = True
                if "saft_inv_type" in self._fields and not vals.get("saft_inv_type"):
                    vals["saft_inv_type"] = "FR"
                if "paga_me" in self._fields:
                    vals["paga_me"] = False
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "is_fr_journal" in vals or "code" in vals:
            for journal in self:
                if journal.is_fr_journal and "paga_me" in self._fields and getattr(journal, "paga_me", False):
                    super(AccountJournal, journal).write({"paga_me": False})
        return res
