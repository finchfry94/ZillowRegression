from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from starlette import status

from app import models
from app.api import deps
from app.core.config import settings

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/example", response_model=Any)
def example() -> Any:
    """
    Example endpoint to demonstrate a simple task.
    This can be replaced with actual task logic.
    """
    from app.tasks import example_task
    # Call the example task
    result = example_task.delay(x=10, y=20)
    print("Task ID:", result.id)  # Log the task ID for reference
    # Wait for the result to be ready
    return result.task_id

@router.get("/url", response_model=str)
def get_html_from_url(
    url: str,
    db: Session = Depends(deps.get_db)
) -> str:


    from app.tasks import get_html_from_url as fetch_html_task
    result = fetch_html_task.delay(url)

    # Wait for the result to be ready
    html_content = result.get(timeout=10)
    if not html_content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch HTML content from the URL."
        )
    # Return the HTML content as a response
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)