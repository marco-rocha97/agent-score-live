# Plan: Agent Score Live

> Reference SPEC: [`docs/specs/agent-score-live.md`](../specs/agent-score-live.md)
> This plan breaks the SPEC into **independent tasks**, each ready to become a dedicated Tech Spec.
> There is **no** stack, schema, architecture, or estimation here — only behavior and sequencing.

---

## Target Outcome

- **Anchor result (do SPEC):** O ciclo completo de qualidade é navegável de ponta a ponta em menos de 4 minutos — um revisor percorre as 5 telas em dados sintéticos plausíveis e segue um caso ilustrativo de queda de qualidade → causa-raiz → recomendação → iteração aplicada → comparação pré/pós, com todas as telas funcionais.
- **MVP deste plano:** Todas as tasks (T01–T11). O build de 3 dias inteiro **é** o MVP — não há "fase 2" dentro deste plano. As 5 telas funcionais (Overview, Drill-down, Iterations, Cliente, QBR) + o mock estático da meta-visão fecham o anchor result.
- **Later phases:** Tudo que está no "Out of Scope" do SPEC — multi-tenant, autenticação real/SSO/RBAC, integrações de produção (CRM/ERP/telefonia), meta-visão de portfólio como feature viva, alertas via Slack/email/WhatsApp, workflow de aprovação humana de iterações, A/B de versões de agente, benchmarking entre clientes, detecção de anomalias avançada, conformidade WCAG 2.1 AA completa.

---

## Task Map

| #   | Task | Covers (SPEC) | Depends on | Phase | Status |
|-----|------|---------------|------------|-------|--------|
| T01 | Base de conversas (dataset Kaggle ou sintético) | Feature "Conversation ingestion and scoring" — cenário "batch loaded" (lado dados) | — | MVP | pending |
| T02 | Motor de score (5 dimensões + explicabilidade por turno) | Feature "Conversation ingestion and scoring" — cenários "batch scored" + "explainable to the turn" (lado dados) | T01 | MVP | pending |
| T03 | Tela Overview (KPIs, tendência, distribuição, filtros) | Feature "Dashboard and drop detection" — "FDE sees trend" + "FDE filters" | T02 | MVP | pending |
| T04 | Detecção de queda + pontos de atenção | Feature "Dashboard and drop detection" — "relevant drop raises an alert" + "thin segment hypothesis" | T02 | MVP | pending |
| T05 | Drill-down de conversas + timeline por turno | Feature "Conversation ingestion and scoring" — "explainable to the turn" (lado UI) | T02 | MVP | pending |
| T06 | Análise de causa-raiz | Feature "Root cause and recommendation" — "dominant pattern" + "no dominance threshold" | T04 | MVP | pending |
| T07 | Recomendação + tarefa rastreada + falso positivo | Feature "Root cause and recommendation" — "accepts recommendation" + "marks false positive" | T06 | MVP | pending |
| T08 | Acompanhamento pré/pós de iteração + tela Iterations | Feature "Iteration pre/post tracking" — "marks an iteration as applied" | T07 | MVP | pending |
| T09 | Tela do Cliente (3 cards, read-only) | Feature "Client screen" — "read-only view" + "no unaccompanied bad news" | T02, T04 | MVP | pending |
| T10 | Resumo executivo de QBR (geração + estados + PDF) | Feature "QBR executive summary" — "generates summary" + "generation fails" | T02 | MVP | pending |
| T11 | Meta-visão de portfólio do CRO (mock estático) | User story do Daniel (CRO) | — | MVP | pending |

> Ordem sugerida: **T01 → T02 → (T03, T04, T05 em paralelo) → T06 → T07 → T08**; **T09** depois de T04; **T10** depois de T02; **T11** a qualquer momento.

---

## Task Details

### T01 — Base de conversas (dataset Kaggle ou sintético)

- **Behavior delivered:** Existe um conjunto de 100–200 conversas, no formato necessário para scoring e drill-down, pronto para ser carregado.
- **Stories/behaviors covered in SPEC:** Feature "Conversation ingestion and scoring" — cenário "A batch of synthetic conversations is loaded and scored" (parte de dados/ingestão).
- **Acceptance criteria:**
  - Dado que se busca um dataset no Kaggle, quando nenhum atende ao formato exigido, então conversas sintéticas são geradas como fallback.
  - As conversas cobrem 3 agentes (Support, Collections, Retention), 2 canais (Voice, WhatsApp), distribuídas em 7 dias simulados.
  - Cada conversa tem estrutura por turno (turnos individualmente identificáveis), pré-requisito para a explicabilidade por turno.
- **Depends on:** —
- **Pending assumptions that may block:** A fonte de dados (dataset do Kaggle vs. geração sintética) será decidida durante a task — o usuário tentará o Kaggle primeiro. PII assumida mascarada upstream; o MVP não mascara — registrar como suposição documentada.
- **Tech Spec:** pending
- **Negotiation notes:** Separado do motor de score (decisão do usuário) justamente porque a fonte de dados está incerta — isolar a incerteza numa task mantém o motor de score independente da origem dos dados.

### T02 — Motor de score (5 dimensões + explicabilidade por turno)

- **Behavior delivered:** Toda conversa carregada recebe score 0–100 nas 5 dimensões, um score consolidado e justificativas rastreáveis até o turno.
- **Stories/behaviors covered in SPEC:** Feature "Conversation ingestion and scoring" — cenário "A batch ... is loaded and scored" (parte de scoring) + cenário "Score is explainable down to the turn" (produção dos dados por turno).
- **Acceptance criteria:**
  - Cada conversa tem score 0–100 em cada uma das 5 dimensões (Resolution, Guardrail Adherence, Clarity & Context, Customer Sentiment, Efficiency).
  - Cada conversa tem um score consolidado = média ponderada das dimensões.
  - Cada score de dimensão expõe 2–4 sub-sinais e uma justificativa textual referenciando um turno específico.
  - Cada turno carrega o score por dimensão e a razão correspondente — os dados que alimentam a timeline da T05.
- **Depends on:** T01
- **Pending assumptions that may block:** Os pesos das dimensões vivem em arquivo de configuração, nunca na UI (princípio "opinionated, not configurable" do SPEC).
- **Tech Spec:** pending

### T03 — Tela Overview (KPIs, tendência, distribuição, filtros)

- **Behavior delivered:** A FDE abre o painel e vê de imediato a tendência semanal de qualidade da conta, com KPIs, distribuição por segmento e filtros.
- **Stories/behaviors covered in SPEC:** Feature "Dashboard and drop detection" — cenários "FDE sees the account quality trend" e "FDE filters the view"; user story da Ana ("ver a tendência semanal de qualidade").
- **Acceptance criteria:**
  - Os KPIs do topo mostram Score médio (semana), delta vs. semana anterior, conversas analisadas e alertas ativos.
  - Uma linha de tendência semanal mostra o Score consolidado e os scores por dimensão.
  - Barras de distribuição quebram o Score por agente, canal e intenção.
  - Ao aplicar filtros (janela de tempo, agente, canal, intenção, segmento de cliente), todos os KPIs, a linha de tendência, as barras de distribuição e a lista de atenção atualizam para o conjunto filtrado.
  - Um filtro sem resultados mostra a mensagem "nenhuma conversa corresponde a estes filtros".
- **Depends on:** T02
- **Negotiation notes:** Mantida separada da T04 (decisão do usuário) — esta task é a apresentação (a tela); a T04 é a lógica analítica de queda. A Overview renderiza a lista de "pontos de atenção" produzida pela T04.

### T04 — Detecção de queda + pontos de atenção

- **Behavior delivered:** O sistema detecta quedas relevantes de qualidade, atribui cada queda ao segmento mais específico possível e rotula quedas com pouco dado como hipótese.
- **Stories/behaviors covered in SPEC:** Feature "Dashboard and drop detection" — cenários "A relevant drop raises an alert" e "Drop in a thin segment is surfaced as a limited-data hypothesis"; user story da Ana ("ver uma queda mesmo em segmento pequeno, rotulada como hipótese").
- **Acceptance criteria:**
  - Dada uma dimensão cujo score caiu 5 ou mais pontos absolutos num segmento (janela móvel de 7 dias vs. os 7 dias anteriores), o segmento aparece na lista de "pontos de atenção" e um badge vermelho sutil aparece no topo.
  - O sistema atribui a queda ao segmento mais específico que conseguir (canal, agente ou intenção).
  - Uma queda num segmento com menos de 20 conversas ainda é exibida, mas visivelmente rotulada como hipótese de dado limitado, não como alerta confirmado.
- **Depends on:** T02

### T05 — Drill-down de conversas + timeline por turno

- **Behavior delivered:** A FDE abre uma conversa afetada e vê a timeline turno a turno, com o score por dimensão de cada turno e a evidência textual destacada.
- **Stories/behaviors covered in SPEC:** Feature "Conversation ingestion and scoring" — cenário "Score is explainable down to the turn" (lado de UI); user story da Ana ("drilar de um score caído para a dimensão e as conversas afetadas").
- **Acceptance criteria:**
  - A partir de uma dimensão/segmento, a FDE acessa a lista de conversas afetadas.
  - Ao abrir uma conversa, a timeline turno a turno mostra o score por dimensão de cada turno e a razão para ele (ex.: "context break at turn 4").
  - A evidência textual por trás de uma razão é destacada no turno.
- **Depends on:** T02

### T06 — Análise de causa-raiz

- **Behavior delivered:** A FDE abre a visão de causa-raiz e vê o padrão dominante (ou a hipótese principal) por trás de um conjunto de conversas de baixo score, com 3 exemplos representativos.
- **Stories/behaviors covered in SPEC:** Feature "Root cause and recommendation" — cenários "System identifies a dominant root-cause pattern" e "No attribute reaches the dominance threshold".
- **Acceptance criteria:**
  - Dado um conjunto de conversas de baixo score numa dimensão caída dentro de um segmento, o sistema mostra o padrão dominante — um atributo compartilhado (mesma intenção, canal, tipo de falha ou segmento de cliente) que cobre 60% ou mais das conversas afetadas — e apresenta 3 conversas-exemplo representativas.
  - Quando nenhum atributo atinge 60% de cobertura, o sistema mostra o atributo mais forte disponível como hipótese principal, visivelmente rotulado como hipótese, não como causa-raiz confirmada.
- **Depends on:** T04
- **Negotiation notes:** Mantida separada da T07 (decisão do usuário). Depende da T04 porque opera sobre as conversas afetadas que a detecção de queda identifica.

### T07 — Recomendação + tarefa rastreada + falso positivo

- **Behavior delivered:** A FDE aceita uma recomendação concreta como tarefa rastreada e pode marcar uma conversa como falso positivo.
- **Stories/behaviors covered in SPEC:** Feature "Root cause and recommendation" — cenários "FDE accepts a recommendation" e "FDE marks a false positive"; user stories da Ana ("iteração sugerida aceita como tarefa rastreada"; "marcar um score como falso positivo").
- **Acceptance criteria:**
  - Cada causa-raiz traz uma ação sugerida concreta (ex.: "adicionar fallback inline de coleta de CPF ao agente de Collections").
  - Ao aceitar a recomendação, uma tarefa rastreada é criada com status "accepted", um toast de confirmação informa que o pré/pós será acompanhado nos próximos 7 dias, e o sistema marca a janela de comparação pré/pós.
  - Ao marcar uma conversa como falso positivo, a conversa é sinalizada como falso positivo e a sinalização é retida como sinal.
- **Depends on:** T06
- **Negotiation notes:** O "marcar falso positivo" foi alocado aqui (decisão do usuário) por o SPEC agrupá-lo na Feature "Root cause and recommendation".

### T08 — Acompanhamento pré/pós de iteração + tela Iterations

- **Behavior delivered:** A FDE marca uma iteração aceita como "aplicada" e acompanha a comparação pré/pós para o segmento afetado na tela Iterations.
- **Stories/behaviors covered in SPEC:** Feature "Iteration pre/post tracking" — cenário "FDE marks an iteration as applied"; user story da Ana ("janela pré/pós quando aplico uma iteração").
- **Acceptance criteria:**
  - Ao marcar uma iteração aceita como "applied", o sistema começa a comparar os scores da janela pré e da janela pós para o segmento afetado.
  - A tela Iterations mostra o status da iteração e suas métricas pré/pós conforme elas acumulam.
- **Depends on:** T07

### T09 — Tela do Cliente (3 cards, read-only)

- **Behavior delivered:** O cliente abre um link read-only e, em ~30 segundos, lê três cards que respondem "estou ganhando dinheiro com isto e está melhorando ou piorando?".
- **Stories/behaviors covered in SPEC:** Feature "Client screen" — cenários "Client opens the read-only view" e "Client screen shows no unaccompanied bad news"; user story da Camila (CX Director).
- **Acceptance criteria:**
  - A tela mostra exatamente três cards — economia projetada acumulada (R$), Score médio com uma tendência simples, e pontos de atenção em linguagem simples ("Nenhum ponto crítico esta semana.").
  - Não há drill-down técnico disponível nesta tela.
  - Quando existe um ponto de atenção ativo, ele é mostrado junto da sua mitigação, nunca como um número negativo cru isolado.
- **Depends on:** T02, T04

### T10 — Resumo executivo de QBR (geração + estados + PDF)

- **Behavior delivered:** O CS seleciona um trimestre e gera um one-pager executivo, on-brand, exportável em PDF.
- **Stories/behaviors covered in SPEC:** Feature "QBR executive summary" — cenários "CS generates a quarterly summary" e "Summary generation fails"; user story do Bruno (CS).
- **Acceptance criteria:**
  - Ao acionar "Gerar resumo trimestral" com uma janela de trimestre selecionada, um estado de loading comunica que a geração está em progresso.
  - Ao concluir, é produzido um one-pager cobrindo evolução do Score, principais melhorias, casos de destaque, ROI estimado e próximas recomendações; o one-pager pode ser exportado como PDF.
  - Em caso de falha, um estado de erro explica o que deu errado e oferece retry; nenhum documento parcial ou corrompido é apresentado como final.
- **Depends on:** T02

### T11 — Meta-visão de portfólio do CRO (mock estático)

- **Behavior delivered:** O CRO abre a meta-visão de portfólio e vê, num relance, quais contas estão saudáveis e quais precisam de intervenção.
- **Stories/behaviors covered in SPEC:** User story do Daniel (CRO).
- **Acceptance criteria:**
  - A meta-visão é um mock estático (sem dados vivos) que mostra a saúde das contas do portfólio num relance.
- **Depends on:** —
- **Negotiation notes:** O SPEC define explicitamente esta tela como mock estático no MVP — a meta-visão de portfólio como feature viva é uma wave posterior (ver "Out of Scope" do SPEC).

---

## External Dependencies

Itens fora do repositório que podem bloquear uma ou mais tasks:

- [ ] Dataset adequado no Kaggle (3 agentes, 2 canais, 7 dias, estrutura por turno) — afeta **T01**. Não é bloqueante: o fallback é geração sintética.

---

## Out of This Plan

Itens do SPEC **deliberadamente diferidos** para waves posteriores (não há tasks para eles neste plano):

- Multi-account / multi-tenant — motivo: MVP é single-tenant, single-user.
- Autenticação real, SSO, RBAC — motivo: desnecessário para um demo single-user.
- Integrações de produção com CRM / ERP / telefonia — motivo: substituídas por dados sintéticos e mocks.
- Monitoramento ao vivo por chamada para supervisor humano — motivo: é outro produto.
- Agent Score de pré-produção / simulação — motivo: o Agent Score Live complementa, não substitui.
- QA manual de conversas com fila de revisão humana — motivo: sem fila de revisão no MVP.
- Dashboard de BI configurável — motivo: o produto é deliberadamente opinativo.
- Billing, pricing, contratos — motivo: não endereçado.
- Mascaramento / anonimização real de PII — motivo: assumido tratado upstream; documentado como suposição.
- Meta-visão de portfólio do CRO como feature viva — motivo: presente só como mock estático (T11); a versão viva é wave posterior.
- Alertas via Slack / email / WhatsApp — motivo: wave posterior.
- Workflow de aprovação humana de iterações com revisão — motivo: wave posterior; o MVP só permite aceitar a recomendação como tarefa rastreada.
- Comparação A/B automatizada de versões de agente — motivo: wave posterior.
- Benchmarking anônimo entre clientes da indústria — motivo: wave posterior.
- Detecção de anomalias avançada — motivo: wave posterior; o MVP usa as regras de threshold declaradas.
- Sugestão automática de novos casos de uso ainda não cobertos — motivo: wave posterior.
- Conformidade WCAG 2.1 AA completa — motivo: o MVP mira só a barra básica (navegação por teclado, status não só por cor, contraste sensato).

---

## Ready for Tech Spec?

- [x] Every task cites at least one story/behavior from the SPEC
- [x] Every task fits in one Tech Spec (no mega-tasks)
- [x] Dependencies are explicit and cycle-free
- [x] MVP is identified and closes the anchor result
- [x] Zero implementation details (no stack, schema, endpoint, infra)
- [x] SPEC out-of-scope is respected
- [x] External blocking dependencies are listed
