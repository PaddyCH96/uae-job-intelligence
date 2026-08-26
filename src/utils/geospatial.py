"""Geospatial insights for UAE job distribution.

Provides district-level analysis and interactive mapping.
"""

from typing import Dict, List, Optional

import structlog

logger = structlog.get_logger()

# UAE Districts/Areas mapping
UAE_DISTRICTS = {
    'Dubai': [
        'Dubai Marina', 'Downtown Dubai', 'Business Bay', 'DIFC',
        'Jumeirah Lake Towers', 'Palm Jumeirah', 'Dubai Silicon Oasis',
        'Dubai Internet City', 'Dubai Media City', 'Al Barsha',
        'Deira', 'Bur Dubai', 'Jumeirah', 'Al Quoz', 'Dubai Investment Park'
    ],
    'Abu Dhabi': [
        'Abu Dhabi Island', 'Al Maryah Island', 'Saadiyat Island',
        'Yas Island', 'Al Raha', 'Khalifa City', 'Mohammed Bin Zayed City',
        'Al Nahyan', 'Al Mushrif', 'Tourist Club Area'
    ],
    'Sharjah': [
        'Sharjah City', 'Al Nahda', 'Al Majaz', 'Al Qasimia',
        'University City', 'Sharjah Industrial Area'
    ],
    'Ajman': [
        'Ajman City', 'Al Nuaimiya', 'Al Jurf'
    ],
    'Ras Al Khaimah': [
        'RAK City', 'Al Hamra Village'
    ],
    'Fujairah': [
        'Fujairah City', 'Dibba'
    ],
    'Umm Al Quwain': [
        'UAQ City'
    ],
    'Al Ain': [
        'Al Ain City', 'Al Jimi', 'Al Muwaiji', 'Zakher'
    ]
}


def extract_district_from_location(location: str) -> Optional[str]:
    """
    Extract district name from job location string.
    
    Uses pattern matching to identify known districts.
    """
    if not location:
        return None
    
    location_lower = location.lower()
    
    # Check all known districts
    for city, districts in UAE_DISTRICTS.items():
        for district in districts:
            if district.lower() in location_lower:
                return district
    
    # Check city names
    for city in UAE_DISTRICTS.keys():
        if city.lower() in location_lower:
            return city
    
    return None


def get_district_coordinates(district: str) -> Optional[Dict]:
    """
    Get approximate coordinates for a district.
    
    Returns dict with 'lat' and 'lng' keys.
    """
    coordinates = {
        'Dubai Marina': {'lat': 25.0800, 'lng': 55.1340},
        'Downtown Dubai': {'lat': 25.1972, 'lng': 55.2744},
        'Business Bay': {'lat': 25.1856, 'lng': 55.2644},
        'DIFC': {'lat': 25.2131, 'lng': 55.2797},
        'Palm Jumeirah': {'lat': 25.1124, 'lng': 55.1389},
        'Dubai Silicon Oasis': {'lat': 25.1090, 'lng': 55.3770},
        'Abu Dhabi Island': {'lat': 24.4539, 'lng': 54.3773},
        'Al Maryah Island': {'lat': 24.4983, 'lng': 54.3713},
        'Sharjah City': {'lat': 25.3463, 'lng': 55.4209},
        'Al Ain City': {'lat': 24.1917, 'lng': 55.8044},
    }
    
    return coordinates.get(district)


class GeoDistributionAnalyzer:
    """Analyze job distribution across UAE districts."""
    
    def __init__(self, db_session):
        self.db_session = db_session
        
    def get_district_job_counts(self) -> List[Dict]:
        """Get job counts by district."""
        query = """
        SELECT 
            COALESCE(district, 'Unknown') as district,
            city,
            COUNT(*) as job_count,
            COUNT(CASE WHEN posted_date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as recent_count
        FROM analytics.fact_job_posting fjp
        LEFT JOIN analytics.dim_location dl ON fjp.location_id = dl.location_id
        WHERE fjp.is_active = TRUE
        GROUP BY district, city
        ORDER BY job_count DESC
        """
        
        result = self.db_session.execute(query)
        districts = []
        for row in result:
            districts.append({
                'district': row[0],
                'city': row[1],
                'job_count': row[2],
                'recent_count': row[3]
            })
        return districts
    
    def get_salary_by_district(self) -> List[Dict]:
        """Get average salary by district."""
        query = """
        SELECT 
            COALESCE(district, 'Unknown') as district,
            ROUND(AVG((salary_min + salary_max) / 2)::numeric, 0) as avg_salary,
            COUNT(*) as sample_size
        FROM analytics.fact_job_posting fjp
        LEFT JOIN analytics.dim_location dl ON fjp.location_id = dl.location_id
        WHERE fjp.is_active = TRUE
          AND salary_min IS NOT NULL
          AND salary_max IS NOT NULL
        GROUP BY district
        HAVING COUNT(*) >= 2
        ORDER BY avg_salary DESC
        """
        
        result = self.db_session.execute(query)
        salaries = []
        for row in result:
            salaries.append({
                'district': row[0],
                'avg_salary': float(row[1]),
                'sample_size': row[2]
            })
        return salaries