from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserStock(Base):
    __tablename__ = "user_stocks"

    stock_symbol: Mapped[str] = mapped_column(primary_key=True)
    amount: Mapped[int] = mapped_column(nullable=False)
