class Settings:
    DB_URL: str = "postgresql+asyncpg://root:hackpassword@db/hack"
    DB_ECHO: bool = False
    API_KEY_ID: str = "FDsjGYFDCvq9ZA1c"
    API_KEY_SECRET: str = "RiNHcpevbNolmAMW"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
