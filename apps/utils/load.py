from django.core.cache import cache
from decimal import Decimal

CITY_DISTANCES = {
    'New York': {
        'nearby': ['Philadelphia', 'Newark', 'Jersey City', 'Yonkers', 'Mount Vernon'],
        'regional': ['Boston', 'Washington DC', 'Baltimore', 'Albany', 'Hartford']
    },
    'Los Angeles': {
        'nearby': ['San Diego', 'Long Beach', 'Anaheim', 'Santa Monica', 'Pasadena'],
        'regional': ['San Francisco', 'Las Vegas', 'Phoenix', 'Sacramento', 'Fresno']
    },
    'Chicago': {
        'nearby': ['Milwaukee', 'Gary', 'Rockford', 'Joliet'],
        'regional': ['Detroit', 'Indianapolis', 'St. Louis', 'Minneapolis']
    },
    'Houston': {
        'nearby': ['Dallas', 'Austin', 'San Antonio', 'Fort Worth'],
        'regional': ['Oklahoma City', 'New Orleans', 'Memphis', 'Little Rock']
    },
    'Philadelphia': {
        'nearby': ['New York', 'Newark', 'Camden', 'Wilmington'],
        'regional': ['Baltimore', 'Washington DC', 'Pittsburgh', 'Atlantic City']
    },
}


def get_distance_category(city1, city2):
    """
    Determine distance category between two cities
    """
    if city1 == city2:
        return 'SAME_CITY'

    # Check both directions for nearby/regional classification
    for source_city, destinations in [(city1, city2), (city2, city1)]:
        city_data = CITY_DISTANCES.get(source_city, {})
        if destinations in city_data.get('nearby', []):
            return 'NEARBY'
        elif destinations in city_data.get('regional', []):
            return 'REGIONAL'

    return 'LONG_DISTANCE'


def get_distance_score(category):
    """
    Get distance score based on category
    """
    scores = {
        'SAME_CITY': 100,
        'NEARBY': 75,
        'REGIONAL': 50,
        'LONG_DISTANCE': 25
    }
    return scores.get(category, 0)


def get_capacity_score(load_weight, truck_capacity):
    """
    Calculate capacity utilization score
    """
    if truck_capacity <= 0:
        return 0

    utilization = (load_weight / truck_capacity) * 100

    if 80 <= utilization <= 100:
        return 100
    elif 60 <= utilization < 80:
        return 75
    elif 40 <= utilization < 60:
        return 50
    elif 20 <= utilization < 40:
        return 25
    else:
        return 0


def get_budget_score(driver_rate, estimated_hours, max_budget):
    """
    Calculate budget compatibility score
    """
    # Convert to Decimal to avoid type mismatch
    driver_rate = Decimal(driver_rate)
    estimated_hours = Decimal(estimated_hours)
    max_budget = Decimal(max_budget)

    if estimated_hours <= 0 or max_budget <= 0:
        return 0

    total_cost = driver_rate * estimated_hours

    if total_cost <= max_budget:
        efficiency_ratio = (max_budget - total_cost) / max_budget
        return float(min(100, 70 + (efficiency_ratio * 30)))  # return as float if needed for further scoring

    return 0


def get_experience_bonus(experience_years):
    """
    Calculate experience bonus points
    """
    if experience_years >= 5:
        return 20
    elif experience_years >= 3:
        return 10
    elif experience_years >= 1:
        return 5
    return 0


def estimate_hours(pickup_city, delivery_city):
    """
    Estimate travel time between cities
    """
    cache_key = f"travel_time:{pickup_city}:{delivery_city}"
    cached_hours = cache.get(cache_key)

    if cached_hours:
        return cached_hours

    # Improved estimation based on distance category
    category = get_distance_category(pickup_city, delivery_city)

    estimated_hours = {
        'SAME_CITY': 2,
        'NEARBY': 4,
        'REGIONAL': 8,
        'LONG_DISTANCE': 15
    }.get(category, 10)

    # Cache for 1 hour
    cache.set(cache_key, estimated_hours, 3600)
    return estimated_hours
