import uuid
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.environment.database import Base
from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer, Float


class MelonCloudCryptoPortfolios(Base):
    __tablename__ = "MelonCloud_Crypto_Portfolios"
    __bind_key__ = 'meloncloud'

    id = Column(UUID(as_uuid=True), primary_key=True, unique=True, nullable=False)
    coin_name = Column(Text, nullable=False)
    coin_symbol = Column(Text, nullable=False)
    portfolio_name = Column(Text, nullable=False)
    value = Column(Float, nullable=False)

    def __init__(self, coin_name, coin_symbol, portfolio_name, value):
        self.id = uuid.uuid4()
        self.coin_name = coin_name
        self.coin_symbol = coin_symbol
        self.portfolio_name = portfolio_name
        self.value = value

    @property
    def serialize(self):
        return {
            "name": self.coin_name,
            "symbol": self.coin_symbol,
            "portfolio": self.portfolio_name,
            "value": self.value
        }
