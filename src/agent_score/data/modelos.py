"""Modelos Pydantic para conversas e turnos."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

TipoAgente = Literal["suporte", "cobranca", "retencao"]
Canal = Literal["voz", "whatsapp"]
SegmentoCliente = Literal["individual", "empresarial", "adesao"]
Autor = Literal["cliente", "agente"]
Intencao = Literal[
    # suporte
    "duvida_produto",
    "problema_tecnico",
    "status_pedido",
    "reclamacao",
    # cobranca
    "negociacao_divida",
    "segunda_via_boleto",
    "contestacao_cobranca",
    "promessa_pagamento",
    # retencao
    "pedido_cancelamento",
    "downgrade_plano",
    "insatisfacao_preco",
    "oferta_retencao",
]

# Mapeamento de intenções por tipo de agente
INTENCOES_POR_AGENTE: dict[TipoAgente, set[Intencao]] = {
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


class Turno(BaseModel):
    """Um turno da conversa."""

    indice: int
    autor: Autor
    texto: str

    @field_validator("texto")
    @classmethod
    def validar_texto_nao_vazio(cls, v: str) -> str:
        """Valida que o texto não é vazio após strip."""
        texto_limpo = v.strip()
        if not texto_limpo:
            raise ValueError("texto não pode ser vazio")
        return texto_limpo

    @field_validator("texto")
    @classmethod
    def validar_cpf_nao_mascarado(cls, v: str) -> str:
        """Valida que não há CPF não-mascarado no texto."""
        import re

        # Padrão de CPF não-mascarado: \d{3}\.\d{3}\.\d{3}-\d{2}
        if re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", v):
            raise ValueError(
                "texto contém CPF não-mascarado (deve estar em formato mascarado)"
            )
        return v


class Conversa(BaseModel):
    """Uma conversa completa com metadados e turnos."""

    id: str
    tipo_agente: TipoAgente
    canal: Canal
    intencao: Intencao
    segmento_cliente: SegmentoCliente
    iniciada_em: datetime
    turnos: list[Turno]

    @field_validator("iniciada_em")
    @classmethod
    def validar_iniciada_em_timezone_aware(cls, v: datetime) -> datetime:
        """Valida que iniciada_em é timezone-aware (UTC)."""
        if v.tzinfo is None:
            raise ValueError("iniciada_em deve ser timezone-aware (UTC)")
        return v

    @model_validator(mode="after")
    def validar_intencao_coerente(self) -> "Conversa":
        """Valida que intencao é coerente com tipo_agente."""
        intencoes_validas = INTENCOES_POR_AGENTE[self.tipo_agente]
        if self.intencao not in intencoes_validas:
            raise ValueError(
                f"intencao '{self.intencao}' não é válida para agente '{self.tipo_agente}'"
            )
        return self

    @model_validator(mode="after")
    def validar_turnos(self) -> "Conversa":
        """Valida turnos: >=4, começa em cliente, alterna autor."""
        if len(self.turnos) < 4:
            raise ValueError("conversa deve ter pelo menos 4 turnos")

        if not self.turnos or self.turnos[0].autor != "cliente":
            raise ValueError("conversa deve começar com turno do cliente")

        for i, turno in enumerate(self.turnos):
            if turno.indice != i:
                raise ValueError(f"turnos devem ser sequenciais; turno {i} tem indice {turno.indice}")

        for i in range(1, len(self.turnos)):
            if self.turnos[i].autor == self.turnos[i - 1].autor:
                raise ValueError(f"turnos devem alternar autor; turnos {i-1} e {i} têm mesmo autor")

        return self


class RoteiroConversa(BaseModel):
    """Saída do LLM — só os turnos. A metadata é atribuída pelo pipeline."""

    turnos: list[Turno]
