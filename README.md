Módulo FR Auto Payment
Este módulo estende a funcionalidade de faturação do Odoo para automatizar a criação de pagamentos para um tipo específico de documento: a Fatura/Recibo.

Funcionalidades
Adiciona um campo Forma de Pagamento ao formulário da fatura.
O campo só é visível e obrigatório para faturas cujo diário tenha o Código Curto configurado como FR.
Ao validar uma fatura do tipo 'FR', um pagamento é automaticamente criado e reconciliado, liquidando a fatura de imediato.
Configuração
Para ativar a funcionalidade de pagamento automático para um diário específico, siga estes passos:

Navegue até Contabilidade > Configuração > Diários.
Selecione e edite o diário que pretende usar para as Faturas/Recibo.
No campo Código Curto, certifique-se de que o valor é exatamente FR.
Guarde as alterações.
A partir deste momento, todas as faturas criadas com este diário terão a funcionalidade de pagamento automático ativa.

Utilização
Crie uma nova Fatura de Cliente em Contabilidade > Clientes > Faturas.
Selecione um Diário que esteja configurado com o código FR.
O campo Forma de Pagamento aparecerá no formulário. Selecione o diário de pagamento pretendido (ex: um diário de Banco ou Caixa).
Preencha os restantes dados da fatura (cliente, linhas de produto, etc.).
Clique em Confirmar.
Após a confirmação, o pagamento será criado e reconciliado automaticamente com a fatura.

Créditos
Desenvolvido por
DIGITALUB