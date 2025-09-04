from typing import List
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models.base import BaseModel
from app.models.trade import trade_tags


class Tag(BaseModel):
    __tablename__ = 'tag'

    name: so.Mapped[str] = so.mapped_column(sa.String(50), nullable=False)

    # Foreign key to user (one-to-many)
    user_id: so.Mapped[str] = so.mapped_column(sa.ForeignKey('user.id'), nullable=False)

    # Relationships
    user: so.Mapped["User"] = so.relationship(back_populates="tags")

    trades: so.Mapped[List["Trade"]] = so.relationship(secondary=trade_tags, back_populates="tags")

    # Unique constraint for user-tag combination (user cannot have duplicate tag names)
    __table_args__ = (sa.UniqueConstraint('name', 'user_id', name='unique_user_tag'),)

    def __repr__(self):
        return f"<Tag {self.name}>"

