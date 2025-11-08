from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "orders-service"
    MONGO_URI: str = "mongodb://orders:orderspw@orders-mongo:27017"
    MONGO_DB: str = "ordersdb"
    CATALOG_BASE_URL: str = "http://catalog-service:8000"  # K8s service DNS

    class Config:
        env_file = ".env"

settings = Settings()
