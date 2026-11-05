import os


class Settings:
    APP_NAME = "CRISPR-X Nexus"
    VERSION = "1.1.0"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    HEDERA_ENABLED = bool(os.getenv("HEDERA_ACCOUNT_ID") and os.getenv("HEDERA_PRIVATE_KEY"))


settings = Settings()
