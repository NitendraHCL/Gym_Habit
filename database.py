"""
Gym Habit - Database Layer
Handles CSV operations and distance calculations
"""

import csv
import json
import math
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class GymDatabase:
    """Manages gym data from CSV file"""

    def __init__(self, csv_path: str = "gyms.csv"):
        self.csv_path = csv_path
        self.gyms: List[Dict] = []
        self.load_gyms()

    def load_gyms(self):
        """Load all gyms from CSV into memory"""
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                self.gyms = []
                for idx, row in enumerate(reader, start=1):
                    gym = {
                        'id': idx,
                        'partner_name': row['PartnerName'].strip(),
                        'gym_name': row['GymName'].strip(),
                        'address': row['Address'].strip(),
                        'pincode': row['Pincode'].strip(),
                        'latitude': float(row['Latitude']),
                        'longitude': float(row['Longitude']),
                        'subscription_amount': int(row['SubscriptionAmount']),
                        'amenities': row['Amenities'].strip()
                    }
                    self.gyms.append(gym)
            print(f"[OK] Loaded {len(self.gyms)} gyms from {self.csv_path}")
        except FileNotFoundError:
            print(f"[WARNING] CSV file not found: {self.csv_path}")
            self.gyms = []
        except Exception as e:
            print(f"[ERROR] Error loading CSV: {e}")
            self.gyms = []

    def get_all_partners(self) -> List[Dict[str, any]]:
        """
        Get unique list of partners with gym counts
        Returns: [{"name": "Cult", "count": 10}, ...]
        """
        partner_counts = {}
        for gym in self.gyms:
            partner = gym['partner_name']
            partner_counts[partner] = partner_counts.get(partner, 0) + 1

        partners = [
            {"name": name, "count": count}
            for name, count in sorted(partner_counts.items())
        ]
        return partners

    def get_gyms_by_partner(self, partner: str) -> List[Dict]:
        """
        Filter gyms by partner name
        Args:
            partner: Partner name (e.g., "Cult")
        Returns: List of gym dictionaries
        """
        if not partner:
            return self.gyms

        filtered = [
            gym for gym in self.gyms
            if gym['partner_name'].lower() == partner.lower()
        ]
        return filtered

    def get_gym_by_id(self, gym_id: int) -> Optional[Dict]:
        """
        Get single gym by ID
        Args:
            gym_id: Gym ID
        Returns: Gym dictionary or None
        """
        for gym in self.gyms:
            if gym['id'] == gym_id:
                return gym
        return None

    def get_nearby_gyms(
        self,
        user_lat: float,
        user_lon: float,
        partner: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find nearest gyms using Haversine distance
        Args:
            user_lat: User's latitude
            user_lon: User's longitude
            partner: Optional partner filter
            limit: Max number of results (default: 10)
        Returns: List of gyms sorted by distance
        """
        # Start with all gyms or filtered by partner
        gyms = self.get_gyms_by_partner(partner) if partner else self.gyms

        # Calculate distance for each gym
        gyms_with_distance = []
        for gym in gyms:
            distance = haversine_distance(
                user_lat, user_lon,
                gym['latitude'], gym['longitude']
            )
            gym_copy = gym.copy()
            gym_copy['distance'] = distance
            gyms_with_distance.append(gym_copy)

        # Sort by distance and limit results
        gyms_with_distance.sort(key=lambda x: x['distance'])
        return gyms_with_distance[:limit]

    def add_gym(self, gym_data: Dict) -> int:
        """
        Add new gym to database and CSV
        Args:
            gym_data: Dictionary with gym information
        Returns: New gym ID
        """
        # Generate new ID
        new_id = max([g['id'] for g in self.gyms], default=0) + 1

        # Create gym object
        new_gym = {
            'id': new_id,
            'partner_name': gym_data['partner_name'],
            'gym_name': gym_data['gym_name'],
            'address': gym_data['address'],
            'pincode': gym_data['pincode'],
            'latitude': float(gym_data['latitude']),
            'longitude': float(gym_data['longitude']),
            'subscription_amount': int(gym_data['subscription_amount']),
            'amenities': gym_data['amenities']
        }

        # Add to memory
        self.gyms.append(new_gym)

        # Save to CSV
        self._save_to_csv()

        return new_id

    def delete_gym(self, gym_id: int) -> bool:
        """
        Delete gym by ID
        Args:
            gym_id: Gym ID to delete
        Returns: True if deleted, False if not found
        """
        original_count = len(self.gyms)
        self.gyms = [g for g in self.gyms if g['id'] != gym_id]

        if len(self.gyms) < original_count:
            self._save_to_csv()
            return True
        return False

    def replace_all_gyms(self, new_csv_path: str) -> int:
        """
        Replace entire gym database with new CSV
        Args:
            new_csv_path: Path to new CSV file
        Returns: Number of gyms loaded
        """
        # Backup current CSV
        backup_path = f"{self.csv_path}.backup"
        try:
            Path(self.csv_path).replace(backup_path)
            print(f"[BACKUP] Backup created: {backup_path}")
        except:
            pass

        # Replace with new CSV
        Path(new_csv_path).replace(self.csv_path)

        # Reload gyms
        self.load_gyms()
        return len(self.gyms)

    def _save_to_csv(self):
        """Save current gyms to CSV file"""
        try:
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as file:
                fieldnames = [
                    'PartnerName', 'GymName', 'Address', 'Pincode',
                    'Latitude', 'Longitude', 'SubscriptionAmount', 'Amenities'
                ]
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()

                for gym in self.gyms:
                    writer.writerow({
                        'PartnerName': gym['partner_name'],
                        'GymName': gym['gym_name'],
                        'Address': gym['address'],
                        'Pincode': gym['pincode'],
                        'Latitude': gym['latitude'],
                        'Longitude': gym['longitude'],
                        'SubscriptionAmount': gym['subscription_amount'],
                        'Amenities': gym['amenities']
                    })
            print(f"[SAVED] Saved {len(self.gyms)} gyms to {self.csv_path}")
        except Exception as e:
            print(f"[ERROR] Error saving CSV: {e}")


class SubscriptionManager:
    """Manages subscription requests"""

    def __init__(self, json_path: str = "subscription_requests.json"):
        # Use /tmp for writable storage in serverless (Vercel)
        import os
        if os.environ.get('VERCEL'):
            self.json_path = f"/tmp/{Path(json_path).name}"
        else:
            self.json_path = json_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create JSON file if it doesn't exist"""
        if not Path(self.json_path).exists():
            with open(self.json_path, 'w') as file:
                json.dump({"requests": []}, file)

    def save_request(self, request_data: Dict) -> str:
        """
        Save subscription request
        Args:
            request_data: Dictionary with user info and gym details
        Returns: Request ID
        """
        # Load existing requests
        requests = self.get_all_requests()

        # Generate request ID
        date_str = datetime.now().strftime('%Y%m%d')
        request_count = len([r for r in requests if r['request_id'].startswith(f"REQ_{date_str}")]) + 1
        request_id = f"REQ_{date_str}_{request_count:03d}"

        # Create request object
        new_request = {
            'request_id': request_id,
            'timestamp': datetime.now().isoformat(),
            'gym_id': request_data['gym_id'],
            'gym_name': request_data['gym_name'],
            'partner_name': request_data['partner_name'],
            'full_name': request_data['full_name'],
            'email': request_data['email'],
            'phone': request_data['phone'],
            'preferred_plan': request_data['preferred_plan'],
            'billing_address': request_data.get('billing_address', ''),
            'message': request_data.get('message', ''),
            'user_latitude': request_data.get('user_latitude'),
            'user_longitude': request_data.get('user_longitude'),
            'user_city': request_data.get('user_city'),
            'status': 'pending'
        }

        # Add to list
        requests.append(new_request)

        # Save to file
        with open(self.json_path, 'w') as file:
            json.dump({"requests": requests}, file, indent=2)

        print(f"[SAVED] Saved subscription request: {request_id}")
        return request_id

    def get_all_requests(self) -> List[Dict]:
        """
        Get all subscription requests
        Returns: List of request dictionaries
        """
        try:
            with open(self.json_path, 'r') as file:
                data = json.load(file)
                return data.get('requests', [])
        except:
            return []


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points using Haversine formula

    Args:
        lat1, lon1: First point coordinates (degrees)
        lat2, lon2: Second point coordinates (degrees)

    Returns:
        Distance in kilometers (rounded to 2 decimals)
    """
    # Earth's radius in kilometers
    R = 6371.0

    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Differences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Haversine formula
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Distance
    distance = R * c

    return round(distance, 2)


def calculate_subscription_plans(base_monthly: int) -> Dict[str, Dict[str, int]]:
    """
    Calculate subscription plans with discounts

    Args:
        base_monthly: Base monthly price

    Returns:
        Dictionary with plan details
    """
    plans = {
        '1-month': {
            'duration': '1 month',
            'total': base_monthly,
            'monthly': base_monthly,
            'savings': 0
        },
        '3-month': {
            'duration': '3 months',
            'total': int(base_monthly * 3 * 0.93),  # 7% discount
            'monthly': int(base_monthly * 0.93),
            'savings': int(base_monthly * 3 * 0.07)
        },
        '12-month': {
            'duration': '12 months',
            'total': int(base_monthly * 12 * 0.83),  # 17% discount
            'monthly': int(base_monthly * 0.83),
            'savings': int(base_monthly * 12 * 0.17)
        }
    }
    return plans


# Test the module
if __name__ == "__main__":
    print("Testing database module...")

    # Test Haversine distance
    # Mumbai (19.0760, 72.8777) to Delhi (28.6139, 77.2090)
    distance = haversine_distance(19.0760, 72.8777, 28.6139, 77.2090)
    print(f"Mumbai to Delhi: {distance} km (should be ~1150 km)")

    # Test subscription plans
    plans = calculate_subscription_plans(2499)
    print(f"\nSubscription plans for Rs.2,499/month:")
    for plan_type, details in plans.items():
        print(f"  {plan_type}: Rs.{details['total']} (Rs.{details['monthly']}/mo, save Rs.{details['savings']})")

    print("\nDatabase module ready!")
