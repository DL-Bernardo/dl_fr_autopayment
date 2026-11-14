# Angola Factura/Recibo Automatic Payment & Reconciliation (`dl_fr_autopayment`)

Automates the entire lifecycle of Angola **Factura-Recibo (FR)** documents and their **Credit Note (NC)** reversals in Odoo **16.0, 17.0, 18.0, 19.0, and 20.0** (Community & Enterprise).

## Key Features (English)

1. **Automated FR Sales Journal Provisioning (`_post_init_hook`)**:
   - Automatically provisions and configures the `FR` (*Fatura-Recibo*) sales journal for each company with `is_fr_journal = True`, `saft_inv_type = 'FR'`, and a default Bank/Cash payment journal (`default_fr_payment_journal_id`).
2. **Mandatory Payment Method Control (`fr_payment_journal_id`)**:
   - Displays and requires the **Forma de Pagamento** (Bank or Cash journal) on customer invoices issued in an `FR` journal (excluding POS invoices where payment is handled by the POS session).
   - Prevents confirming an `FR` invoice with zero or negative total.
3. **1-Click Automatic Payment & Receivable Reconciliation**:
   - Upon confirming an `FR` invoice (`action_post`), automatically creates and posts an inbound `account.payment` on the selected Bank/Cash journal, reconciles the receivable lines (`asset_receivable`), and marks the invoice as **Paid**.
4. **Smart Credit Note (`NC`) Automatic Refund & Reversal**:
   - When a Credit Note (`out_refund`) is confirmed against a paid `FR` invoice, automatically creates and reconciles the outbound refund payment and updates the original `FR` invoice status to **Reversed**.
5. **Standalone & AGT Ecosystem Ready**:
   - Depends only on `account` (works standalone on any Odoo installation) while preserving native integration with `dl_certification_ao`, `dl_layouts_ao`, and `l10n_ao_fe` (`skip_fe_agt=True`, `is_fr_payment=True`).

---

## Funcionalidades Principais (Portugues)

1. **Configuracao Automatica do Diario FR (`_post_init_hook`)**:
   - Cria ou atualiza automaticamente o diario de vendas `FR` (*Fatura-Recibo*) com a flag `is_fr_journal = True` e a **Forma de Pagamento Padrao (FR)**.
2. **Controlo Obrigatorio da Forma de Pagamento (`fr_payment_journal_id`)**:
   - Apresenta e torna obrigatorio o campo **Forma de Pagamento** (Banco ou Caixa) nas Faturas-Recibo (`FR`), impedindo a validacao de documentos sem forma de pagamento ou com valor zero.
3. **Liquidacao e Reconciliacao Automatica Imediata**:
   - Ao confirmar uma Fatura-Recibo (`FR`), gera e publica automaticamente o pagamento (`account.payment`) e reconcilia a conta de clientes, passando a fatura imediatamente para o estado **Pago**.
4. **Estorno Automatico em Notas de Credito (`NC`)**:
   - Ao confirmar uma Nota de Credito (`out_refund`) referente a uma `FR` paga, gera automaticamente o pagamento de reembolso, reconcilia a Nota de Credito e atualiza o estado da `FR` de origem para **Estornado (`reversed`)**.

## Credits

- **Author:** DIGITALUB, LDA (InvoiceOne Suite)
- **Website:** https://digitalub.ao
- **License:** LGPL-3
