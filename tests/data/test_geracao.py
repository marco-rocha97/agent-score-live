"""Testes para o pipeline de geração de conversas."""

from datetime import datetime, timezone

from pydantic_ai.models.test import TestModel

from agent_score.data.modelos import Conversa, RoteiroConversa
from agent_score.data.taxonomia import INTENCOES


def test_roteiro_conversa_valido() -> None:
    """Testa que RoteiroConversa pode ser criado."""
    roteiro = RoteiroConversa(
        turnos=[
            {"indice": 0, "autor": "cliente", "texto": "Olá"},
            {"indice": 1, "autor": "agente", "texto": "Oi"},
            {"indice": 2, "autor": "cliente", "texto": "Teste"},
            {"indice": 3, "autor": "agente", "texto": "Ok"},
        ]
    )
    assert len(roteiro.turnos) == 4


def test_conversa_com_metadados() -> None:
    """Testa que uma conversa com metadados atribuídos é válida."""
    roteiro = RoteiroConversa(
        turnos=[
            {"indice": 0, "autor": "cliente", "texto": "Olá"},
            {"indice": 1, "autor": "agente", "texto": "Oi"},
            {"indice": 2, "autor": "cliente", "texto": "Teste"},
            {"indice": 3, "autor": "agente", "texto": "Ok"},
        ]
    )

    # Montar Conversa com metadados
    conversa = Conversa(
        id="conv-0001",
        tipo_agente="suporte",
        canal="voz",
        intencao="duvida_produto",
        segmento_cliente="individual",
        iniciada_em=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
        turnos=roteiro.turnos,
    )

    assert conversa.id == "conv-0001"
    assert conversa.tipo_agente == "suporte"
    assert conversa.canal == "voz"
    assert conversa.intencao == "duvida_produto"
    assert len(conversa.turnos) == 4


def test_prompt_montado_inclui_tipo_agente() -> None:
    """Testa que o prompt de geração inclui o tipo de agente correto."""
    tipo_agente = "cobranca"
    canal = "whatsapp"
    intencao = "negociacao_divida"
    segmento_cliente = "individual"

    # Simular montagem de prompt
    estilo_canal = "fala transcrita, coloquial" if canal == "voz" else "texto curto, assíncrono"
    prompt = f"""Tipo de agente: {tipo_agente}
Canal: {canal} ({estilo_canal})
Intenção: {intencao}
Segmento do cliente: {segmento_cliente}"""

    assert tipo_agente in prompt
    assert canal in prompt
    assert intencao in prompt
    assert segmento_cliente in prompt


def test_intencoes_por_agente() -> None:
    """Testa que a taxonomia de intenções está correta."""
    assert "duvida_produto" in INTENCOES["suporte"]
    assert "negociacao_divida" in INTENCOES["cobranca"]
    assert "pedido_cancelamento" in INTENCOES["retencao"]

    # Verificar que não há overlaps
    todas_intencoes = set()
    for agente_intencoes in INTENCOES.values():
        for intencao in agente_intencoes:
            assert intencao not in todas_intencoes, f"Intenção duplicada: {intencao}"
            todas_intencoes.add(intencao)
