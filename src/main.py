from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
from typing import List, Dict
from .data_processor import KilterboardDataProcessor, HoldUsageConfig
from . import convert_grade_to_v_scale

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize data processor
processor = KilterboardDataProcessor("path_to_your_database.db")

@app.get("/api/heatmap")
async def get_heatmap_data(
    min_grade: float = Query(..., description="Minimum grade difficulty"),
    max_grade: float = Query(..., description="Maximum grade difficulty"),
    angle: int = Query(..., description="Wall angle"),
    hold_type: str = Query("all", description="Type of holds to analyze")
) -> Dict:
    """Get heatmap data for the specified parameters."""
    config = HoldUsageConfig(
        min_grade=min_grade,
        max_grade=max_grade,
        angle=angle,
        hold_type=hold_type
    )
    
    # Calculate heatmap data
    heatmap_data = processor.calculate_hold_frequencies(config)
    
    # Get summary statistics
    stats = processor.get_summary_stats(config)
    
    return {
        "heatmap": heatmap_data.tolist(),
        "stats": stats,
        "config": {
            "min_grade": convert_grade_to_v_scale(min_grade),
            "max_grade": convert_grade_to_v_scale(max_grade),
            "angle": angle,
            "hold_type": hold_type
        }
    }

@app.get("/api/metadata")
async def get_metadata() -> Dict:
    """Get available ranges and options for filtering."""
    min_grade, max_grade = processor.get_grade_range()
    angles = processor.get_available_angles()
    
    return {
        "grades": {
            "min": convert_grade_to_v_scale(min_grade),
            "max": convert_grade_to_v_scale(max_grade)
        },
        "angles": angles,
        "holdTypes": ["all", "hands", "feet"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)