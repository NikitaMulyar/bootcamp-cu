from sqlalchemy import String
from .base import Base
from sqlalchemy.orm import Mapped, mapped_column


class User(Base):
    email: Mapped[str] = mapped_column(String, unique=True)
    fio: Mapped[str] = mapped_column(String)
    experience: Mapped[str] = mapped_column(String)
    speciality: Mapped[str] = mapped_column(String)
    place: Mapped[str] = mapped_column(String)
    essay: Mapped[str] = mapped_column(String, nullable=True, default=None)
