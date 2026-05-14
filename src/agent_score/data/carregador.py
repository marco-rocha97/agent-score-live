"""Loader JSONL → SQLite idempotente."""

import json
import sqlite3
from pathlib import Path

from pydantic import ValidationError

from agent_score.data.modelos import Conversa


def criar_schema(conexao: sqlite3.Connection) -> None:
    """Cria (ou recria) o schema SQLite."""
    cursor = conexao.cursor()

    # Drop das tabelas existentes para idempotência
    cursor.execute("DROP TABLE IF EXISTS turnos")
    cursor.execute("DROP TABLE IF EXISTS conversas")

    # Criar tabela de conversas
    cursor.execute("""
        CREATE TABLE conversas (
            id TEXT PRIMARY KEY,
            tipo_agente TEXT NOT NULL,
            canal TEXT NOT NULL,
            intencao TEXT NOT NULL,
            segmento_cliente TEXT NOT NULL,
            iniciada_em TEXT NOT NULL
        )
    """)

    # Criar tabela de turnos
    cursor.execute("""
        CREATE TABLE turnos (
            conversa_id TEXT NOT NULL,
            indice INTEGER NOT NULL,
            autor TEXT NOT NULL,
            texto TEXT NOT NULL,
            PRIMARY KEY (conversa_id, indice),
            FOREIGN KEY (conversa_id) REFERENCES conversas(id)
        )
    """)

    conexao.commit()


def carregar_jsonl(caminho_jsonl: Path, conexao: sqlite3.Connection) -> int:
    """Carrega conversas de um arquivo JSONL para SQLite."""
    cursor = conexao.cursor()
    total_carregadas = 0

    with open(caminho_jsonl, "r", encoding="utf-8") as f:
        for num_linha, linha in enumerate(f, 1):
            linha = linha.strip()
            if not linha:
                continue

            try:
                dados = json.loads(linha)
                conversa = Conversa(**dados)
            except (json.JSONDecodeError, ValidationError) as e:
                raise ValueError(f"Erro na linha {num_linha}: {e}")

            # Inserir conversa
            cursor.execute(
                """
                INSERT INTO conversas (id, tipo_agente, canal, intencao, segmento_cliente, iniciada_em)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    conversa.id,
                    conversa.tipo_agente,
                    conversa.canal,
                    conversa.intencao,
                    conversa.segmento_cliente,
                    conversa.iniciada_em.isoformat(),
                ),
            )

            # Inserir turnos
            for turno in conversa.turnos:
                cursor.execute(
                    """
                    INSERT INTO turnos (conversa_id, indice, autor, texto)
                    VALUES (?, ?, ?, ?)
                    """,
                    (conversa.id, turno.indice, turno.autor, turno.texto),
                )

            total_carregadas += 1

    conexao.commit()
    return total_carregadas


def carregar(caminho_jsonl: Path = Path("data/conversas.seed.jsonl")) -> None:
    """Função principal: carrega o fixture no banco de dados."""
    if not caminho_jsonl.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_jsonl}")

    caminho_db = Path("data/agent_score.db")
    caminho_db.parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(caminho_db)

    try:
        criar_schema(conexao)
        print(f"Schema criado em {caminho_db}")

        total = carregar_jsonl(caminho_jsonl, conexao)
        print(f"Carregadas {total} conversas")

        # Validação rápida
        cursor = conexao.cursor()
        cursor.execute("SELECT COUNT(*) FROM conversas")
        num_conversas = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM turnos")
        num_turnos = cursor.fetchone()[0]

        print(f"Verificação: {num_conversas} conversas, {num_turnos} turnos")

    finally:
        conexao.close()


def main() -> None:
    """Entry point CLI."""
    carregar()


if __name__ == "__main__":
    main()
