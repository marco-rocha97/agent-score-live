"""Testes para modelos Pydantic."""

from datetime import datetime, timezone

import pytest

from agent_score.data.modelos import Conversa, Turno


class TestTurno:
    """Testes para a classe Turno."""

    def test_turno_valido(self) -> None:
        """Testa criação de um turno válido."""
        turno = Turno(indice=0, autor="cliente", texto="Olá, preciso de ajuda")
        assert turno.indice == 0
        assert turno.autor == "cliente"
        assert turno.texto == "Olá, preciso de ajuda"

    def test_turno_texto_vazio_rejeitado(self) -> None:
        """Testa que texto vazio é rejeitado."""
        with pytest.raises(ValueError, match="texto não pode ser vazio"):
            Turno(indice=0, autor="cliente", texto="   ")

    def test_turno_cpf_nao_mascarado_rejeitado(self) -> None:
        """Testa que CPF não-mascarado é rejeitado."""
        with pytest.raises(ValueError, match="CPF não-mascarado"):
            Turno(
                indice=0,
                autor="cliente",
                texto="Meu CPF é 123.456.789-10 e preciso resolver isso",
            )

    def test_turno_cpf_mascarado_aceito(self) -> None:
        """Testa que CPF mascarado (xxx.xxx.xxx-xx) é aceito."""
        turno = Turno(
            indice=0,
            autor="cliente",
            texto="Meu CPF é xxx.xxx.xxx-xx e preciso de ajuda",
        )
        assert "xxx.xxx.xxx-xx" in turno.texto


class TestConversa:
    """Testes para a classe Conversa."""

    def test_conversa_valida(self) -> None:
        """Testa criação de uma conversa válida."""
        conversa = Conversa(
            id="conv-0001",
            tipo_agente="suporte",
            canal="voz",
            intencao="duvida_produto",
            segmento_cliente="individual",
            iniciada_em=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
            turnos=[
                Turno(indice=0, autor="cliente", texto="Olá"),
                Turno(indice=1, autor="agente", texto="Oi, como posso ajudar?"),
                Turno(indice=2, autor="cliente", texto="Tenho uma dúvida"),
                Turno(indice=3, autor="agente", texto="Claro, qual é sua dúvida?"),
            ],
        )
        assert conversa.id == "conv-0001"
        assert len(conversa.turnos) == 4

    def test_conversa_iniciada_em_naive_rejeitada(self) -> None:
        """Testa que iniciada_em naive (sem timezone) é rejeitada."""
        with pytest.raises(ValueError, match="timezone-aware"):
            Conversa(
                id="conv-0001",
                tipo_agente="suporte",
                canal="voz",
                intencao="duvida_produto",
                segmento_cliente="individual",
                iniciada_em=datetime(2026, 5, 1, 10, 0, 0),  # naive
                turnos=[
                    Turno(indice=0, autor="cliente", texto="Olá"),
                    Turno(indice=1, autor="agente", texto="Oi"),
                    Turno(indice=2, autor="cliente", texto="Teste"),
                    Turno(indice=3, autor="agente", texto="Ok"),
                ],
            )

    def test_conversa_intencao_incoerente_rejeitada(self) -> None:
        """Testa que intencao incoerente com tipo_agente é rejeitada."""
        with pytest.raises(ValueError, match="intencao"):
            Conversa(
                id="conv-0001",
                tipo_agente="suporte",
                canal="voz",
                intencao="negociacao_divida",  # inválida para suporte
                segmento_cliente="individual",
                iniciada_em=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
                turnos=[
                    Turno(indice=0, autor="cliente", texto="Olá"),
                    Turno(indice=1, autor="agente", texto="Oi"),
                    Turno(indice=2, autor="cliente", texto="Teste"),
                    Turno(indice=3, autor="agente", texto="Ok"),
                ],
            )

    def test_conversa_poucos_turnos_rejeitada(self) -> None:
        """Testa que conversa com <4 turnos é rejeitada."""
        with pytest.raises(ValueError, match="pelo menos 4 turnos"):
            Conversa(
                id="conv-0001",
                tipo_agente="suporte",
                canal="voz",
                intencao="duvida_produto",
                segmento_cliente="individual",
                iniciada_em=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
                turnos=[
                    Turno(indice=0, autor="cliente", texto="Olá"),
                    Turno(indice=1, autor="agente", texto="Oi"),
                    Turno(indice=2, autor="cliente", texto="Teste"),
                ],
            )

    def test_conversa_nao_comeca_em_cliente_rejeitada(self) -> None:
        """Testa que conversa que não começa em cliente é rejeitada."""
        with pytest.raises(ValueError, match="começar com turno do cliente"):
            Conversa(
                id="conv-0001",
                tipo_agente="suporte",
                canal="voz",
                intencao="duvida_produto",
                segmento_cliente="individual",
                iniciada_em=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
                turnos=[
                    Turno(indice=0, autor="agente", texto="Oi"),  # começa em agente!
                    Turno(indice=1, autor="cliente", texto="Olá"),
                    Turno(indice=2, autor="agente", texto="Teste"),
                    Turno(indice=3, autor="cliente", texto="Ok"),
                ],
            )

    def test_conversa_autor_nao_alterna_rejeitada(self) -> None:
        """Testa que conversa onde autor não alterna é rejeitada."""
        with pytest.raises(ValueError, match="alternar autor"):
            Conversa(
                id="conv-0001",
                tipo_agente="suporte",
                canal="voz",
                intencao="duvida_produto",
                segmento_cliente="individual",
                iniciada_em=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
                turnos=[
                    Turno(indice=0, autor="cliente", texto="Olá"),
                    Turno(indice=1, autor="cliente", texto="Mais uma coisa"),  # não alterna!
                    Turno(indice=2, autor="agente", texto="Teste"),
                    Turno(indice=3, autor="agente", texto="Ok"),
                ],
            )

    def test_conversa_indice_nao_sequencial_rejeitada(self) -> None:
        """Testa que conversa com índices não-sequenciais é rejeitada."""
        with pytest.raises(ValueError, match="sequenciais"):
            Conversa(
                id="conv-0001",
                tipo_agente="suporte",
                canal="voz",
                intencao="duvida_produto",
                segmento_cliente="individual",
                iniciada_em=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
                turnos=[
                    Turno(indice=0, autor="cliente", texto="Olá"),
                    Turno(indice=1, autor="agente", texto="Oi"),
                    Turno(indice=5, autor="cliente", texto="Teste"),  # buraco!
                    Turno(indice=6, autor="agente", texto="Ok"),
                ],
            )

    def test_conversa_todas_intencoes_suporte(self) -> None:
        """Testa todas as intenções válidas para suporte."""
        intencoes = [
            "duvida_produto",
            "problema_tecnico",
            "status_pedido",
            "reclamacao",
        ]
        for intencao in intencoes:
            conversa = Conversa(
                id="conv-0001",
                tipo_agente="suporte",
                canal="voz",
                intencao=intencao,  # type: ignore
                segmento_cliente="individual",
                iniciada_em=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
                turnos=[
                    Turno(indice=0, autor="cliente", texto="Olá"),
                    Turno(indice=1, autor="agente", texto="Oi"),
                    Turno(indice=2, autor="cliente", texto="Teste"),
                    Turno(indice=3, autor="agente", texto="Ok"),
                ],
            )
            assert conversa.intencao == intencao

    def test_conversa_todas_intencoes_cobranca(self) -> None:
        """Testa todas as intenções válidas para cobrança."""
        intencoes = [
            "negociacao_divida",
            "segunda_via_boleto",
            "contestacao_cobranca",
            "promessa_pagamento",
        ]
        for intencao in intencoes:
            conversa = Conversa(
                id="conv-0001",
                tipo_agente="cobranca",
                canal="voz",
                intencao=intencao,  # type: ignore
                segmento_cliente="individual",
                iniciada_em=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
                turnos=[
                    Turno(indice=0, autor="cliente", texto="Olá"),
                    Turno(indice=1, autor="agente", texto="Oi"),
                    Turno(indice=2, autor="cliente", texto="Teste"),
                    Turno(indice=3, autor="agente", texto="Ok"),
                ],
            )
            assert conversa.intencao == intencao

    def test_conversa_todas_intencoes_retencao(self) -> None:
        """Testa todas as intenções válidas para retenção."""
        intencoes = [
            "pedido_cancelamento",
            "downgrade_plano",
            "insatisfacao_preco",
            "oferta_retencao",
        ]
        for intencao in intencoes:
            conversa = Conversa(
                id="conv-0001",
                tipo_agente="retencao",
                canal="voz",
                intencao=intencao,  # type: ignore
                segmento_cliente="individual",
                iniciada_em=datetime(2026, 5, 1, 10, 0, 0, tzinfo=timezone.utc),
                turnos=[
                    Turno(indice=0, autor="cliente", texto="Olá"),
                    Turno(indice=1, autor="agente", texto="Oi"),
                    Turno(indice=2, autor="cliente", texto="Teste"),
                    Turno(indice=3, autor="agente", texto="Ok"),
                ],
            )
            assert conversa.intencao == intencao
