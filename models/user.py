from sqlalchemy import Column, BigInteger, String, DateTime, Boolean, Index
#
from sqlalchemy.ext.declarative import declarative_base
#
from start_utils import Base


class User(Base):
    __tablename__ = 'user'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    urn = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    is_logged_in = Column(Boolean, nullable=False, default=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    last_login = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    
    __table_args__ = (
        Index('idx_user_urn', 'urn'),
        Index('idx_user_email', 'email'),
        Index('idx_user_created_at', 'created_at'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"
