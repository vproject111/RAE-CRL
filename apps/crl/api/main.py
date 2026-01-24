from fastapi import FastAPI

app = FastAPI(title="RAE-CRL API", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "rae-crl"}


@app.get("/")
async def root():
    return {"message": "Cognitive Research Loop API is running"}
