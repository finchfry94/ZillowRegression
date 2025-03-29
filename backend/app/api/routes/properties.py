from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from starlette import status

from app import models
from app.api import deps
from app.core.config import settings

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("/", response_model=models.PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(
    *,
    db: Session = Depends(deps.get_db),
    property_in: models.PropertyCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Any:
    """
    Create new property.
    """
    property = models.Property.model_validate(property_in)
    db.add(property)
    db.commit()
    db.refresh(property)
    return property


@router.get("/", response_model=list[models.PropertyRead])
def read_properties(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Retrieve properties.
    """
    properties = db.exec(select(models.Property).offset(skip).limit(limit)).all()
    return properties


@router.get("/{property_id}", response_model=models.PropertyRead)
def read_property(
    *,
    db: Session = Depends(deps.get_db),
    property_id: str,
    current_user: models.User = Depends(deps.get_current_user),
) -> Any:
    """
    Get property by ID.
    """
    property = db.get(models.Property, property_id)
    if not property:
        raise HTTPException(status_code=404, detail="Property not found")
    return property


