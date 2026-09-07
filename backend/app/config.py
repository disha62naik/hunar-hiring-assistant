# from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     model_config = SettingsConfigDict(env_file=".env", extra="ignore")

#     database_url: str = "sqlite:///./hunar.db"
#     frontend_origin: str = "http://localhost:3000"
#     public_backend_url: str = "http://localhost:8000"

#     hunar_api_key: str = ""
#     hunar_base_url: str = "https://api.voice.hunar.ai/external/v1"
#     hunar_voice_persona: str = "NEHA"   # one of: NEHA, ROY, ZOE, SAM, MIRA, EESHA
#     hunar_language: str = "ENGLISH"
#     # Comma-separated list of active Hunar API keys used to sign webhooks.
#     # Defaults to just HUNAR_API_KEY -- only set this separately if your org
#     # has more than one active key and you want to trust all of them.
#     hunar_webhook_api_keys: str = ""

#     @property
#     def hunar_trusted_webhook_keys(self) -> list[str]:
#         extra = [k.strip() for k in self.hunar_webhook_api_keys.split(",") if k.strip()]
#         return list({self.hunar_api_key, *extra}) if self.hunar_api_key else extra

#     people_search_provider: str = "apollo"  # "apollo" or "pdl"
#     apollo_api_key: str = ""
#     pdl_api_key: str = ""

#     anthropic_api_key: str = ""


# settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./hunar.db"
    frontend_origin: str = "http://localhost:3000"
    public_backend_url: str = "http://localhost:8000"

    hunar_api_key: str = ""
    hunar_base_url: str = "https://api.voice.hunar.ai/external/v1"
    hunar_voice_persona: str = "NEHA"   # one of: NEHA, ROY, ZOE, SAM, MIRA, EESHA
    hunar_language: str = "ENGLISH"
    # Comma-separated list of active Hunar API keys used to sign webhooks.
    # Defaults to just HUNAR_API_KEY -- only set this separately if your org
    # has more than one active key and you want to trust all of them.
    hunar_webhook_api_keys: str = ""

    @property
    def hunar_trusted_webhook_keys(self) -> list[str]:
        extra = [k.strip() for k in self.hunar_webhook_api_keys.split(",") if k.strip()]
        return list({self.hunar_api_key, *extra}) if self.hunar_api_key else extra

    people_search_provider: str = "apollo"  # "apollo", "pdl", or "mock"
    apollo_api_key: str = ""
    pdl_api_key: str = ""
    # Your own real phone number in E.164 format, used by the "mock" people
    # search provider (see services/people_search.py) as a fallback when
    # you can't get an Apollo/PDL/Coresignal account approved in time.
    mock_test_phone_number: str = ""

    anthropic_api_key: str = ""


settings = Settings()