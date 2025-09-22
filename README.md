# Módulo FR Auto Payment

Este módulo estende a funcionalidade de faturação do Odoo para automatizar a criação de pagamentos para um tipo específico de documento: a Fatura/Recibo.

## Funcionalidades

*   Adiciona um campo **Forma de Pagamento** ao formulário da fatura.
*   O campo só é visível e obrigatório para faturas cujo diário tenha o **Código Curto** configurado como `FR`.
*   Ao validar uma fatura do tipo 'FR', um pagamento é automaticamente criado e reconciliado, liquidando a fatura de imediato.

## Configuração

Para ativar a funcionalidade de pagamento automático para um diário específico, siga estes passos:

1.  Navegue até **Contabilidade > Configuração > Diários**.
2.  Selecione e edite o diário que pretende usar para as Faturas/Recibo.
3.  No campo **Código Curto**, certifique-se de que o valor é exatamente `FR`.
4.  Guarde as alterações.

A partir deste momento, todas as faturas criadas com este diário terão a funcionalidade de pagamento automático ativa.

## Utilização

1.  Crie uma nova Fatura de Cliente em **Contabilidade > Clientes > Faturas**.
2.  Selecione um **Diário** que esteja configurado com o código `FR`.
3.  O campo **Forma de Pagamento** aparecerá no formulário. Selecione o diário de pagamento pretendido (ex: um diário de Banco ou Caixa).
4.  Preencha os restantes dados da fatura (cliente, linhas de produto, etc.).
5.  Clique em **Confirmar**.

Após a confirmação, o pagamento será criado e reconciliado automaticamente com a fatura.

## Créditos

### Autor

*   [O seu nome ou nome da empresa aqui]

### Desenvolvido por

*   Jules (Assistente de Engenharia de Software)
