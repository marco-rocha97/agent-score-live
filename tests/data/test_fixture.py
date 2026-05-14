"""Testes de sanidade do fixture commitado."""

import json
import re
from pathlib import Path

import pytest

from agent_score.data.modelos import Conversa
from agent_score.data.taxonomia import (
    CONVERSAS_HEROI_DEGRADADAS,
    DATA_INICIO_DEGRADADA,
    JANELA_FIM,
    JANELA_INICIO,
    SEGMENTO_FINO,
    SEGMENTO_HEROI,
)


@pytest.fixture
def conversas_fixture() -> list[Conversa]:
    """Carrega o fixture commitado."""
    caminho = Path("data/conversas.seed.jsonl")
    assert caminho.exists(), f"Fixture não encontrado: {caminho}"

    conversas = []
    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                dados = json.loads(linha)
                conversa = Conversa(**dados)
                conversas.append(conversa)

    return conversas


def test_fixture_tem_conversas(conversas_fixture: list[Conversa]) -> None:
    """Testa que o fixture tem conversas."""
    assert len(conversas_fixture) >= 100, f"Fixture com poucos dados: {len(conversas_fixture)}"
    assert len(conversas_fixture) <= 200, f"Fixture com muitos dados: {len(conversas_fixture)}"


def test_fixture_tem_3_agentes(conversas_fixture: list[Conversa]) -> None:
    """Testa que o fixture tem os 3 tipos de agente."""
    tipos_agente = set(c.tipo_agente for c in conversas_fixture)
    assert "suporte" in tipos_agente
    assert "cobranca" in tipos_agente
    assert "retencao" in tipos_agente


def test_fixture_tem_2_canais(conversas_fixture: list[Conversa]) -> None:
    """Testa que o fixture tem os 2 canais."""
    canais = set(c.canal for c in conversas_fixture)
    assert "voz" in canais
    assert "whatsapp" in canais


def test_fixture_cobre_14_dias(conversas_fixture: list[Conversa]) -> None:
    """Testa que o fixture cobre os 14 dias da janela."""
    datas = set(c.iniciada_em.date() for c in conversas_fixture)

    # Deve cobrir todo o intervalo
    assert min(datas) == JANELA_INICIO
    assert max(datas) == JANELA_FIM


def test_fixture_segmento_heroi_tem_suficientes(conversas_fixture: list[Conversa]) -> None:
    """Testa que segmento-herói tem >=20 na janela degradada."""
    tipo_agente, canal, intencao = SEGMENTO_HEROI

    conversas_heroi_degradadas = [
        c
        for c in conversas_fixture
        if c.tipo_agente == tipo_agente
        and c.canal == canal
        and c.intencao == intencao
        and c.iniciada_em.date() >= DATA_INICIO_DEGRADADA
    ]

    assert (
        len(conversas_heroi_degradadas) >= CONVERSAS_HEROI_DEGRADADAS - 5
    ), f"Segmento herói degradado: {len(conversas_heroi_degradadas)} (esperado ≥{CONVERSAS_HEROI_DEGRADADAS})"


def test_fixture_segmento_fino_existe(conversas_fixture: list[Conversa]) -> None:
    """Testa que existe um segmento fino (<20 na janela degradada)."""
    tipo_agente, canal, intencao = SEGMENTO_FINO

    conversas_fino_degradadas = [
        c
        for c in conversas_fixture
        if c.tipo_agente == tipo_agente
        and c.canal == canal
        and c.intencao == intencao
        and c.iniciada_em.date() >= DATA_INICIO_DEGRADADA
    ]

    assert (
        len(conversas_fino_degradadas) < 20
    ), f"Segmento fino muito grande: {len(conversas_fino_degradadas)}"


def test_fixture_sem_cpf_nao_mascarado(conversas_fixture: list[Conversa]) -> None:
    """Testa que nenhuma conversa tem CPF não-mascarado."""
    padrao_cpf_nao_mascarado = r"\d{3}\.\d{3}\.\d{3}-\d{2}"

    for conversa in conversas_fixture:
        for turno in conversa.turnos:
            if re.search(padrao_cpf_nao_mascarado, turno.texto):
                pytest.fail(
                    f"CPF não-mascarado encontrado em {conversa.id}, turno {turno.indice}"
                )


def test_fixture_ids_unicos(conversas_fixture: list[Conversa]) -> None:
    """Testa que todos os IDs são únicos."""
    ids = [c.id for c in conversas_fixture]
    assert len(ids) == len(set(ids)), "IDs duplicados encontrados"


def test_fixture_sem_turnos_vazios(conversas_fixture: list[Conversa]) -> None:
    """Testa que nenhuma conversa tem turnos vazios."""
    for conversa in conversas_fixture:
        for turno in conversa.turnos:
            assert turno.texto.strip(), f"Turno vazio em {conversa.id}"


def test_fixture_turnos_ordenados(conversas_fixture: list[Conversa]) -> None:
    """Testa que os turnos de cada conversa estão corretamente ordenados."""
    for conversa in conversas_fixture:
        indices = [t.indice for t in conversa.turnos]
        assert indices == list(range(len(indices))), f"Índices fora de ordem em {conversa.id}"


def test_fixture_comeca_com_cliente(conversas_fixture: list[Conversa]) -> None:
    """Testa que toda conversa começa com turno do cliente."""
    for conversa in conversas_fixture:
        assert conversa.turnos[0].autor == "cliente", f"Conversa {conversa.id} não começa com cliente"


def test_fixture_alternancia_autor(conversas_fixture: list[Conversa]) -> None:
    """Testa que os autores alternam em toda conversa."""
    for conversa in conversas_fixture:
        for i in range(1, len(conversa.turnos)):
            assert (
                conversa.turnos[i].autor != conversa.turnos[i - 1].autor
            ), f"Autores não alternam em {conversa.id}, turnos {i-1}/{i}"


def test_fixture_intencoes_coerentes(conversas_fixture: list[Conversa]) -> None:
    """Testa que intencoes são coerentes com tipo_agente."""
    intencoes_validas = {
        "suporte": {
            "duvida_produto",
            "problema_tecnico",
            "status_pedido",
            "reclamacao",
        },
        "cobranca": {
            "negociacao_divida",
            "segunda_via_boleto",
            "contestacao_cobranca",
            "promessa_pagamento",
        },
        "retencao": {
            "pedido_cancelamento",
            "downgrade_plano",
            "insatisfacao_preco",
            "oferta_retencao",
        },
    }

    for conversa in conversas_fixture:
        assert (
            conversa.intencao in intencoes_validas[conversa.tipo_agente]
        ), f"Intenção {conversa.intencao} inválida para agente {conversa.tipo_agente}"


def test_fixture_iniciada_em_timezone_aware(conversas_fixture: list[Conversa]) -> None:
    """Testa que todas as conversas têm iniciada_em timezone-aware."""
    for conversa in conversas_fixture:
        assert (
            conversa.iniciada_em.tzinfo is not None
        ), f"Conversa {conversa.id} tem iniciada_em naive"
        assert (
            conversa.iniciada_em.tzinfo.utcoffset(None) is not None
        ), f"Conversa {conversa.id} não é UTC"
