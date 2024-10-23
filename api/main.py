from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import pandas as pd
import numpy as np
from typing import List, Dict
from supabase import create_client
import os

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Supabase 初始化
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

class AnalysisRequest(BaseModel):
    age_range: List[int]
    iq_range: List[int]
    scores: Dict[str, float]

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    try:
        # 从 Supabase 获取数据
        response = supabase.table('jef_data').select('*').execute()
        df = pd.DataFrame(response.data)
        
        filtered_df = df[
            (df['age'].between(request.age_range[0], request.age_range[1])) &
            (df['est_IQ'].between(request.iq_range[0], request.iq_range[1]))
        ]

        means = filtered_df.iloc[:, :9].mean()
        stds = filtered_df.iloc[:, :9].std()
        z_scores = (pd.Series(request.scores) - means) / stds

        return JSONResponse(content={
            'z_scores': z_scores.to_dict(),
            'n_samples': len(filtered_df),
            'age_range': request.age_range,
            'iq_range': request.iq_range
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
