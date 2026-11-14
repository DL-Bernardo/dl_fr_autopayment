# -*- coding: utf-8 -*-
import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def _post_init_hook(*args):
    """Ensure every company has a configured FR (Fatura-Recibo) sales journal
    and at least one Bank/Cash payment journal ready for automatic reconciliation.
    Compatible with Odoo 16 (cr, registry) and Odoo 17-20 (env).
    """
    if len(args) == 1:
        env = args[0]
    else:
        cr, _registry = args
        env = api.Environment(cr, SUPERUSER_ID, {})

    Journal = env["account.journal"].sudo()
    Account = env["account.account"].sudo()
    companies = env["res.company"].sudo().search([])

    for company in companies:
        with env.cr.savepoint():
            try:
                # 1. Find or create a default Cash/Bank payment journal for FR
                pay_journal = Journal.search([
                    ("company_id", "=", company.id),
                    ("type", "in", ("cash", "bank")),
                ], limit=1)
                if not pay_journal:
                    cash_vals = {
                        "name": "Numerário / Caixa",
                        "code": "CX1",
                        "type": "cash",
                        "company_id": company.id,
                    }
                    pay_journal = Journal.with_company(company).create(cash_vals)

                # Ensure default_account_id and payment method line accounts are set on pay_journal
                liq_acc = pay_journal.default_account_id
                if not liq_acc:
                    liq_acc = Account.search(
                        [("account_type", "in", ("asset_cash", "asset_current")), ("company_id", "=", company.id)]
                        if "company_id" in Account._fields
                        else [("account_type", "in", ("asset_cash", "asset_current"))],
                        limit=1,
                    )
                    if liq_acc:
                        pay_journal.default_account_id = liq_acc.id
                if liq_acc:
                    for pml in (pay_journal.inbound_payment_method_line_ids | pay_journal.outbound_payment_method_line_ids):
                        if "payment_account_id" in pml._fields and not pml.payment_account_id:
                            pml.payment_account_id = liq_acc.id

                # 2. Find or create the FR (Fatura-Recibo) Sales Journal
                fr_journal = Journal.search([
                    ("company_id", "=", company.id),
                    ("type", "=", "sale"),
                    "|",
                    ("code", "=", "FR"),
                    ("is_fr_journal", "=", True),
                ], limit=1)

                if fr_journal:
                    update_vals = {"is_fr_journal": True}
                    if not fr_journal.default_fr_payment_journal_id and pay_journal:
                        update_vals["default_fr_payment_journal_id"] = pay_journal.id
                    if "saft_inv_type" in Journal._fields and getattr(fr_journal, "saft_inv_type", False) != "FR":
                        update_vals["saft_inv_type"] = "FR"
                    if "paga_me" in Journal._fields and getattr(fr_journal, "paga_me", False):
                        update_vals["paga_me"] = False
                    fr_journal.write(update_vals)
                else:
                    income_acc = Account.search(
                        [("account_type", "=", "income"), ("company_id", "=", company.id)]
                        if "company_id" in Account._fields
                        else [("account_type", "=", "income")],
                        limit=1,
                    )
                    fr_vals = {
                        "name": "Fatura-Recibo",
                        "code": "FR",
                        "type": "sale",
                        "company_id": company.id,
                        "is_fr_journal": True,
                        "default_fr_payment_journal_id": pay_journal.id if pay_journal else False,
                    }
                    if income_acc:
                        fr_vals["default_account_id"] = income_acc.id
                    if "saft_inv_type" in Journal._fields:
                        fr_vals["saft_inv_type"] = "FR"
                    if "paga_me" in Journal._fields:
                        fr_vals["paga_me"] = False
                    if "refund_sequence" in Journal._fields:
                        fr_vals["refund_sequence"] = True
                    Journal.with_company(company).create(fr_vals)
            except Exception as exc:
                _logger.warning("dl_fr_autopayment: Could not initialize FR journal for company %s: %s", company.name, exc)
