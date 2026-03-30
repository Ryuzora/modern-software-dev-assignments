from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import asc, desc, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import ActionItem
from ..schemas import (
    ActionItemCreate,
    ActionItemPatch,
    ActionItemRead,
    ActionItemsBatchSetCompletedRequest,
    ActionItemsBatchSetCompletedResponse,
)

router = APIRouter(prefix="/action-items", tags=["action_items"])


@router.get("/", response_model=list[ActionItemRead])
def list_items(
    db: Session = Depends(get_db),
    completed: Optional[bool] = None,
    skip: int = 0,
    limit: int = Query(50, le=200),
    sort: str = Query("-created_at"),
) -> list[ActionItemRead]:
    stmt = select(ActionItem)
    if completed is not None:
        stmt = stmt.where(ActionItem.completed.is_(completed))

    sort_field = sort.lstrip("-")
    order_fn = desc if sort.startswith("-") else asc
    if hasattr(ActionItem, sort_field):
        stmt = stmt.order_by(order_fn(getattr(ActionItem, sort_field)))
    else:
        stmt = stmt.order_by(desc(ActionItem.created_at))

    rows = db.execute(stmt.offset(skip).limit(limit)).scalars().all()
    return [ActionItemRead.model_validate(row) for row in rows]


@router.post("/", response_model=ActionItemRead, status_code=201)
def create_item(payload: ActionItemCreate, db: Session = Depends(get_db)) -> ActionItemRead:
    item = ActionItem(description=payload.description, completed=False)
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.put("/{item_id}/complete", response_model=ActionItemRead)
def complete_item(item_id: int, db: Session = Depends(get_db)) -> ActionItemRead:
    item = db.get(ActionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    item.completed = True
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.patch("/{item_id}", response_model=ActionItemRead)
def patch_item(item_id: int, payload: ActionItemPatch, db: Session = Depends(get_db)) -> ActionItemRead:
    item = db.get(ActionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    if payload.description is not None:
        item.description = payload.description
    if payload.completed is not None:
        item.completed = payload.completed
    db.add(item)
    db.flush()
    db.refresh(item)
    return ActionItemRead.model_validate(item)


@router.post("/batch-set-completed", response_model=ActionItemsBatchSetCompletedResponse)
def batch_set_completed(
    payload: ActionItemsBatchSetCompletedRequest, db: Session = Depends(get_db)
) -> ActionItemsBatchSetCompletedResponse:
    try:
        rows = db.execute(select(ActionItem).where(ActionItem.id.in_(payload.item_ids))).scalars().all()
        found_ids = {row.id for row in rows}
        missing_ids = [item_id for item_id in payload.item_ids if item_id not in found_ids]
        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Action items not found for ids: {missing_ids}",
            )

        for row in rows:
            row.completed = payload.completed
            db.add(row)
        db.flush()

        ordered_items = sorted(rows, key=lambda item: payload.item_ids.index(item.id))
        return ActionItemsBatchSetCompletedResponse(
            updated_count=len(ordered_items),
            items=[ActionItemRead.model_validate(item) for item in ordered_items],
        )
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Failed to update action items") from exc


