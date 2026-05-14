"""Conversas-exemplo PT-BR para few-shot (seeds)."""

# Exemplos de conversas reais (few-shot) para guiar a geração do LLM
# Cada tipo de agente tem 2-3 exemplos para estabilizar a qualidade

SEED_SUPORTE_VOZ = """Cliente: Olá, bom dia. Eu estava tentando acessar minha conta e recebi um erro.
Agente: Oi! Tudo bem? Desculpa pelos problemas. Qual é o erro que você está vendo?
Cliente: Aparece "Erro 500 - Servidor indisponível". Já tentei fechar o navegador e entrar de novo.
Agente: Entendi. Deixe-me checar aqui. Você está acessando de qual navegador?
Cliente: Estou usando o Chrome na versão mais recente.
Agente: Perfeito. Vou resetar sua sessão no servidor. Tenta acessar de novo e avisa se funciona.
Cliente: Ótimo! Agora funcionou. Obrigado pela ajuda.
Agente: Que bom! Qualquer outra coisa, é só chamar. Tenha um ótimo dia!"""

SEED_SUPORTE_WHATSAPP = """Cliente: oi, qual é o prazo de entrega do meu pedido? ja faz 2 semanas
Agente: Oi! 👋 Deixe-me conferir seu pedido. Qual é o número?
Cliente: é o pedido 78941
Agente: Achei aqui! Este pedido foi despachado dia 15, já deve estar na sua região. Quer o código de rastreamento?
Cliente: sim, preciso saber quando chega
Agente: O código é BR5566778899. Com ele você acompanha minuto a minuto. Só de passar na transportadora deve chegar em 2 dias úteis.
Cliente: ok, vou checar. obrigado!
Agente: De nada! Fico no aguardo. 😊"""

SEED_COBRANCA_VOZ = """Cliente: Oi, recebi uma cobrança e achei estranho. Não contratei isso.
Agente: Boa tarde. Deixa eu ajudar. Qual é o valor que aparece na fatura?
Cliente: Aparece 89 reais em uma categoria que chama "Serviço Premium".
Agente: Achei. Você foi automaticamente convertido para Premium quando fez uma compra em fevereiro. Deixa eu checar se você autorizou isso.
Cliente: Não, não autorizo cobranças automáticas não. Quero cancelar.
Agente: Vou cancelar agora mesmo. Qual é seu CPF para confirmar?
Cliente: Meu CPF é xxx.xxx.xxx-xx.
Agente: Confirmado. Seu Premium foi cancelado e vou gerar um boleto de devolução do valor. Você recebe por email em 24 horas.
Cliente: Tá bom, obrigado!"""

SEED_COBRANCA_WHATSAPP = """Cliente: oi, tenho uma divida atrasada e gostaria de negociar o pagamento
Agente: Oi! Bem-vindo ao atendimento de cobranças. Vou ajudar sim. Deixa eu consultar sua conta.
Cliente: meu nome é João Silva
Agente: Qual é seu CPF? Preciso para buscar suas informações.
Cliente: xxx.xxx.xxx-xx
Agente: Achei! Você tem uma dívida de 450 reais vencida há 3 meses. Qual é sua capacidade de pagamento?
Cliente: consigo pagar 150 agora e o resto em 3 parcelas
Agente: Perfeito! Vou criar um acordo com 150 à vista + 3x de 100. Aceita esse plano?
Cliente: sim! quando gero o boleto da primeira parcela?
Agente: Já enviei para seu email! Você recebe em 1 hora. A próxima vence em 30 dias. Tudo bem?
Cliente: sim, obrigado mesmo!"""

SEED_RETENCAO_VOZ = """Cliente: Oi, gostaria de falar sobre cancelar meu plano.
Agente: Oi! Que pena saber isso. Antes de cancelar, posso perguntar o motivo?
Cliente: Achei muito caro para o que eu uso. Eu gasto pouco dados e minutos.
Agente: Entendo perfeitamente. Você sabe que temos um plano mais econômico? Deixa eu ver sua conta.
Cliente: Sim, mas também nenhum desses planos me atrai muito.
Agente: Certo! Que tal eu fazer uma oferta especial? Te dou 30% de desconto nos próximos 3 meses.
Cliente: Uau, 30%? Quanto fica o plano então?
Agente: Seu plano atual está 89 reais. Com desconto fica 62 reais por mês. Topa?
Cliente: Tá bom! Vocês me convenceram. Obrigado!
Agente: Ótimo! Vou ativar o desconto na sua próxima fatura. Fico feliz em continuar te atendendo!"""

SEED_RETENCAO_WHATSAPP = """Cliente: oi, estou pensando em cancelar meu plano porque tou acumulando saldo nao usado
Agente: Oi! Que pena. Mas ótimo que você tem crédito! Você sabia que o saldo não expira?
Cliente: não sabia! e posso usar pra alguma coisa?
Agente: Claro! Vale para chamadas, mensagens, dados, tudo. Seu saldo é de 127 reais. Bastante coisa!
Cliente: ah sério? entao talvez nem cancel. qual é o plano mais barato que vocês tem?
Agente: Temos o plano básico de 29 reais por mês com 2GB de dados. Quer migrar?
Cliente: sim, vou migrar em vez de cancelar então. obrigado!
Agente: Que legal! Já ativo pra você agora. Você vai economizar muito! 🎉"""

# Seeds estruturadas para consulta
SEEDS_AGENTE: dict[str, dict[str, list[str]]] = {
    "suporte": {
        "voz": [SEED_SUPORTE_VOZ],
        "whatsapp": [SEED_SUPORTE_WHATSAPP],
    },
    "cobranca": {
        "voz": [SEED_COBRANCA_VOZ],
        "whatsapp": [SEED_COBRANCA_WHATSAPP],
    },
    "retencao": {
        "voz": [SEED_RETENCAO_VOZ],
        "whatsapp": [SEED_RETENCAO_WHATSAPP],
    },
}
