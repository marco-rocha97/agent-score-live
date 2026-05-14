"""Testes para o loader JSONL → SQLite."""

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from agent_score.data.carregador import carregar_jsonl, criar_schema
from agent_score.data.modelos import Conversa, Turno
from datetime import datetime, timezone


@pytest.fixture
def temp_db() -> sqlite3.Connection:
    """Cria um banco de dados temporário para testes."""
    db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    conexao = sqlite3.connect(db.name)
    criar_schema(conexao)
    yield conexao
    conexao.close()
    Path(db.name).unlink()


@pytest.fixture
def temp_jsonl() -> Path:
    """Cria um arquivo JSONL temporário para testes."""
    f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl", encoding="utf-8")
    f.close()
    yield Path(f.name)
    Path(f.name).unlink()


def test_roundtrip_jsonl_sqlite(temp_db: sqlite3.Connection, temp_jsonl: Path) -> None:
    """Testa roundtrip JSONL → SQLite com validação."""
    # Escrever conversa válida em JSONL
    conversa = Conversa(
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
            Turno(indice=3, autor="agente", texto="Ok"),
        ],
    )

    with open(temp_jsonl, "w", encoding="utf-8") as f:
        f.write(conversa.model_dump_json() + "\n")

    # Carregar no SQLite
    total = carregar_jsonl(temp_jsonl, temp_db)
    assert total == 1

    # Verificar contagem
    cursor = temp_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversas")
    assert cursor.fetchone()[0] == 1

    cursor.execute("SELECT COUNT(*) FROM turnos")
    assert cursor.fetchone()[0] == 4


def test_idempotencia(temp_db: sqlite3.Connection, temp_jsonl: Path) -> None:
    """Testa que rodar o loader duas vezes resulta no mesmo estado."""
    conversa = Conversa(
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
            Turno(indice=3, autor="agente", texto="Ok"),
        ],
    )

    with open(temp_jsonl, "w", encoding="utf-8") as f:
        f.write(conversa.model_dump_json() + "\n")

    # Primeira carga
    carregar_jsonl(temp_jsonl, temp_db)
    cursor = temp_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversas")
    count_primeira = cursor.fetchone()[0]

    # Recria schema (simula recarregamento)
    criar_schema(temp_db)
    carregar_jsonl(temp_jsonl, temp_db)
    cursor.execute("SELECT COUNT(*) FROM conversas")
    count_segunda = cursor.fetchone()[0]

    assert count_primeira == count_segunda == 1


def test_erro_jsonl_invalido(temp_db: sqlite3.Connection) -> None:
    """Testa que um JSONL inválido aborta com erro claro."""
    f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl", encoding="utf-8")
    f.write("{ invalido json\n")
    f.close()

    with pytest.raises(ValueError, match="Erro na linha"):
        carregar_jsonl(Path(f.name), temp_db)

    Path(f.name).unlink()


def test_erro_modelo_invalido(temp_db: sqlite3.Connection) -> None:
    """Testa que um modelo inválido no JSONL aborta."""
    f = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl", encoding="utf-8")
    # Conversa sem turnos (invalida)
    f.write(
        json.dumps({
            "id": "conv-0001",
            "tipo_agente": "suporte",
            "canal": "voz",
            "intencao": "duvida_produto",
            "segmento_cliente": "individual",
            "iniciada_em": "2026-05-01T10:00:00+00:00",
            "turnos": [],  # Vazio! Inválido
        }) + "\n"
    )
    f.close()

    with pytest.raises(ValueError, match="Erro na linha"):
        carregar_jsonl(Path(f.name), temp_db)

    Path(f.name).unlink()


def test_multiplas_conversas(temp_db: sqlite3.Connection, temp_jsonl: Path) -> None:
    """Testa carregamento de múltiplas conversas."""
    conversas = []
    for i in range(3):
        conversa = Conversa(
            id=f"conv-{i:04d}",
            tipo_agente="suporte",
            canal="voz",
            intencao="duvida_produto",
            segmento_cliente="individual",
            iniciada_em=datetime(2026, 5, 1 + i, 10, 0, 0, tzinfo=timezone.utc),
            turnos=[
                Turno(indice=0, autor="cliente", texto="Olá"),
                Turno(indice=1, autor="agente", texto="Oi"),
                Turno(indice=2, autor="cliente", texto="Teste"),
                Turno(indice=3, autor="agente", texto="Ok"),
            ],
        )
        conversas.append(conversa)

    with open(temp_jsonl, "w", encoding="utf-8") as f:
        for conversa in conversas:
            f.write(conversa.model_dump_json() + "\n")

    total = carregar_jsonl(temp_jsonl, temp_db)
    assert total == 3

    cursor = temp_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM conversas")
    assert cursor.fetchone()[0] == 3

    cursor.execute("SELECT COUNT(*) FROM turnos")
    assert cursor.fetchone()[0] == 12  # 3 conversas × 4 turnos
