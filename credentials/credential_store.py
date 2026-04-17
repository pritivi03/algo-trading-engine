from dataclasses import dataclass

@dataclass
class CredentialStore:
    ALPACA_API_KEY: str
    ALPACA_SECRET_KEY: str