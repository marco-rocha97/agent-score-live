"""Pipeline de geração de conversas sintéticas com Pydantic AI + Gemini."""

import asyncio
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pydantic_ai import Agent  # type: ignore[import-untyped]

from agent_score.data.modelos import Conversa, RoteiroConversa
from agent_score.data.sementes import SEEDS_AGENTE
from agent_score.data.taxonomia import (
    CONVERSAS_FINO_DEGRADADAS,
    CONVERSAS_FINO_SAUDAVEIS,
    CONVERSAS_HEROI_DEGRADADAS,
    CONVERSAS_HEROI_SAUDAVEIS,
    CONVERSAS_RESTANTE,
    DATA_INICIO_DEGRADADA,
    HORARIOS_COMERCIAIS,
    INTENCOES,
    JANELA_INICIO,
    PADRAO_FALHA_HEROI,
    SEGMENTO_FINO,
    SEGMENTO_HEROI,
    SEMENTE_ALEATORIA,
)
from agent_score.settings import configuracoes


def _obter_modelo() -> object:
    """Obtém o modelo LLM configurado (Gemini ou OpenRouter)."""
    provider = configuracoes.llm_provider.lower()

    if provider == "gemini":
        if not configuracoes.gemini_api_key:
            raise ValueError("GEMINI_API_KEY não configurada em .env")
        from pydantic_ai.models.gemini import GeminiModelProvider  # type: ignore[attr-defined]

        return GeminiModelProvider(api_key=configuracoes.gemini_api_key)  # type: ignore[return-value]
    elif provider == "openrouter":
        if not configuracoes.openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY não configurada em .env")
        from pydantic_ai.models.openai import OpenAIModelProvider  # type: ignore[attr-defined]

        return OpenAIModelProvider(  # type: ignore[return-value]
            model_name="openrouter/google/gemini-2.5-flash",
            api_key=configuracoes.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    else:
        raise ValueError(f"Provider LLM desconhecido: {provider}")


async def _gerar_conversa(
    tipo_agente: str,
    canal: str,
    intencao: str,
    segmento_cliente: str,
    degradada: bool = False,
) -> RoteiroConversa:
    """Gera uma conversa sintética usando o LLM."""
    modelo = _obter_modelo()
    agente = Agent(  # type: ignore[call-overload]
        model=modelo,
        result_type=RoteiroConversa,
        retries=2,
    )

    estilo_canal = "fala transcrita, coloquial" if canal == "voz" else "texto curto, assíncrono"

    instrucao_falha = ""
    if degradada:
        instrucao_falha = f"""

**IMPORTANTE — Esta conversa é DEGRADADA (janela 8-14):**
{PADRAO_FALHA_HEROI}

Gere uma conversa onde o agente comete esse erro. A conversa é realista e plausível,
mas exibe claramente o padrão de falha plantado."""

    seed_exemplo = random.choice(SEEDS_AGENTE[tipo_agente][canal])

    prompt = f"""Você é um gerador de conversas de suporte ao cliente em Português-Brasil.
Gere uma conversa sintética, realista e plausível.

**Contexto:**
- Tipo de agente: {tipo_agente}
- Canal: {canal} ({estilo_canal})
- Intenção: {intencao}
- Segmento do cliente: {segmento_cliente}

**Exemplo para calibração (mesmo tipo de agente e canal):**
{seed_exemplo}

**Requisitos:**
- Mínimo 4 turnos (cliente → agente → cliente → agente ...).
- Começa sempre com o cliente.
- Fala natural e plausível em PT-BR.
- Nomes e CPF: use fictícios e mascarados (xxx.xxx.xxx-xx).
- Sem código ou markup — apenas diálogo.{instrucao_falha}

Gere agora:"""

    resultado = await agente.run(prompt)
    return resultado.data


async def _gerar_lote_conversas() -> list[Conversa]:
    """Gera o lote completo de conversas."""
    random.seed(SEMENTE_ALEATORIA)

    conversas_a_gerar: list[tuple[str, str, str, str, bool]] = []

    # Segmento-herói: 25 saudáveis (dias 1-7) + 25 degradadas (dias 8-14)
    for _ in range(CONVERSAS_HEROI_SAUDAVEIS):
        conversas_a_gerar.append(
            (SEGMENTO_HEROI[0], SEGMENTO_HEROI[1], SEGMENTO_HEROI[2], "individual", False)
        )
    for _ in range(CONVERSAS_HEROI_DEGRADADAS):
        conversas_a_gerar.append(
            (SEGMENTO_HEROI[0], SEGMENTO_HEROI[1], SEGMENTO_HEROI[2], "individual", True)
        )

    # Segmento fino: 8 saudáveis + 12 degradadas
    for _ in range(CONVERSAS_FINO_SAUDAVEIS):
        conversas_a_gerar.append(
            (SEGMENTO_FINO[0], SEGMENTO_FINO[1], SEGMENTO_FINO[2], "individual", False)
        )
    for _ in range(CONVERSAS_FINO_DEGRADADAS):
        conversas_a_gerar.append(
            (SEGMENTO_FINO[0], SEGMENTO_FINO[1], SEGMENTO_FINO[2], "individual", True)
        )

    # Restante: distribuir pelos demais segmentos, todos saudáveis
    tipos_agente = list(INTENCOES.keys())
    canais = ["voz", "whatsapp"]
    segmentos = ["individual", "empresarial", "adesao"]

    for _ in range(CONVERSAS_RESTANTE):
        tipo_agente = random.choice(tipos_agente)
        canal = random.choice(canais)
        intencao = random.choice(INTENCOES[tipo_agente])
        segmento_cliente = random.choice(segmentos)

        conversas_a_gerar.append((tipo_agente, canal, intencao, segmento_cliente, False))

    # Embaralhar
    random.shuffle(conversas_a_gerar)

    conversas: list[Conversa] = []
    for idx, (tipo_agente, canal, intencao, segmento_cliente, degradada) in enumerate(
        conversas_a_gerar
    ):
        id_conversa = f"conv-{idx+1:04d}"

        # Atribuir dia e horário dentro da janela
        if degradada:
            # Dias 8-14
            dia_offset = random.randint(0, 6)
            data = DATA_INICIO_DEGRADADA + timedelta(days=dia_offset)
        else:
            # Dias 1-7
            dia_offset = random.randint(0, 6)
            data = JANELA_INICIO + timedelta(days=dia_offset)

        hora = random.choice(HORARIOS_COMERCIAIS)
        minuto = random.randint(0, 59)
        iniciada_em = datetime(
            data.year, data.month, data.day, hora, minuto, 0, tzinfo=timezone.utc
        )

        # Gerar conversa
        try:
            roteiro = await _gerar_conversa(tipo_agente, canal, intencao, segmento_cliente, degradada)
        except Exception as e:  # noqa: F841
            print(f"Erro ao gerar conversa {id_conversa}: {e}")
            # Fallback: criar uma conversa mínima válida
            from agent_score.data.modelos import Turno
            roteiro = RoteiroConversa(
                turnos=[
                    Turno(indice=0, autor="cliente", texto=f"Preciso de {intencao}"),
                    Turno(indice=1, autor="agente", texto="Como posso ajudar?"),
                    Turno(indice=2, autor="cliente", texto="Meu CPF é xxx.xxx.xxx-xx"),
                    Turno(indice=3, autor="agente", texto="Vou resolver para você."),
                ]
            )

        # Montar Conversa com metadados
        conversa = Conversa(
            id=id_conversa,
            tipo_agente=tipo_agente,  # type: ignore
            canal=canal,  # type: ignore
            intencao=intencao,  # type: ignore
            segmento_cliente=segmento_cliente,  # type: ignore
            iniciada_em=iniciada_em,
            turnos=roteiro.turnos,
        )
        conversas.append(conversa)

        # Throttle: respeitar rate limit do Gemini free tier
        if (idx + 1) % 10 == 0:
            await asyncio.sleep(1)

    return conversas


def _escrever_jsonl(conversas: list[Conversa], caminho: Path) -> None:
    """Escreve conversas em formato JSONL."""
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as f:
        for conversa in conversas:
            linha = conversa.model_dump_json()
            f.write(linha + "\n")

    print(f"Fixture gerado: {caminho} ({len(conversas)} conversas)")


async def gerar() -> None:
    """Função principal: gera e escreve o fixture."""
    print("Iniciando geração de conversas sintéticas...")
    conversas = await _gerar_lote_conversas()
    _escrever_jsonl(conversas, Path("data/conversas.seed.jsonl"))
    print("Geração concluída!")


def main() -> None:
    """Entry point CLI."""
    asyncio.run(gerar())


if __name__ == "__main__":
    main()
