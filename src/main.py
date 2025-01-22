from fastapi import FastAPI
from typing import List, Dict, Any
from models import HeatmapRequest, HeatmapResponse
from db import get_db, calculate_frequencies

app = FastAPI(title="Kilterboard Heatmap API")

@app.post("/api/v1/heatmap", response_model=HeatmapResponse)
async def get_heatmap(request: HeatmapRequest) -> HeatmapResponse:
    db = get_db()
    try:
        holds, metadata = calculate_frequencies(
            db,
            request.min_grade,
            request.max_grade,
            request.angle,
            request.hold_type,
            request.min_ascents
        )
        return HeatmapResponse(holds=holds, metadata=metadata)
    finally:
        db.close()

@app.get("/api/v1/angles")
async def get_angles() -> List[int]:
    """Get all available angles"""
    db = get_db()
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT DISTINCT angle 
            FROM climb_stats 
            WHERE angle IS NOT NULL 
            ORDER BY angle
        """)
        return [row['angle'] for row in cursor.fetchall()]
    finally:
        db.close()

@app.get("/api/v1/grades")
async def get_grades() -> List[Dict[str, Any]]:
    """Get grade mapping information"""
    db = get_db()
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT difficulty, boulder_name, route_name
            FROM difficulty_grades
            WHERE is_listed = 1
            ORDER BY difficulty
        """)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        db.close()