import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    supabase_url: str
    supabase_service_role_key: str
    request_timeout_seconds: float = 20.0
    request_delay_seconds: float = 2.0
    user_agent: str = "PersonalPriceTracker/0.1"
    whatsapp_api_version: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_recipient_number: str = ""
    whatsapp_template_name: str = "price_drop_alert"
    whatsapp_template_language: str = "id"

    @classmethod
    def from_env(cls) -> "Settings":
        url = os.getenv("SUPABASE_URL", "").rstrip("/")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured."
            )
        return cls(
            supabase_url=url,
            supabase_service_role_key=key,
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
            request_delay_seconds=float(os.getenv("REQUEST_DELAY_SECONDS", "2")),
            user_agent=os.getenv("USER_AGENT", "PersonalPriceTracker/0.1"),
            whatsapp_api_version=os.getenv("WHATSAPP_API_VERSION", ""),
            whatsapp_phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
            whatsapp_access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
            whatsapp_recipient_number=os.getenv("WHATSAPP_RECIPIENT_NUMBER", ""),
            whatsapp_template_name=os.getenv("WHATSAPP_TEMPLATE_NAME", "price_drop_alert"),
            whatsapp_template_language=os.getenv("WHATSAPP_TEMPLATE_LANGUAGE", "id"),
        )

    @property
    def whatsapp_enabled(self) -> bool:
        return all((
            self.whatsapp_api_version,
            self.whatsapp_phone_number_id,
            self.whatsapp_access_token,
            self.whatsapp_recipient_number,
        ))
