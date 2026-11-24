from fastapi import FastAPI

from src.routes import accounts, transactions

app = FastAPI(title="Banking Transactions API", version="0.1.0")
app.include_router(transactions.router)
app.include_router(accounts.router)
