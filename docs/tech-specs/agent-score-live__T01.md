# Tech Spec: Base de conversas — `T01`

> **SPEC:** [`docs/specs/agent-score-live.md`](../specs/agent-score-live.md)
> **Plan:** [`docs/plans/agent-score-live.md`](../plans/agent-score-live.md) — task `T01`
> **Convenções aplicadas:** `CLAUDE.md` (projeto) + `~/.claude/rules/*` (usuário)
>
> Este documento detalha **como** entregar a task. O **porquê** vive no SPEC; o **quê** e **em que ordem**, no Plan.

---

## Task Scope

- **Comportamento entregue** (do Plan): existe um conjunto de ~180 conversas, no formato necessário para scoring e drill-down, consultável no SQLite e pronto para ser carregado.
- **Stories/critérios do SPEC cobertos:** Feature "Conversation ingestion and scoring" — cenário "A batch of synthetic conversations is loaded and scored" (lado dados/ingestão); pré-requisito de "Score is explainable down to the turn" (estrutura por turno).
- **Depende de:** — (primeira task; bootstrap do projeto acontece junto)
- **Dependências externas:** API do Gemini (AI Studio, free tier) para a geração — usada **uma vez**, fora do caminho da demo.

---

## Decisões fechadas (rodada de negociação)

1. **Janela temporal: 14 dias.** Dias 1–7 = baseline saudável; dias 8–14 = janela visível no dashboard, onde a regressão é plantada. Resolve a inconsistência SPEC/Plan: a T04 compara "janela de 7 dias vs. os 7 dias anteriores" — impossível com só 7 dias de dados.
2. **Geração sintética com seeds PT-BR escritos à mão.** A busca no Kaggle foi feita (registrada na conversa); nenhum dataset encaixa (inglês, domínio errado, sem estrutura de turno). Satisfaz a cláusula de fallback do critério de aceite da T01.
3. **Persistência: T01 entrega JSONL + loader + tabelas SQLite.** Entregável = "conversas consultáveis no SQLite".
4. **Distribuição ponderada intencional.** Um segmento-herói com ≥20 conversas na janela degradada (alerta confirmado na T04) + um segmento fino <20 (caminho "hipótese de dado limitado").

---

## Architecture

- **Abordagem geral:** T01 é a fundação de dados do projeto — define o schema Pydantic que T02 (scoring) e T05 (drill-down) consomem. Um pipeline de geração usa o Pydantic AI com Gemini 2.5 Flash para produzir conversas sintéticas em PT-BR, guiado por seeds few-shot escritos à mão e por uma taxonomia/distribuição fixa. A geração roda **uma vez**, produz o fixture `data/conversas.seed.jsonl` (commitado, fonte de verdade) e um loader popula o SQLite. A demo carrega o fixture: determinística e com custo zero de API.
- **A regressão é plantada no _comportamento_, não no _score_.** As conversas da janela degradada exibem genuinamente o padrão de falha (agente de Cobrança que não coleta CPF inline → quebra de contexto, repetição, não-resolução). T02 pontua honestamente e a queda emerge. T01 nunca escreve scores.
- **Módulos afetados:** novo pacote `src/agent_score/data/`.
- **Arquivos novos:**
  - `src/agent_score/data/modelos.py` — modelos Pydantic: `Turno`, `Conversa`, `RoteiroConversa` (saída do LLM).
  - `src/agent_score/data/taxonomia.py` — constantes: taxonomia de intenções por agente, segmentos, janela de 14 dias, alvos de distribuição, especificação da regressão plantada, semente aleatória.
  - `src/agent_score/data/sementes.py` — conversas-exemplo PT-BR escritas à mão (few-shot), 2–3 por tipo de agente.
  - `src/agent_score/data/geracao.py` — pipeline de geração (Pydantic AI + Gemini), throttle, montagem de `Conversa`, escrita do JSONL. CLI: `python -m agent_score.data.geracao`.
  - `src/agent_score/data/carregador.py` — loader JSONL → SQLite (tabelas `conversas`, `turnos`), idempotente. CLI: `python -m agent_score.data.carregador`.
  - `src/agent_score/settings.py` — config de ambiente via `pydantic-settings` (chaves de API, provider).
  - `data/conversas.seed.jsonl` — fixture commitado (~180 linhas).
  - **Bootstrap do projeto** (lands com T01 por ser a primeira task): `pyproject.toml` (uv), `.python-version`, `.gitignore`, `.env.example`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
- **Padrões reutilizados:** nenhum — repositório era só documentação. **Esta Tech Spec estabelece os padrões** (modelagem Pydantic, CLI por módulo, testes com `pytest`).
- **Observabilidade:** instrumentar as chamadas de geração com Logfire é opcional e não bloqueia o aceite da T01 (Logfire entra de fato no pipeline de scoring, T02).

> **Fonte das decisões:** `CLAUDE.md` (stack: Python 3.12+, uv, Pydantic v2, Pydantic AI, Gemini/OpenRouter, SQLite); rodada de negociação acima; regras do usuário (`secrets.md`, `ci-cd.md`, `git.md`, `dependencies.md`, `datetime.md`, `language.md`).

---

## Contracts

### Interfaces internas (o contrato que T02/T05 consomem)

```python
# src/agent_score/data/modelos.py
from datetime import datetime
from typing import Literal
from pydantic import BaseModel

TipoAgente = Literal["suporte", "cobranca", "retencao"]
Canal = Literal["voz", "whatsapp"]
SegmentoCliente = Literal["individual", "empresarial", "adesao"]
Autor = Literal["cliente", "agente"]
Intencao = Literal[
    # suporte
    "duvida_produto", "problema_tecnico", "status_pedido", "reclamacao",
    # cobranca
    "negociacao_divida", "segunda_via_boleto", "contestacao_cobranca", "promessa_pagamento",
    # retencao
    "pedido_cancelamento", "downgrade_plano", "insatisfacao_preco", "oferta_retencao",
]

class Turno(BaseModel):
    indice: int            # >= 0, sequencial, sem buracos
    autor: Autor
    texto: str             # não-vazio após strip

class Conversa(BaseModel):
    id: str                # "conv-0001" .. "conv-0180"
    tipo_agente: TipoAgente
    canal: Canal
    intencao: Intencao
    segmento_cliente: SegmentoCliente
    iniciada_em: datetime  # UTC, timezone-aware, ISO-8601
    turnos: list[Turno]    # >= 4 turnos, começa em "cliente", alterna autor

class RoteiroConversa(BaseModel):
    """Saída do LLM — só os turnos. A metadata é atribuída pelo pipeline."""
    turnos: list[Turno]
```

### Formato do fixture — `data/conversas.seed.jsonl`

Uma `Conversa` serializada por linha (JSON, `iniciada_em` em ISO-8601 com `Z`). Fonte de verdade versionada no git.

### Schema SQLite — `data/agent_score.db`

```sql
CREATE TABLE conversas (
  id               TEXT PRIMARY KEY,
  tipo_agente      TEXT NOT NULL,
  canal            TEXT NOT NULL,
  intencao         TEXT NOT NULL,
  segmento_cliente TEXT NOT NULL,
  iniciada_em      TEXT NOT NULL          -- ISO-8601 UTC
);
CREATE TABLE turnos (
  conversa_id TEXT NOT NULL REFERENCES conversas(id),
  indice      INTEGER NOT NULL,
  autor       TEXT NOT NULL,
  texto       TEXT NOT NULL,
  PRIMARY KEY (conversa_id, indice)
);
```

O loader recria as duas tabelas (`DROP TABLE IF EXISTS` → `CREATE`) e faz bulk-insert — idempotente e determinístico. T01 é dono **apenas** de `conversas`/`turnos`; T02 adiciona suas próprias tabelas.

### CLI

```
python -m agent_score.data.geracao      # gera e (re)escreve data/conversas.seed.jsonl  — gasta quota do Gemini
python -m agent_score.data.carregador   # carrega o JSONL no data/agent_score.db        — custo zero, idempotente
```

---

## Data Model

| Campo | Tipo | Obrigatório | Default | Notas |
|---|---|---|---|---|
| `Conversa.id` | `str` | sim | — | `conv-NNNN`, único, atribuído pelo pipeline |
| `Conversa.tipo_agente` | `TipoAgente` | sim | — | `suporte` \| `cobranca` \| `retencao` |
| `Conversa.canal` | `Canal` | sim | — | `voz` \| `whatsapp` |
| `Conversa.intencao` | `Intencao` | sim | — | Literal de 12 valores; **coerente com `tipo_agente`** (validador) |
| `Conversa.segmento_cliente` | `SegmentoCliente` | sim | — | `individual` \| `empresarial` \| `adesao` |
| `Conversa.iniciada_em` | `datetime` | sim | — | UTC, timezone-aware; naive é rejeitado (validador) |
| `Conversa.turnos` | `list[Turno]` | sim | — | ≥ 4; `indice` sequencial 0..n; começa em `cliente`; `autor` alterna (validador) |
| `Turno.indice` | `int` | sim | — | ≥ 0 |
| `Turno.autor` | `Autor` | sim | — | `cliente` \| `agente` |
| `Turno.texto` | `str` | sim | — | não-vazio após `strip()`; **sem PII não-mascarada** |

> **Validação:** `field_validator`/`model_validator` no `modelos.py`. Regras não-óbvias: (1) `intencao` deve pertencer ao conjunto do `tipo_agente`; (2) `iniciada_em` deve ser timezone-aware (regra `datetime.md`); (3) `turnos` deve começar em `cliente` e alternar autor; (4) `texto` não pode casar com CPF não-mascarado `\d{3}\.\d{3}\.\d{3}-\d{2}`.

### Taxonomia e distribuição (`taxonomia.py`)

- **Intenções por agente:** suporte → {duvida_produto, problema_tecnico, status_pedido, reclamacao}; cobranca → {negociacao_divida, segunda_via_boleto, contestacao_cobranca, promessa_pagamento}; retencao → {pedido_cancelamento, downgrade_plano, insatisfacao_preco, oferta_retencao}.
- **Janela:** `JANELA_FIM = date(2026, 5, 13)`, 14 dias → `JANELA_INICIO = date(2026, 4, 30)`. Datas fixas (não relativas a `now()`) para o fixture ser 100% determinístico. Janela degradada = dias 8–14 (`2026-05-07` … `2026-05-13`).
- **Segmento-herói:** `cobranca` / `whatsapp` / `negociacao_divida` — ~25 conversas saudáveis nos dias 1–7 + ~25 degradadas nos dias 8–14 (≥20 na janela → **alerta confirmado** na T04). Padrão de falha plantado: agente não coleta CPF inline → quebra de contexto, repetição, não-resolução (cobre ≥60% das degradadas → padrão dominante na T06; alinhado ao exemplo de recomendação da T07).
- **Segmento fino:** `retencao` / `voz` / `insatisfacao_preco` — ~8 saudáveis + ~12 degradadas (leve), <20 na janela → **hipótese de dado limitado** na T04.
- **Restante (~110):** distribuído pelos demais segmentos, todas saudáveis, sem queda plantada — corpo geral do dashboard.
- **Total alvo:** ~180 (dentro do range 100–200 do SPEC). `SEMENTE_ALEATORIA = 42` para a montagem (atribuição de id, timestamp dentro do dia em horário comercial, escolha de segmentos do restante) ser reprodutível — só o texto gerado pelo LLM varia entre execuções.

---

## External Integrations

- **Parceiro:** Google AI Studio — Gemini 2.5 Flash (free tier).
- **Como é usado:** apenas no comando `geracao`, fora do caminho da demo. Acesso via Pydantic AI (provider Gemini).
- **Autenticação:** `GEMINI_API_KEY` via variável de ambiente (`pydantic-settings` lê de `.env`). `.env` no `.gitignore`; `.env.example` commitado com a chave em branco. Fallback configurável: `LLM_PROVIDER=openrouter` + `OPENROUTER_API_KEY`.
- **Rate limits / retry:** geração em batch throttled a `LIMITE_RPM` (constante conservadora para o free tier); retry com backoff exponencial em erro 429; `retries=2` no `Agent` do Pydantic AI para falha de validação de saída.
- **Mock para testes:** `TestModel` do Pydantic AI (`pydantic_ai.models.test`) — nenhum teste chama a API real.

---

## Trade-offs and Rejected Alternatives

**Decisão: geração sintética com seeds à mão, não dataset Kaggle.**
- Rejeitado: baixar e adaptar um dataset do Kaggle.
- Motivo: todos os candidatos são inglês, domínio errado e sem estrutura de turno; adaptá-los exigiria tradução, re-rotulagem de canais, fatiamento em 3 agentes e fabricação da regressão — ~80% de trabalho sintético mesmo assim.
- Fonte: busca registrada na conversa; cláusula de fallback no critério de aceite da T01.

**Decisão: 14 dias de dados, não 7.**
- Rejeitado: 7 dias (texto literal da T01).
- Motivo: o cenário de detecção de queda da T04 compara a janela com "os 7 dias anteriores" — inviável sem baseline.
- Fonte: cenário "A relevant drop raises an alert" no SPEC.

**Decisão: fixture JSONL commitado + loader, geração roda uma vez.**
- Rejeitado: gerar conversas a cada boot da aplicação.
- Motivo: gastaria quota do free tier a cada execução e tornaria a demo não-determinística (o anchor metric exige um caso ilustrativo estável).
- Fonte: `CLAUDE.md` (custo zero de API no demo); regra do usuário sobre custo de API.

**Decisão: regressão plantada no comportamento, não no score.**
- Rejeitado: gerar conversas já com scores baixos.
- Motivo: acoplaria T01 ao T02 e tornaria o motor de score não-verificável (não dá para validar um scorer contra dados cujo score foi fabricado).
- Fonte: separação de responsabilidades T01/T02 no Plan.

**Decisão: `sqlite3` da stdlib, sem ORM.**
- Rejeitado: SQLAlchemy ou similar.
- Motivo: escopo é um par de tabelas; ORM seria peso morto.
- Fonte: `CLAUDE.md` (SQLite, infra mínima); regra de dependências do usuário (minimalismo, "reuse over install").

**Decisão: o LLM gera só `RoteiroConversa` (turnos); a metadata é atribuída pelo pipeline.**
- Rejeitado: o LLM gerar `id`, `iniciada_em`, enums.
- Motivo: reduz superfície de erro de validação e garante que a distribuição ponderada seja controlada por código, não pela sorte do LLM.

---

## Risks and Mitigations

| Risco | Impacto | Mitigação |
|---|---|---|
| Rate limit do free tier durante a geração | geração lenta ou falha parcial | batch throttled a `LIMITE_RPM` + retry com backoff em 429; fixture commitado → roda uma vez só |
| Regressão sutil demais ou óbvia demais | T04/T06 não detectam, ou detectam trivialmente | padrão de falha explícito no prompt da janela degradada; teste de sanidade confere a contagem do segmento-herói; calibração fina fica para a T02 |
| Conversas sintéticas pouco realistas | demo perde credibilidade na banca | few-shot com seeds PT-BR escritos à mão; estilo específico por canal (voz = fala transcrita; whatsapp = texto curto/assíncrono) |
| Taxonomia de `intencao` inventada nesta task | T06 (causa-raiz) depende dela; mudar depois = retrabalho | taxonomia fixada em `taxonomia.py` como constante única e citada como contrato nesta Tech Spec |
| `data/agent_score.db` commitado por engano | binário derivado no git, divergência de estado | `.gitignore` cobre `data/*.db`; só o JSONL é versionado; o `.db` é sempre regenerável pelo loader |
| PII real vazando nas conversas | violação da suposição LGPD do SPEC | prompt instrui nomes fictícios e documentos pré-mascarados; validador rejeita CPF não-mascarado; teste de sanidade varre o fixture inteiro |

---

## Testing Plan

Framework: **pytest** (estabelecido aqui). Estrutura: `tests/` espelhando `src/`.

- **Unit — `tests/data/test_modelos.py`:**
  - Happy path: uma `Conversa` válida parseia.
  - Erro: `turnos` vazio é rejeitado; `intencao` incoerente com `tipo_agente` é rejeitada; `iniciada_em` naive (sem tz) é rejeitada.
  - Edge: `turnos` que não começa em `cliente` / não alterna autor é rejeitado; `texto` com CPF não-mascarado é rejeitado.
- **Unit — `tests/data/test_geracao.py`** (com `TestModel` do Pydantic AI, sem API real):
  - O prompt montado inclui o `tipo_agente`/`canal` corretos e o bloco de falha quando a conversa é degradada.
  - Pós-processamento: cada `Conversa` recebe `id` único e `iniciada_em` dentro do dia atribuído.
- **Integration — `tests/data/test_carregador.py`:**
  - Roundtrip JSONL → SQLite: contagem de `conversas` e `turnos` confere com o fixture.
  - Idempotência: rodar o loader duas vezes resulta no mesmo estado.
  - Erro: uma linha JSONL inválida aborta com erro claro, sem inserção parcial.
- **Sanity — `tests/data/test_fixture.py`** (valida o fixture commitado):
  - 3 tipos de agente e 2 canais presentes; `iniciada_em` cobre os 14 dias.
  - Segmento-herói (`cobranca`/`whatsapp`/`negociacao_divida`) tem ≥20 conversas na janela degradada.
  - Existe ≥1 segmento com <20 conversas na janela degradada.
  - Nenhuma `Conversa` do fixture tem CPF não-mascarado.

---

## Implementation Sequence

Cada passo deve virar um commit coeso (Conventional Commits, em PT-BR — regra `git.md`).

1. **Bootstrap do projeto** (`chore`): `pyproject.toml` (uv) com deps diretas `pydantic`, `pydantic-ai`, `pydantic-settings` e dev `pytest`, `ruff`, `mypy`; `.python-version`; `.gitignore` (inclui `.env*`, `data/*.db`, `__pycache__`); `.env.example` (`GEMINI_API_KEY=`, `OPENROUTER_API_KEY=`, `LLM_PROVIDER=gemini`); `.pre-commit-config.yaml` (trailing-whitespace, end-of-file-fixer, check-merge-conflict, check-added-large-files, gitleaks, ruff, mypy); `.github/workflows/ci.yml` (lint → type-check → test, com `concurrency` e `permissions: contents: read`).
2. **`settings.py`** (`feat`): config de ambiente com `pydantic-settings` — chaves de API e `LLM_PROVIDER`.
3. **`modelos.py` + `test_modelos.py`** (`feat`): `Turno`, `Conversa`, `RoteiroConversa`, Literals e validadores.
4. **`taxonomia.py`** (`feat`): taxonomia de intenções, segmentos, janela de 14 dias, alvos de distribuição, spec da regressão plantada, `SEMENTE_ALEATORIA`.
5. **`sementes.py`** (`feat`): seeds PT-BR escritos à mão (2–3 por tipo de agente).
6. **`geracao.py` + `test_geracao.py`** (`feat`): pipeline Pydantic AI + Gemini, throttle, retry, montagem de `Conversa`, escrita do JSONL; CLI `python -m agent_score.data.geracao`.
7. **Rodar a geração** (`chore`): executar o comando e commitar `data/conversas.seed.jsonl`.
8. **`carregador.py` + `test_carregador.py`** (`feat`): loader JSONL → SQLite idempotente; CLI `python -m agent_score.data.carregador`.
9. **`test_fixture.py`** (`test`): teste de sanidade do fixture commitado.

---

## Conventions Applied (from CLAUDE.md + regras do usuário)

- **Stack:** Python 3.12+, uv (lockfile `uv.lock` versionado), Pydantic v2, Pydantic AI, SQLite via `sqlite3` stdlib.
- **LLM:** Gemini 2.5 Flash (AI Studio free tier) padrão; OpenRouter como fallback configurável. Chave por env var, nunca commitada.
- **Idioma:** identificadores de código, nomes de arquivo, comentários e commits em **Português-Brasil** (`.claude/rules/language.md` do projeto).
- **Data/hora:** `iniciada_em` em UTC, timezone-aware, ISO-8601 (`datetime.md`).
- **Segredos:** `.env` no `.gitignore`, `.env.example` commitado, gitleaks no pre-commit (`secrets.md`).
- **CI/CD:** `ci.yml` (lint → type-check → test), `permissions` mínimo, `concurrency` com cancel-in-progress (`ci-cd.md`).
- **Dependências:** todas as libs novas estão na stack do `CLAUDE.md`; lockfile commitado; sem ORM (minimalismo — `dependencies.md`).
- **Testes:** pytest, `*_test`/`test_*` em `tests/` espelhando `src/`; cobertura mínima happy path + erro + edge (`testing.md`).
- **Arquitetura:** feature-first — pacote `src/agent_score/data/` por domínio (`architecture.md` adaptado a Python).

---

## Ready to Code?

- [x] Arquitetura descrita com módulos e arquivos novos nomeados
- [x] Contratos (modelos Pydantic, formato JSONL, schema SQLite, CLI) em forma final
- [x] Data model com tipos, campos obrigatórios e validadores
- [x] Trade-offs não-triviais com alternativa rejeitada documentada
- [x] Riscos conhecidos listados com mitigação
- [x] Plano de testes cobre happy path + ≥2 casos de erro
- [x] Sequência de implementação executável sem perguntas
- [x] Nenhuma lib nova fora da stack já decidida no `CLAUDE.md`
- [x] Convenções do `CLAUDE.md` e regras do usuário citadas e respeitadas
