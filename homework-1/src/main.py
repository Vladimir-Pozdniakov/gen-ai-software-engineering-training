from fastapi import FastAPI

from src.errors import register_exception_handlers
from src.routes import accounts, transactions

app = FastAPI(title="Banking Transactions API", version="0.1.0")
register_exception_handlers(app)
app.include_router(transactions.router)
app.include_router(accounts.router)
