"""
Address Service - Address lookup operations
"""
from typing import List, Dict, Any
from ..interfaces.database_port import DatabasePort


class AddressService:
    def __init__(self, db: DatabasePort):
        self.db = db
    
    def get_countries(self) -> List[str]:
        """Get list of unique countries"""
        rows = self.db.fetch_all("SELECT DISTINCT country FROM master_address ORDER BY country")
        return [row['country'] for row in rows]
    
    def get_provinces(self, country: str) -> List[str]:
        """Get list of provinces for a country"""
        rows = self.db.fetch_all(
            "SELECT DISTINCT province FROM master_address WHERE country = %s ORDER BY province",
            (country,)
        )
        return [row['province'] for row in rows]
    
    def get_districts(self, country: str, province: str) -> List[Dict[str, Any]]:
        """Get list of districts (with id) for country + province"""
        rows = self.db.fetch_all(
            """SELECT id, district FROM master_address 
               WHERE country = %s AND province = %s 
               ORDER BY district""",
            (country, province)
        )
        return [{"id": row['id'], "district": row['district']} for row in rows]
    
    def get_address_by_id(self, address_id: int) -> Dict[str, Any]:
        """Get full address by ID"""
        return self.db.fetch_one(
            "SELECT * FROM master_address WHERE id = %s", (address_id,)
        )
