from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from dataclasses import dataclass

@dataclass
class HoldUsageConfig:
    min_grade: float
    max_grade: float
    angle: int
    hold_type: str  # 'all', 'hands', 'feet'

class KilterboardDataProcessor:
    def __init__(self, db_path: str):
        """Initialize the data processor with database connection.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.board_width = 12
        self.board_height = 12
        
    def get_hold_positions(self) -> pd.DataFrame:
        """Get all hold positions from the database."""
        query = """
        SELECT 
            h.id as hole_id,
            h.x,
            h.y,
            l.position as led_position
        FROM holes h
        JOIN leds l ON h.id = l.hole_id
        WHERE h.product_id = (
            SELECT id FROM products WHERE name LIKE '%Kilter%' LIMIT 1
        )
        """
        return pd.read_sql(query, self.engine)
    
    def get_climb_holds(self, config: HoldUsageConfig) -> pd.DataFrame:
        """Get hold usage data for climbs matching the criteria."""
        query = """
        SELECT 
            c.uuid,
            c.name,
            cs.display_difficulty,
            p.hole_id,
            pr.name as role_name
        FROM climbs c
        JOIN climb_stats cs ON c.uuid = cs.climb_uuid
        JOIN placements p ON c.layout_id = p.layout_id
        JOIN placement_roles pr ON p.default_placement_role_id = pr.id
        WHERE cs.angle = :angle
        AND cs.display_difficulty BETWEEN :min_grade AND :max_grade
        """
        
        # Add hold type filter if specified
        if config.hold_type == 'hands':
            query += " AND pr.name IN ('start', 'hand', 'finish')"
        elif config.hold_type == 'feet':
            query += " AND pr.name = 'foot'"
            
        params = {
            'angle': config.angle,
            'min_grade': config.min_grade,
            'max_grade': config.max_grade
        }
        
        return pd.read_sql(query, self.engine, params=params)
    
    def calculate_hold_frequencies(self, config: HoldUsageConfig) -> np.ndarray:
        """Calculate the frequency of hold usage for the given parameters.
        
        Returns:
            2D numpy array representing the heatmap data
        """
        # Get base hold positions
        holds_df = self.get_hold_positions()
        
        # Get climb hold usage data
        climbs_df = self.get_climb_holds(config)
        
        # Calculate frequency of each hold's usage
        hold_counts = climbs_df['hole_id'].value_counts()
        max_count = hold_counts.max()
        
        # Initialize heatmap array
        heatmap = np.zeros((self.board_height, self.board_width))
        
        # Fill heatmap with normalized frequencies
        for _, hold in holds_df.iterrows():
            x, y = int(hold['x']), int(hold['y'])
            count = hold_counts.get(hold['hole_id'], 0)
            if max_count > 0:  # Avoid division by zero
                heatmap[y, x] = count / max_count
                
        return heatmap
    
    def get_grade_range(self) -> Tuple[float, float]:
        """Get the minimum and maximum grades available in the database."""
        query = """
        SELECT 
            MIN(display_difficulty) as min_grade,
            MAX(display_difficulty) as max_grade
        FROM climb_stats
        """
        result = pd.read_sql(query, self.engine)
        return (result['min_grade'].iloc[0], result['max_grade'].iloc[0])
    
    def get_available_angles(self) -> List[int]:
        """Get list of angles that have climbs."""
        query = """
        SELECT DISTINCT angle 
        FROM climb_stats 
        WHERE angle IS NOT NULL 
        ORDER BY angle
        """
        result = pd.read_sql(query, self.engine)
        return result['angle'].tolist()
    
    def get_summary_stats(self, config: HoldUsageConfig) -> Dict:
        """Get summary statistics for the current filter configuration."""
        query = """
        SELECT 
            COUNT(DISTINCT c.uuid) as total_climbs,
            AVG(cs.quality_average) as avg_quality,
            COUNT(DISTINCT c.setter_id) as unique_setters
        FROM climbs c
        JOIN climb_stats cs ON c.uuid = cs.climb_uuid
        WHERE cs.angle = :angle
        AND cs.display_difficulty BETWEEN :min_grade AND :max_grade
        """
        
        params = {
            'angle': config.angle,
            'min_grade': config.min_grade,
            'max_grade': config.max_grade
        }
        
        result = pd.read_sql(query, self.engine, params=params)
        return result.iloc[0].to_dict()

def convert_grade_to_v_scale(difficulty: float) -> str:
    """Convert numeric difficulty to V-scale grade."""
    # This is a simplified conversion - you might want to adjust based on actual data
    v_grade = int(difficulty / 4)  # Assuming each V-grade spans 4 difficulty points
    return f"V{v_grade}"