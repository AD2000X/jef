from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pandas as pd
import numpy as np
from typing import List, Dict
import plotly.graph_objects as go
from fastapi.responses import JSONResponse

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load data
@app.on_event("startup")
async def startup_event():
    global df
    df = pd.read_excel("data/JEF.data.xlsx")
    df['age'] = pd.to_numeric(df['age'])
    df['est_IQ'] = pd.to_numeric(df['est_IQ'])

class AnalysisRequest(BaseModel):
    age_range: List[int]
    iq_range: List[int]
    scores: Dict[str, float]

@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    try:
        filtered_df = df[
            (df['age'].between(request.age_range[0], request.age_range[1])) &
            (df['est_IQ'].between(request.iq_range[0], request.iq_range[1]))
        ]

        means = filtered_df.iloc[:, :9].mean()
        stds = filtered_df.iloc[:, :9].std()

        # Calculate z-scores
        z_scores = (pd.Series(request.scores) - means) / stds

        # Create plot data
        plot_data = {
            'z_scores': z_scores.to_dict(),
            'n_samples': len(filtered_df),
            'age_range': request.age_range,
            'iq_range': request.iq_range
        }

        return JSONResponse(content=plot_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add root route to serve the frontend
@app.get("/")
async def root():
    return FileResponse("static/index.html")