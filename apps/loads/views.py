import logging

from datetime import datetime

from rest_framework import status
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from django.db import transaction
from django.shortcuts import render
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from apps.loads.models import Load
from apps.drivers.models import Driver
from apps.matches.models import LoadMatch
from apps.loads.serializers import LoadSerializer
from apps.utils.load import get_distance_category, get_distance_score, get_capacity_score, get_budget_score, \
    get_experience_bonus, estimate_hours

logger = logging.getLogger(__name__)


class LoadCreateAPIView(generics.CreateAPIView):
    """
    API endpoint to create a new Load instance.
    """

    def get_queryset(self):
        return Load.objects.all()

    def get_serializer_class(self):
        return LoadSerializer


class LoadMatchListAPIView(APIView):
    """
    Get best driver matches for a specific load
    """

    def get(self, request, pk):
        try:
            # Check cache first
            cache_key = f"load_matches:{pk}"
            cached_matches = cache.get(cache_key)

            if cached_matches:
                logger.info(f"Returning cached matches for load {pk}")
                return Response({
                    'load_id': pk,
                    'matches': cached_matches,
                    'cached': True
                }, status=status.HTTP_200_OK)

            # Get load with error handling
            try:
                load = Load.objects.select_related('company').get(pk=pk)
            except Load.DoesNotExist:
                return Response(
                    {'error': 'Load not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if load is still available for matching
            if load.status != 'POSTED':
                return Response(
                    {'error': 'Load is not available for matching'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get available drivers with optimized query
            available_drivers = Driver.objects.select_related('user').filter(
                is_available=True,
                truck_capacity_kg__gte=load.weight_kg * 1.1  # 10% safety margin
            )

            if not available_drivers.exists():
                return Response({
                    'load_id': pk,
                    'matches': [],
                    'message': 'No available drivers found'
                }, status=status.HTTP_200_OK)

            matches = []

            for driver in available_drivers:
                try:
                    match_data = self._calculate_match_score(load, driver)

                    # Only include drivers with reasonable scores (>20)
                    if match_data['total_score'] > 20:
                        matches.append(match_data)

                except Exception as e:
                    logger.warning(f"Error calculating match for driver {driver.id}: {str(e)}")
                    continue

            # Sort by score and limit to top 10
            sorted_matches = sorted(matches, key=lambda x: x['total_score'], reverse=True)[:10]

            # Create LoadMatch records for top matches
            self._create_load_match_records(load, sorted_matches)

            # Cache results for 10 minutes
            cache.set(cache_key, sorted_matches, 600)

            logger.info(f"Generated {len(sorted_matches)} matches for load {pk}")

            return Response({
                'load_id': pk,
                'load_details': {
                    'pickup_city': load.pickup_city,
                    'delivery_city': load.delivery_city,
                    'weight_kg': load.weight_kg,
                    'max_budget': float(load.max_budget),
                    'pickup_date': load.pickup_date.isoformat()
                },
                'matches': sorted_matches,
                'total_matches': len(sorted_matches),
                'cached': False
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in LoadMatchListAPIView: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _calculate_match_score(self, load, driver):
        """
        Calculate comprehensive match score for driver-load pair
        """

        # Distance scoring (35%)
        distance_category = get_distance_category(load.pickup_city, driver.home_city)
        distance_score = get_distance_score(distance_category)

        # Capacity scoring (30%)
        capacity_score = get_capacity_score(load.weight_kg, driver.truck_capacity_kg)

        # Budget scoring (25%)
        estimated_hours = estimate_hours(load.pickup_city, load.delivery_city)
        budget_score = get_budget_score(driver.hourly_rate, estimated_hours, load.max_budget)

        # Experience bonus (10%)
        experience_bonus = get_experience_bonus(driver.experience_years)

        # Calculate weighted total score
        total_score = (
                distance_score * 0.35 +
                capacity_score * 0.30 +
                budget_score * 0.25 +
                experience_bonus  # Experience bonus is already in points, not percentage
        )

        # Calculate estimated cost for transparency
        estimated_cost = driver.hourly_rate * estimated_hours

        return {
            'driver_id': driver.id,
            'driver_name': driver.user.get_full_name() or driver.user.username,
            'home_city': driver.home_city,
            'truck_capacity_kg': driver.truck_capacity_kg,
            'hourly_rate': float(driver.hourly_rate),
            'experience_years': driver.experience_years,
            'distance_category': distance_category,
            'estimated_hours': estimated_hours,
            'estimated_cost': float(estimated_cost),
            'scores': {
                'distance_score': round(distance_score * 0.35, 1),
                'capacity_score': round(capacity_score * 0.30, 1),
                'budget_score': round(budget_score * 0.25, 1),
                'experience_bonus': experience_bonus
            },
            'total_score': round(total_score, 2),
            'capacity_utilization': round((load.weight_kg / driver.truck_capacity_kg) * 100, 1),
            'budget_fit': estimated_cost <= load.max_budget
        }

    def _create_load_match_records(self, load, matches):
        """
        Create LoadMatch records for top matches.
        """

        try:
            with transaction.atomic():
                # Clear existing matches for this load
                LoadMatch.objects.filter(load=load).delete()

                # Create new match records
                match_objects = []
                for match in matches[:5]:  # Store top 5 matches
                    match_objects.append(LoadMatch(
                        load=load,
                        driver_id=match['driver_id'],
                        distance_category=match['distance_category'],
                        match_score=match['total_score']
                    ))

                LoadMatch.objects.bulk_create(match_objects)

        except Exception as e:
            logger.warning(f"Failed to create LoadMatch records: {str(e)}")

    def delete(self, request, pk):
        """
        Clear cached matches for a load (useful for testing)
        """

        cache_key = f"load_matches:{pk}"
        cache.delete(cache_key)

        return Response(
            {'message': f'Cache cleared for load {pk}'},
            status=status.HTTP_200_OK
        )
