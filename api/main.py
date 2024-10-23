# main.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
from typing import List, Dict
from supabase import create_client
import os

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Supabase initialization with error handling
try:
    supabase = create_client(
        "https://uxwzcwedgyrkclyusvxh.supabase.co",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV4d3pjd2VkZ3lya2NseXVzdnhoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mjk2NjA2MjgsImV4cCI6MjA0NTIzNjYyOH0.Rk2d3Jq4KMApZtXbCkt1RBMniFBEL1wgbfOqvojwFLU"
    )
except Exception as e:
    print(f"Supabase initialization error: {e}")
    supabase = None

class AnalysisRequest(BaseModel):
    age_range: List[int]
    iq_range: List[int]
    scores: Dict[str, float]

@app.get("/")
async def root():
    try:
        return FileResponse("static/index.html")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Database connection not initialized")
    
    try:
        response = supabase.table('jef_data').select('*').execute()
        
        if not response.data:
            return JSONResponse(content={
                'error': 'No data retrieved from database',
                'z_scores': {},
                'n_samples': 0,
                'age_range': [0, 0],
                'iq_range': [0, 0]
            })
            
        df = pd.DataFrame(response.data)
        
        filtered_df = df[
            (df['age'].between(request.age_range[0], request.age_range[1])) &
            (df['est_IQ'].between(request.iq_range[0], request.iq_range[1]))
        ]

        if len(filtered_df) == 0:
            return JSONResponse(content={
                'error': 'No data matches the specified criteria',
                'z_scores': {},
                'n_samples': 0,
                'age_range': request.age_range,
                'iq_range': request.iq_range
            })

        constructs = ["PL", "PR", "ST", "CT", "AT", "EBPM", "ABPM", "TBPM", "AVG"]
        
        means = filtered_df[constructs].mean()
        stds = filtered_df[constructs].std()

        z_scores = {}
        for construct in constructs:
            if construct in request.scores:
                if stds[construct] == 0:
                    z_scores[construct] = 0
                else:
                    z_scores[construct] = float((request.scores[construct] - means[construct]) / stds[construct])

        return JSONResponse(content={
            'z_scores': z_scores,
            'n_samples': len(filtered_df),
            'age_range': [float(min(filtered_df['age'])), float(max(filtered_df['age']))],
            'iq_range': [float(min(filtered_df['est_IQ'])), float(max(filtered_df['est_IQ']))]
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")
