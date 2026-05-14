"""Configuração de ambiente via pydantic-settings."""

from pydantic_settings import BaseSettings


class Configuracoes(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    llm_provider: str = "gemini"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


configuracoes = Configuracoes()
