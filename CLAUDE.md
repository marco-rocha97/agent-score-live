# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

> Idioma: respostas, código, commits e documentação técnica deste projeto são em **Português-Brasil** (ver `.claude/rules/language.md`). Este arquivo segue a mesma regra; só o cabeçalho acima é fixo em inglês.

## O que é este repositório

Entrega de entrevista para a vaga de **Forward Deployed Engineer / AI Engineer Pleno (FDE)** na Khal.ai. O produto a construir é o **Agent Score Live** — uma *camada de observabilidade de produção* para agentes de IA: ela mede, explica e faz evoluir a qualidade de agentes **depois do go-live**, substituindo o relatório semanal que hoje o FDE monta à mão.

Limite de posicionamento (regra de negócio do SPEC): é uma camada de **observabilidade**, **não** uma ferramenta de construção de agentes — não deve duplicar nem parecer duplicar o Agent Builder da Khal.

## Estado atual

O repositório é **somente documentação** — ainda não há código nem arquivos de projeto (`pyproject.toml`, testes, CI). O que existe:

- `docs/specs/agent-score-live.md` — SPEC aprovado (problema, personas, comportamentos esperados, fora de escopo).
- `docs/plans/agent-score-live.md` — Plan aprovado: 11 tasks (T01–T11), todas no MVP, com dependências e ordem sugerida.

O próximo passo do fluxo é gerar uma **Tech Spec por task** e, a partir dela, código. Schema, prompts do LLM-as-judge e a divisão de scoring determinístico-vs-LLM são decididos **por task na Tech Spec** — o SPEC e o Plan não os contêm por design. A **stack abaixo** já é a baseline fixada para todo o deliverable.

## Stack

Escolha enxuta, alinhada à vaga (Python avançado, Pydantic/Pydantic AI, Linux server-side) e ao build de 3 dias — o esforço fica no motor de score e na lógica analítica, não em encanamento de frontend.

| Camada | Escolha | Por quê |
|---|---|---|
| Linguagem | **Python 3.12+** | Core da vaga; um runtime só para dados, scoring e UI. |
| Gerenciador de pacotes | **uv** | Rápido; lockfile (`uv.lock`) versionado. |
| Modelagem e validação | **Pydantic v2** | Conversa, Turno, Score, Iteração são modelos Pydantic — fronteira de dados tipada de ponta a ponta. |
| Framework de agentes | **Pydantic AI** | Saída estruturada validada por Pydantic, model-agnostic, integra nativamente com Logfire — e está no core da vaga. CrewAI/LangGraph seriam over-engineering: isto é um pipeline de LLM-as-judge, não agentes colaborando. |
| Provider de LLM | **Gemini 2.5 Flash** (AI Studio, free tier) padrão; **OpenRouter** como fallback configurável | Zero custo de API no build. No Pydantic AI o provider é uma linha de config — trocar Gemini↔OpenRouter não exige refactor. Chave por env var, nunca commitada. |
| Scoring | **LLM-as-judge + sub-sinais determinísticos** | Uma chamada por conversa retorna as 5 dimensões em saída estruturada; os sub-sinais objetivos ficam em Python puro, fora do LLM. |
| Otimização de token | **Rubrica compacta + batch throttled + caching implícito do Gemini** | Uma chamada para as 5 dimensões (não 5 chamadas); system prompt enxuto; o batch de scoring respeita o rate limit do free tier (≈1500 req/dia cobre re-scorings de 100–200 conversas). |
| Persistência | **SQLite** (`data/agent_score.db`) | Single-tenant, single-user (ver SPEC) — arquivo local, zero infra. |
| Frontend | **Streamlit** (multipage) | As 5 telas como pages; `st.toast`/`st.spinner` cobrem os estados do SPEC. O dashboard renderiza de dados **pré-scored** em cache (`@st.cache_data`), então o re-run do Streamlit não cai no caminho quente — não há scoring na interação. Python puro, sem build de JS. |
| Gráficos | **Plotly** | Linha de tendência e barras de distribuição da Overview. |
| Export PDF (QBR) | **WeasyPrint** (HTML → PDF) | One-pager renderizado de um template HTML on-brand. |
| Observabilidade | **Logfire** | Tracing do pipeline de scoring e das chamadas ao Claude — "diferencial" citado na vaga, integra nativamente com Pydantic AI. |
| Qualidade | **Ruff** (lint+format), **mypy** (tipos), **pytest** (testes) | Gate do `ci.yml`. |
| CI | **GitHub Actions** (`ci.yml`) | lint → type-check → test, conforme as regras globais de CI/CD. |

**Retrieval / vector DB / Graph RAG ficam de fora de propósito.** A vaga lista essas estratégias, mas o Agent Score Live é analítico, não conversacional — a causa-raiz (T06) agrupa conversas por atributo compartilhado, não busca semântica. Adicionar essa infra seria abstração especulativa.

Layout sugerido (a Tech Spec de cada task refina): `src/agent_score/` com submódulos por feature (`data/`, `scoring/`, `analytics/`, `iterations/`, `qbr/`) + `config.py` (pesos das dimensões, thresholds de queda); `src/app/` com as pages Streamlit; `tests/` espelhando `src/`.

## Fluxo de trabalho — spec-driven

O projeto segue um pipeline estrito de 4 etapas. **Pular uma etapa é anti-padrão.**

```
Briefing  → /spec      → docs/specs/<slug>.md
SPEC      → /plan      → docs/plans/<slug>.md
Task      → /tech-spec → docs/tech-specs/<slug>__<TASK_ID>.md
Tech Spec → /code      → handoff explícito ao agente coder → código + PR
```

Cada etapa tem uma responsabilidade fechada: o SPEC diz **qual problema / para quem / como sabemos que funcionou** (sem implementação); o Plan diz **quais tasks, em que ordem, o que é MVP** (sem stack); a Tech Spec diz **como implementar esta task, contratos, trade-offs**; o `/code` **executa a Tech Spec sem redefinir escopo**. Skills pensam junto com o usuário no contexto principal; agentes executam isolados.

## Arquitetura do produto (do SPEC/Plan)

Cinco telas funcionais + um mock estático fecham o MVP. O fluxo de dados encadeia as 11 tasks:

- **T01 — Base de conversas:** 100–200 conversas (dataset Kaggle ou geração sintética como fallback), 3 agentes (Support, Collections, Retention), 2 canais (Voice, WhatsApp), 7 dias simulados, **estrutura por turno** (pré-requisito da explicabilidade).
- **T02 — Motor de score:** cada conversa recebe score 0–100 nas **5 dimensões** (Resolution, Guardrail Adherence, Clarity & Context, Customer Sentiment, Efficiency), um score consolidado = média ponderada, e justificativa textual rastreável **até o turno**. Os pesos das dimensões vivem em **arquivo de configuração, nunca na UI**.
- **T03 — Tela Overview:** KPIs, linha de tendência semanal, barras de distribuição (agente/canal/intenção), filtros que atualizam tudo.
- **T04 — Detecção de queda:** dimensão que caiu ≥5 pontos absolutos num segmento (janela móvel 7d vs. 7d anteriores) vira "ponto de atenção"; atribui a queda ao segmento mais específico; segmento com <20 conversas é rotulado como **hipótese de dado limitado**.
- **T05 — Drill-down + timeline por turno:** conversas afetadas → timeline turno a turno com score por dimensão e evidência textual destacada.
- **T06 — Causa-raiz:** padrão dominante = atributo compartilhado que cobre ≥60% das conversas afetadas + 3 exemplos; sem 60%, mostra o atributo mais forte rotulado como **hipótese principal**.
- **T07 — Recomendação:** ação concreta sugerida → aceitar cria tarefa rastreada (status "accepted") + toast + janela pré/pós; marcar conversa como falso positivo retém o sinal.
- **T08 — Pré/pós de iteração + tela Iterations:** marcar iteração "applied" inicia a comparação pré/pós do segmento.
- **T09 — Tela do Cliente:** read-only, exatamente **3 cards** (economia projetada acumulada em R$, Score médio com tendência, pontos de atenção em linguagem simples). Sem drill-down técnico. Nunca má notícia crua sem mitigação ao lado.
- **T10 — Resumo executivo de QBR:** gera one-pager trimestral on-brand, exportável em PDF, com estados de loading e erro (ação genuinamente assíncrona).
- **T11 — Meta-visão do CRO:** **mock estático** no MVP (a versão viva é wave posterior).

Ordem sugerida: **T01 → T02 → (T03, T04, T05 em paralelo) → T06 → T07 → T08**; **T09** após T04; **T10** após T02; **T11** a qualquer momento.

## Princípios de produto não-negociáveis

Ao implementar qualquer tela, estes vêm do SPEC e não são opcionais:

- **Opinativo, não configurável.** O painel diz o que olhar; o usuário não monta a própria view. Pesos de dimensão em config, nunca na UI.
- **Explicabilidade obrigatória.** Nenhum score é exibido como número cru — sempre acompanha justificativa textual referenciando um turno.
- **Linguagem de negócio, não técnica.** "Aderência às regras de negócio", não "guardrail violation".
- **Cor semântica.** Verde/amarelo/vermelho só com critério explícito declarado, nunca decorativo — e **status nunca só por cor**: sempre pareado com ícone ou texto.
- **Gradiente de densidade.** Alta densidade nas telas internas (FDE); baixa na tela do Cliente.
- **A tela do Cliente é curada.** Sem má notícia desacompanhada de mitigação.

## Restrições do build

- **3 dias.** Dia 1: dados + motor de score + calibração. Dia 2: dashboard + drill-down + causa-raiz + recomendação + tela do Cliente. Dia 3: gerador de resumo + polish + script de demo + vídeo de backup + one-pager.
- **Métrica âncora (gate de "pronto"):** o ciclo completo de qualidade é navegável de ponta a ponta em **menos de 4 minutos** — as 5 telas funcionam em dados sintéticos plausíveis e um caso ilustrativo vai de queda → causa-raiz → recomendação → iteração aplicada → comparação pré/pós.
- **LGPD/PII:** o MVP **assume PII mascarada upstream** e não mascara — essa suposição deve ficar documentada.

## Fora de escopo (não construir)

Multi-tenant, autenticação real/SSO/RBAC, integrações de produção (CRM/ERP/telefonia — substituídas por dados sintéticos), monitoramento ao vivo por chamada, Agent Score de pré-produção, fila de revisão humana, dashboard de BI configurável, billing, mascaramento real de PII, meta-visão do CRO como feature viva, alertas via Slack/email/WhatsApp, aprovação humana de iterações, A/B de versões, benchmarking entre clientes, detecção de anomalias avançada, conformidade WCAG 2.1 AA completa (o MVP mira só a barra básica: navegação por teclado, status não só por cor, contraste sensato).
