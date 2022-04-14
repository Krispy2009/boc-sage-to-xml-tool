from fastapi import Request
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")


async def root(req: Request):
    return templates.TemplateResponse("index.html", {"request": req})
