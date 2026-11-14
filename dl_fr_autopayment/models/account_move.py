# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    fr_payment_journal_id = fields.Many2one(
        "account.journal",
        string="Forma de Pagamento",
        domain="[('type', 'in', ('bank', 'cash')), ('company_id', '=', company_id)]",
        copy=False,
        help="Seleciona o diário de Banco ou Caixa utilizado para liquidar imediatamente a Fatura-Recibo (FR).",
    )
    journal_code = fields.Char(
        related="journal_id.code",
        string="Código do Diário",
        store=False,
        readonly=True,
    )
    is_fr_journal = fields.Boolean(
        string="É Fatura-Recibo (FR)",
        compute="_compute_is_fr_journal",
        store=True,
        readonly=True,
    )
    is_pos_invoice = fields.Boolean(
        string="É Fatura POS",
        default=False,
        copy=False,
        help="Indica se a fatura foi originada pelo Ponto de Venda (POS), onde o pagamento já é gerido pela sessão POS.",
    )
    fr_auto_payment_id = fields.Many2one(
        "account.payment",
        string="Pagamento Automático (FR)",
        readonly=True,
        copy=False,
        help="Registo do pagamento gerado e reconciliado automaticamente para esta Fatura-Recibo.",
    )

    @api.depends("journal_id", "journal_id.code", "journal_id.is_fr_journal")
    def _compute_is_fr_journal(self):
        for move in self:
            code_upper = (move.journal_id.code or "").strip().upper()
            saft_type = getattr(move.journal_id, "saft_inv_type", False)
            move.is_fr_journal = bool(
                move.journal_id
                and move.journal_id.type == "sale"
                and (move.journal_id.is_fr_journal or code_upper == "FR" or saft_type == "FR")
            )

    def _compute_payment_state(self):
        res = super()._compute_payment_state()
        for move in self:
            reversals = (
                getattr(move, "reversal_move_ids", False)
                or getattr(move, "reversal_move_id", self.env["account.move"])
            )
            if (
                move.move_type == "out_invoice"
                and move.state == "posted"
                and move.is_fr_journal
                and move.currency_id.is_zero(move.amount_residual)
                and reversals.filtered(
                    lambda r: r.state == "posted" and r.currency_id.is_zero(r.amount_residual)
                )
            ):
                move.payment_state = "reversed"
        return res

    @api.onchange("journal_id", "move_type")
    def _onchange_journal_id_set_default_fr_payment(self):
        for move in self:
            if move.move_type == "out_invoice" and move.is_fr_journal:
                if not move.fr_payment_journal_id and move.journal_id.default_fr_payment_journal_id:
                    move.fr_payment_journal_id = move.journal_id.default_fr_payment_journal_id
            elif move.move_type == "out_invoice" and not move.is_fr_journal:
                move.fr_payment_journal_id = False

    @api.model_create_multi
    def create(self, vals_list):
        Journal = self.env["account.journal"]
        for vals in vals_list:
            if vals.get("move_type") == "out_invoice" and not vals.get("fr_payment_journal_id") and vals.get("journal_id"):
                journal = Journal.browse(vals["journal_id"])
                code_upper = (journal.code or "").strip().upper()
                if (journal.is_fr_journal or code_upper == "FR") and journal.default_fr_payment_journal_id:
                    vals["fr_payment_journal_id"] = journal.default_fr_payment_journal_id.id
        return super().create(vals_list)

    @api.constrains("journal_id", "fr_payment_journal_id", "is_pos_invoice", "move_type")
    def _check_fr_payment_required(self):
        """Nas Faturas-Recibo (FR) manuais/normais, a Forma de Pagamento é obrigatória."""
        for move in self:
            if (
                move.move_type == "out_invoice"
                and move.is_fr_journal
                and not move.is_pos_invoice
                and not move.fr_payment_journal_id
            ):
                if move.journal_id.default_fr_payment_journal_id:
                    move.fr_payment_journal_id = move.journal_id.default_fr_payment_journal_id
                else:
                    raise ValidationError(
                        _("É obrigatório selecionar a Forma de Pagamento nas Faturas-Recibo (FR).")
                    )

    def _get_liquidity_account_for_journal(self, payment_journal):
        account = payment_journal.default_account_id
        if not account:
            Account = self.env["account.account"].sudo()
            domain = [("account_type", "in", ("asset_cash", "asset_current"))]
            if "company_id" in Account._fields:
                domain.append(("company_id", "=", self.company_id.id))
            account = Account.search(domain, limit=1)
            if account:
                payment_journal.sudo().default_account_id = account.id
        return account

    def _get_or_ensure_payment_outstanding_account(self, payment, payment_journal, payment_type):
        """In Odoo 18+, account.payment only creates a journal entry (move_id) when
        outstanding_account_id is set. Ensure a valid liquidity account is available.
        """
        Payment = self.env["account.payment"]
        if "outstanding_account_id" not in Payment._fields:
            return
        if payment.outstanding_account_id:
            return
        account = self._get_liquidity_account_for_journal(payment_journal)
        if not account and hasattr(payment, "_get_outstanding_account"):
            try:
                account = payment._get_outstanding_account(payment_type)
            except Exception:
                account = False
        if account:
            payment.outstanding_account_id = account.id

    def _create_and_reconcile_fr_payment(self, payment_journal, payment_type, amount, memo_ref):
        """Create, post, and return an account.payment compatible with Odoo 16.0 through 20.0."""
        self.ensure_one()
        Payment = self.env["account.payment"]

        if payment_type == "inbound":
            method_lines = payment_journal.inbound_payment_method_line_ids
        else:
            method_lines = payment_journal.outbound_payment_method_line_ids
        payment_method_line = method_lines[:1]
        if not payment_method_line:
            raise UserError(
                _("O diário de pagamento '%s' não possui método de pagamento (%s) configurado.")
                % (payment_journal.display_name, payment_type)
            )

        # Ensure payment_method_line has a payment_account_id for Odoo 16-20
        liq_account = self._get_liquidity_account_for_journal(payment_journal)
        if "payment_account_id" in payment_method_line._fields and not payment_method_line.payment_account_id and liq_account:
            payment_method_line.sudo().payment_account_id = liq_account.id

        # Find the invoice's receivable/payable line to pass destination_account_id
        inv_rec_line = self.line_ids.filtered(
            lambda l: l.account_id.account_type in ("asset_receivable", "liability_payable")
        )[:1]

        payment_vals = {
            "payment_type": payment_type,
            "partner_type": "customer",
            "partner_id": self.partner_id.id,
            "amount": amount,
            "currency_id": self.currency_id.id,
            "date": self.invoice_date or fields.Date.context_today(self),
            "journal_id": payment_journal.id,
            "payment_method_line_id": payment_method_line.id,
        }
        if inv_rec_line and "destination_account_id" in Payment._fields:
            payment_vals["destination_account_id"] = inv_rec_line.account_id.id

        if "memo" in Payment._fields:
            payment_vals["memo"] = memo_ref
        elif "ref" in Payment._fields:
            payment_vals["ref"] = memo_ref

        if "l10n_ao_fe_serie_id" in Payment._fields:
            payment_vals["l10n_ao_fe_serie_id"] = False
        if "fe_status" in Payment._fields:
            payment_vals["fe_status"] = "not_sent"

        ctx_Payment = Payment.with_context(
            skip_fe_agt=True,
            is_fr_payment=True,
            skip_account_move_synchronization=True,
            skip_invoice_sync=True,
        )
        payment = ctx_Payment.create(payment_vals)
        self._get_or_ensure_payment_outstanding_account(payment, payment_journal, payment_type)
        payment.with_context(
            skip_fe_agt=True,
            is_fr_payment=True,
            skip_sale_auto_invoice_send=True,
        ).action_post()

        # In Odoo 18+, ensure journal entry move_id is generated and posted
        if not payment.move_id and hasattr(payment, "_generate_journal_entry"):
            self._get_or_ensure_payment_outstanding_account(payment, payment_journal, payment_type)
            payment._generate_journal_entry()
            if payment.move_id and payment.move_id.state == "draft":
                payment.move_id.action_post()

        payment_move_lines = (
            payment.move_id.line_ids
            if payment.move_id
            else getattr(payment, "line_ids", self.env["account.move.line"])
        )
        lines_to_reconcile = (payment_move_lines + self.line_ids).filtered(
            lambda l: l.account_id.account_type in ("asset_receivable", "liability_payable")
            and not l.reconciled
            and l.parent_state == "posted"
        )
        for account in lines_to_reconcile.account_id:
            acc_lines = lines_to_reconcile.filtered(lambda l, a=account: l.account_id == a and not l.reconciled)
            if len(acc_lines) >= 2:
                acc_lines.reconcile()

        if "matched_payment_ids" in self._fields:
            self.matched_payment_ids = [(4, payment.id)]
        self.fr_auto_payment_id = payment.id
        return payment

    def action_post(self):
        # 1. Validate FR requirements before posting
        for move in self:
            if move.move_type == "out_invoice" and move.is_fr_journal and not move.is_pos_invoice:
                if not move.fr_payment_journal_id and move.journal_id.default_fr_payment_journal_id:
                    move.fr_payment_journal_id = move.journal_id.default_fr_payment_journal_id
                if move.amount_total <= 0:
                    raise UserError(
                        _("Não é permitido validar uma Fatura-Recibo (FR) sem valor ou com total igual a zero.")
                    )
                if not move.fr_payment_journal_id:
                    raise UserError(
                        _("Deve selecionar a Forma de Pagamento para validar uma Fatura-Recibo (FR).")
                    )

        # 2. Post the invoice / credit note via standard Odoo flow
        res = super().action_post()

        # 3. Execute automatic payment & reconciliation for FR and NC
        for move in self:
            # --- CASE 1: Customer Invoice-Receipt (FR) ---
            if (
                move.move_type == "out_invoice"
                and move.is_fr_journal
                and not move.is_pos_invoice
                and move.fr_payment_journal_id
                and move.amount_residual > 0
            ):
                _logger.info(
                    "dl_fr_autopayment: Creating automatic inbound payment for FR %s via journal %s",
                    move.name,
                    move.fr_payment_journal_id.display_name,
                )
                move._create_and_reconcile_fr_payment(
                    payment_journal=move.fr_payment_journal_id,
                    payment_type="inbound",
                    amount=move.amount_residual,
                    memo_ref=move.name,
                )

            # --- CASE 2: Customer Credit Note (NC) ---
            elif move.move_type == "out_refund":
                origin = move.reversed_entry_id or getattr(move, "invoice_origin_id", False)
                if origin and origin.state == "posted":
                    # Step A: Reconcile open receivable lines between origin invoice and NC
                    rec_lines = (origin.line_ids + move.line_ids).filtered(
                        lambda l: l.account_id.account_type == "asset_receivable"
                        and not l.reconciled
                        and l.parent_state == "posted"
                    )
                    if len(rec_lines) >= 2:
                        rec_lines.reconcile()

                    # Step B: If NC still has residual (e.g. origin FR was already paid), issue outbound refund payment
                    if move.amount_residual > 0:
                        payment_journal = move.fr_payment_journal_id or origin.fr_payment_journal_id
                        if payment_journal:
                            _logger.info(
                                "dl_fr_autopayment: Creating automatic outbound refund payment for NC %s via journal %s",
                                move.name,
                                payment_journal.display_name,
                            )
                            move._create_and_reconcile_fr_payment(
                                payment_journal=payment_journal,
                                payment_type="outbound",
                                amount=move.amount_residual,
                                memo_ref=_("Reembolso %s (Ref: %s)") % (move.name, origin.name),
                            )

                    # Step C: Update origin FR payment_state to 'reversed' when fully credited
                    if origin.is_fr_journal and origin.currency_id.is_zero(origin.amount_residual):
                        self.env.flush_all()
                        origin.payment_state = "reversed"

        return res

    def _get_starting_sequence(self):
        starting_sequence = super()._get_starting_sequence()
        if self.is_fr_journal and starting_sequence and starting_sequence.count("/") > 1:
            if self.move_type == "out_refund" and starting_sequence.startswith("RFR/"):
                starting_sequence = "NC " + starting_sequence[4:]
            else:
                starting_sequence = starting_sequence.replace("/", " ", 1)
        return starting_sequence

    def action_open_fr_auto_payment(self):
        self.ensure_one()
        if not self.fr_auto_payment_id:
            return False
        return {
            "name": _("Pagamento Automático (FR)"),
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            "view_mode": "form",
            "res_id": self.fr_auto_payment_id.id,
        }
