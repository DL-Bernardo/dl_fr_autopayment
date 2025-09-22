from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"

    # Campo Forma de Pagamento (liga a diários do tipo banco ou caixa)
    fr_payment_journal_id = fields.Many2one(
        "account.journal",
        string="Forma de Pagamento",
        domain="[('type', 'in', ('bank', 'cash'))]",
        help="Seleciona a forma de pagamento usada no caso de Factura/Recibo."
    )

    is_fr_journal = fields.Boolean(
        related="journal_id.is_fr_journal",
        store=True,
        readonly=True
    )

    @api.constrains("journal_id", "fr_payment_journal_id")
    def _check_fr_payment_required(self):
        """
        Garante que nos diários de Fatura/Recibo a Forma de Pagamento é obrigatória.
        """
        for move in self:
            if move.is_fr_journal and not move.fr_payment_journal_id:
                raise ValidationError(_("É obrigatório selecionar a Forma de Pagamento nas Facturas/Recibo."))

    def action_post(self):
        """
        Ao validar uma Fatura/Recibo, cria um pagamento automático.
        """
        res = super(AccountMove, self).action_post()
        for move in self:
            if move.is_fr_journal and move.fr_payment_journal_id:
                # Criar pagamento automático
                payment_vals = {
                    "payment_type": "inbound",
                    "partner_type": "customer",
                    "partner_id": move.partner_id.id,
                    "amount": move.amount_residual,
                    "currency_id": move.currency_id.id,
                    "journal_id": move.fr_payment_journal_id.id,
                    "ref": move.name,
                    "date": move.invoice_date or fields.Date.context_today(self),
                }
                payment = self.env["account.payment"].create(payment_vals)
                payment.action_post()

                # Reconciliar automaticamente
                (payment.line_ids + move.line_ids).filtered(
                    lambda l: l.account_id == move.partner_id.property_account_receivable_id
                ).reconcile()
        return res