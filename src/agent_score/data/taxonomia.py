"""Taxonomia e constantes para geração de conversas."""

from datetime import date, datetime, timedelta, timezone
from typing import Final

# Janela temporal fixa (determinismo do fixture)
JANELA_INICIO: Final[date] = date(2026, 4, 30)  # Dia 1
JANELA_FIM: Final[date] = date(2026, 5, 13)    # Dia 14
DIAS_TOTAIS: Final[int] = (JANELA_FIM - JANELA_INICIO).days + 1

# Dias 1-7 = baseline saudável; dias 8-14 = janela degradada
DIA_INICIO_DEGRADADA: Final[int] = 8
DATA_INICIO_DEGRADADA: Final[date] = JANELA_INICIO + timedelta(days=DIA_INICIO_DEGRADADA - 1)

# Intenções por tipo de agente
INTENCOES: Final[dict[str, list[str]]] = {
    "suporte": [
        "duvida_produto",
        "problema_tecnico",
        "status_pedido",
        "reclamacao",
    ],
    "cobranca": [
        "negociacao_divida",
        "segunda_via_boleto",
        "contestacao_cobranca",
        "promessa_pagamento",
    ],
    "retencao": [
        "pedido_cancelamento",
        "downgrade_plano",
        "insatisfacao_preco",
        "oferta_retencao",
    ],
}

# Distribuição planejada de conversas
# Segmento-herói: cobranca/whatsapp/negociacao_divida
# ~25 saudáveis (dias 1-7) + ~25 degradadas (dias 8-14)
SEGMENTO_HEROI: Final[tuple[str, str, str]] = ("cobranca", "whatsapp", "negociacao_divida")
CONVERSAS_HEROI_SAUDAVEIS: Final[int] = 25
CONVERSAS_HEROI_DEGRADADAS: Final[int] = 25

# Segmento fino: retencao/voz/insatisfacao_preco
# ~8 saudáveis + ~12 degradadas (leve), <20 na janela
SEGMENTO_FINO: Final[tuple[str, str, str]] = ("retencao", "voz", "insatisfacao_preco")
CONVERSAS_FINO_SAUDAVEIS: Final[int] = 8
CONVERSAS_FINO_DEGRADADAS: Final[int] = 12

# Alvo total de conversas
TOTAL_CONVERSAS_ALVO: Final[int] = 180

# Conversas no "restante" (todos os demais segmentos, saudáveis)
CONVERSAS_RESTANTE: Final[int] = (
    TOTAL_CONVERSAS_ALVO
    - (CONVERSAS_HEROI_SAUDAVEIS + CONVERSAS_HEROI_DEGRADADAS)
    - (CONVERSAS_FINO_SAUDAVEIS + CONVERSAS_FINO_DEGRADADAS)
)

# Semente aleatória para determinismo
SEMENTE_ALEATORIA: Final[int] = 42

# Padrão de falha plantado no segmento-herói
# Dias 8-14: agente de Cobrança não coleta CPF inline
# → quebra de contexto, repetição, não-resolução
PADRAO_FALHA_HEROI: Final[str] = (
    "agente de cobrança não coleta CPF inline "
    "durante a conversa inicial → quebra de contexto "
    "e necessidade de repetição das informações, "
    "reduzindo a eficiência e resolução"
)


def datetime_utc(ano: int, mes: int, dia: int, hora: int = 12, minuto: int = 0) -> datetime:
    """Helper para criar datetimes UTC timezone-aware."""
    return datetime(ano, mes, dia, hora, minuto, 0, tzinfo=timezone.utc)


# Horários comerciais para timestamps dentro do dia
HORARIOS_COMERCIAIS: Final[list[int]] = list(range(8, 19))  # 08:00 a 18:00
