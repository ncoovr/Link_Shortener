import uuid
from datetime import datetime, timezone
import boto3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl

app = FastAPI()

# Configuración de CORS para solicitudes desde el frontend en S3
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conexión a DynamoDB en us-east-1 usando el Rol IAM de la EC2
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
table = dynamodb.Table("UrlShortener")


class ShortenRequest(BaseModel):
    original_url: HttpUrl


@app.post("/shorten")
def shorten_url(payload: ShortenRequest):
    short_code = str(uuid.uuid4())
    original_url = str(payload.original_url)
    created_at = datetime.now(timezone.utc).isoformat()

    table.put_item(
        Item={
            "short_code": short_code,
            "original_url": original_url,
            "created_at": created_at,
        }
    )

    return {
        "short_code": short_code,
        "original_url": original_url,
        "created_at": created_at,
    }


@app.get("/{short_code}")
def redirect_to_url(short_code: str):
    response = table.get_item(Key={"short_code": short_code})
    item = response.get("Item")

    if not item:
        raise HTTPException(status_code=404, detail="URL no encontrada")

    return RedirectResponse(url=item["original_url"], status_code=307)


@app.get("/urls/{short_code}")
def get_url_info(short_code: str):
    response = table.get_item(Key={"short_code": short_code})
    item = response.get("Item")

    if not item:
        raise HTTPException(status_code=404, detail="URL no encontrada")

    return item


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
