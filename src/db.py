import os
from dotenv import load_dotenv
from fastapi import HTTPException
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from .models import HoldType, HoldFrequency, ResponseMetadata
import sqlitecloud

load_dotenv()

def get_db():
    DB_HOST = os.getenv('SQLITE_CLOUD_HOST')
    DB_NAME = os.getenv('SQLITE_CLOUD_NAME')
    API_KEY = os.getenv('SQLITE_CLOUD_API_KEY')

    conn = sqlitecloud.connect(f"sqlitecloud://{DB_HOST}/{DB_NAME}?apikey={API_KEY}")
    conn.row_factory = sqlitecloud.Row
    return conn

def parse_frames(frames: str) -> List[Dict[str, Any]]:
    """
    Parse the frames string to extract hold information.
    Handles both standard format and potential corrupted data.
    
    Args:
        frames: String in format p1083r15p1117r15p1164r12...
        
    Returns:
        List of dicts containing hole_id and hold_type
    """
    holds = []
    try:
        # Clean the input string
        frames = frames.split('"')[0]  # Remove any trailing JSON-like content
        parts = frames.split('p')[1:]  # Skip empty first element
        
        for part in parts:
            if not part:
                continue
                
            # Handle potential corrupted data
            if 'r' not in part:
                continue
                
            # Split on 'r' and take only the first two elements
            components = part.split('r')
            if len(components) < 2:
                continue
                
            pos_str, role_str = components[0], components[1]
            
            # Clean and validate id and type
            try:
                hole_id = int(pos_str.strip())
                # Take only the numeric part of role
                role_id = int(''.join(c for c in role_str if c.isdigit()))
                
                # Validate reasonable ranges
                if 0 <= hole_id <= 2000 and 12 <= role_id <= 15:
                    holds.append({
                        'hole_id': hole_id,
                        'role': role_id
                    })
            except ValueError:
                continue  # Skip invalid entries
                
    except Exception as e:
        print(f"Error parsing frames: {e}")
        return []
        
    return holds

def get_hold_coordinates(db, hole_id: int) -> Tuple[int, int]:

    """Get x,y coordinates for a given LED position"""
    cursor = db.cursor()
    cursor.execute("""
        SELECT h.x, h.y
        FROM holes h
        WHERE h.id = ?
    """, (hole_id,))

    result = cursor.fetchone()
    return (result['x'], result['y']) if result else None

def calculate_frequencies(
    db,
    min_grade: float,
    max_grade: float,
    angle: int,
    hold_type: HoldType,
    min_ascents: int
) -> Tuple[List[HoldFrequency], Dict[str, Any]]:
    """Calculate hold frequencies based on the given criteria"""
    cursor = db.cursor()

    # Modified query to ensure frames is not null and has expected format
    cursor.execute("""
        WITH c AS (
            SELECT * FROM climbs
            WHERE layout_id = 1
        )
        SELECT c.name, c.frames, cs.ascensionist_count
        FROM c
            JOIN climb_stats cs ON c.uuid = cs.climb_uuid
        WHERE ROUND(cs.display_difficulty) BETWEEN ? AND ?
            AND cs.angle = ?
            AND cs.ascensionist_count >= ?
            AND c.is_listed = 1
            AND c.frames IS NOT NULL
        -- ORDER BY cs.ascensionist_count DESC -- Useful for debugging
    """, (min_grade, max_grade, angle, min_ascents))
    
    climbs = cursor.fetchall()
    
    if not climbs:
        raise HTTPException(status_code=404, detail="No climbs found matching criteria")
    
    # Count hold frequencies
    frequencies = defaultdict(int)
    total_climbs = len(climbs)
    invalid_frames = 0
    
    for climb in climbs:

        holds = parse_frames(climb['frames'])

        if not holds:
            invalid_frames += 1
            continue
            
        for hold in holds:

            coords = get_hold_coordinates(db, hold['hole_id'])

            if coords:
                # Filter holds based on role
                match hold_type:
                    case HoldType.ALL:
                        pass
                    case HoldType.HANDS if hold['role'] == 15:
                        continue
                    case HoldType.START if hold['role'] != 12:
                        continue
                    case HoldType.FINISH if hold['role'] != 14:
                        continue
                    case HoldType.FOOT if hold['role'] != 15:
                        continue
                frequencies[coords] += 1

    if not frequencies:
        raise HTTPException(
            status_code=404, 
            detail="No valid holds found in matching climbs"
        )

    # Normalize frequencies
    max_freq = max(frequencies.values())
    
    hold_frequencies = []
    for coords, count in frequencies.items():
        hold_frequencies.append(HoldFrequency(
            x=coords[0],
            y=coords[1],
            frequency=count,
            frequency_norm=count / max_freq,
        ))
    
    metadata = ResponseMetadata(
        min_grade = min_grade,
        max_grade = max_grade,
        angle = angle,
        hold_type = hold_type,
        total_climbs = total_climbs,
        invalid_climbs = invalid_frames,
        valid_climbs = total_climbs - invalid_frames,
        total_holds = len(hold_frequencies),
        max_frequency = max_freq,
        avg_frequency = sum(frequencies.values()) / len(frequencies)
    )
    
    return hold_frequencies, metadata