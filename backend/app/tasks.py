from .worker import celery_app


@celery_app.task
def example_task(x, y):
    print(x,y)
    return x + y

@celery_app.task
def get_html_from_url(url: str):
    """
    Example task that fetches HTML content from a given URL.
    This is just a placeholder function for demonstration purposes.
    """
    import requests
    try:
        response = requests.get(url)
        return response.text
    except Exception as e:
        return str(e)