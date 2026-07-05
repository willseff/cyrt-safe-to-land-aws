from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .retrieve_data import retrieve_latest_forecast
from .inference import predict_from_grib2


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: pre-load the model into memory
    from .inference import get_model
    get_model()
    print("Model loaded and ready.")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Cyrt Safe-to-Land API",
    description="Weather landing prediction service (AWS)",
    version="0.1.0",
    lifespan=lifespan,
)


@app.post("/predict")
async def predict():
    """
    Retrieve the latest ECMWF forecast and return the landing probability.
    """
    try:
        grib2_data = retrieve_latest_forecast()
        probability = predict_from_grib2(grib2_data)
        return JSONResponse(
            content={
                "status": "ok",
                "landing_probability": round(probability, 4),
            },
            status_code=200,
        )
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500,
        )


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
