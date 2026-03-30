from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteRead(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotePatch(BaseModel):
    title: str | None = None
    content: str | None = None


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class TagRead(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TagPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)


class ActionItemCreate(BaseModel):
    description: str
    tag_ids: list[int] = Field(default_factory=list)


class ActionItemRead(BaseModel):
    id: int
    description: str
    completed: bool
    created_at: datetime
    updated_at: datetime
    tags: list[TagRead] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ActionItemPatch(BaseModel):
    description: str | None = None
    completed: bool | None = None
    # When set (including []), replaces the full tag set for this item.
    tag_ids: list[int] | None = None


class ActionItemsBatchSetCompletedRequest(BaseModel):
    item_ids: list[int] = Field(min_length=1, max_length=200)
    completed: bool

    @field_validator("item_ids")
    @classmethod
    def ensure_positive_unique_ids(cls, value: list[int]) -> list[int]:
        if any(item_id <= 0 for item_id in value):
            raise ValueError("item_ids must contain only positive integers")
        if len(set(value)) != len(value):
            raise ValueError("item_ids must not contain duplicates")
        return value


class ActionItemsBatchSetCompletedResponse(BaseModel):
    updated_count: int
    items: list[ActionItemRead]


class NotesStatsRead(BaseModel):
    total_notes: int
    total_characters: int
    average_characters: float
    longest_note_title: str | None = None
    shortest_note_title: str | None = None
