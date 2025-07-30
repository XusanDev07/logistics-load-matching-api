import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from django.db import transaction
from django.utils import timezone
from django.core.cache import cache

from apps.loads.models import Load
from apps.drivers.models import Driver

logger = logging.getLogger(__name__)


class DriverAvailabilityAPIView(APIView):
    """
    Update driver's availability status
    POST /api/drivers/availability/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Update driver availability status
        """
        try:
            # Get driver for authenticated user
            try:
                driver = Driver.objects.select_related('user').get(user=request.user)
            except Driver.DoesNotExist:
                return Response(
                    {'error': 'Driver profile not found for this user'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Validate request data
            is_available = request.data.get('is_available')

            if is_available is None:
                return Response(
                    {'error': 'is_available field is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if not isinstance(is_available, bool):
                return Response(
                    {'error': 'is_available must be a boolean value'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get current status before update
            previous_status = driver.is_available

            # Optional: Add reason for status change
            reason = request.data.get('reason', '')

            # Update driver availability with transaction
            with transaction.atomic():
                driver.is_available = is_available
                driver.save(update_fields=['is_available'])

                # Log the status change
                logger.info(
                    f"Driver {driver.id} ({driver.user.username}) "
                    f"availability changed from {previous_status} to {is_available}"
                )

            # Cache the new availability status
            self._cache_driver_availability(driver)

            # Invalidate related cached matches if driver became unavailable
            if previous_status and not is_available:
                self._invalidate_related_matches(driver)

            # Prepare response data
            response_data = {
                'driver_id': driver.id,
                'driver_name': driver.user.get_full_name() or driver.user.username,
                'is_available': driver.is_available,
                'previous_status': previous_status,
                'status_changed': previous_status != is_available,
                'updated_at': timezone.now().isoformat(),
                'home_city': driver.home_city,
                'truck_capacity_kg': driver.truck_capacity_kg
            }

            # Add reason if provided
            if reason:
                response_data['reason'] = reason

            # Add helpful message
            if driver.is_available:
                response_data['message'] = 'Driver is now available for new loads'

                # Suggest suitable loads if driver became available
                suitable_loads = self._get_suitable_loads(driver)
                if suitable_loads:
                    response_data['suggested_loads'] = suitable_loads[:3]  # Top 3
                    response_data['total_suitable_loads'] = len(suitable_loads)
            else:
                response_data['message'] = 'Driver is now unavailable for new loads'

            status_code = status.HTTP_200_OK

            return Response(response_data, status=status_code)

        except Exception as e:
            logger.error(f"Error updating driver availability: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _cache_driver_availability(self, driver):
        """
        Cache driver availability status
        """
        cache_key = f"driver_availability:{driver.id}"
        cache_data = {
            'is_available': driver.is_available,
            'home_city': driver.home_city,
            'truck_capacity_kg': driver.truck_capacity_kg,
            'hourly_rate': float(driver.hourly_rate),
            'updated_at': timezone.now().isoformat()
        }

        # Cache for 1 hour
        cache.set(cache_key, cache_data, 3600)
        logger.debug(f"Cached availability for driver {driver.id}")

    def _invalidate_related_matches(self, driver):
        """
        Invalidate cached matches that include this driver
        """
        try:
            # Find loads that might have this driver in cached matches
            # This is a simplified approach - in production you might want more sophisticated cache tagging

            # Get recent posted loads in driver's region
            from apps.loads.models import Load

            # Rough estimate of loads that might include this driver
            potential_loads = Load.objects.filter(
                status='POSTED',
                pickup_date__gte=timezone.now().date()
            )

            # Clear cache for these loads
            invalidated_count = 0
            for load in potential_loads:
                cache_key = f"load_matches:{load.id}"
                if cache.delete(cache_key):
                    invalidated_count += 1

            if invalidated_count > 0:
                logger.info(
                    f"Invalidated {invalidated_count} cached match results due to driver {driver.id} status change")

        except Exception as e:
            logger.warning(f"Failed to invalidate related matches: {str(e)}")


class SuitableLoadsAPIView(APIView):
    """
    Get current driver availability status.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Get driver for authenticated user
            try:
                driver = Driver.objects.select_related('user').get(user=request.user)
            except Driver.DoesNotExist:
                return Response(
                    {'error': 'Driver profile not found for this user'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check if status is cached
            cache_key = f"driver_availability:{driver.id}"
            cached_status = cache.get(cache_key)

            response_data = {
                'driver_id': driver.id,
                'driver_name': driver.user.get_full_name() or driver.user.username,
                'is_available': driver.is_available,
                'home_city': driver.home_city,
                'truck_capacity_kg': driver.truck_capacity_kg,
                'hourly_rate': float(driver.hourly_rate),
                'experience_years': driver.experience_years,
                'cached': cached_status is not None
            }

            # If available, show suitable loads
            if driver.is_available:
                suitable_loads = self._get_suitable_loads(driver)
                response_data['suitable_loads_count'] = len(suitable_loads)
                if suitable_loads:
                    response_data['top_suitable_loads'] = suitable_loads[:5]

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error getting driver availability: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_suitable_loads(self, driver):
        """
        Get loads suitable for this driver
        """
        try:
            from apps.loads.models import Load
            from apps.utils.load import get_distance_category, estimate_hours

            # Get posted loads that driver can handle
            suitable_loads_qs = Load.objects.select_related('company').filter(
                status='POSTED',
                pickup_date__gte=timezone.now().date(),
                weight_kg__lte=driver.truck_capacity_kg * 0.9  # 10% safety margin
            )

            suitable_loads = []

            for load in suitable_loads_qs[:10]:  # Limit to avoid performance issues
                try:
                    # Quick suitability check
                    estimated_hours = estimate_hours(load.pickup_city, load.delivery_city)
                    estimated_cost = driver.hourly_rate * estimated_hours

                    # Must fit in budget
                    if estimated_cost <= load.max_budget:
                        distance_category = get_distance_category(load.pickup_city, driver.home_city)

                        suitable_loads.append({
                            'load_id': load.id,
                            'pickup_city': load.pickup_city,
                            'delivery_city': load.delivery_city,
                            'weight_kg': load.weight_kg,
                            'max_budget': float(load.max_budget),
                            'pickup_date': load.pickup_date.isoformat(),
                            'distance_category': distance_category,
                            'estimated_hours': estimated_hours,
                            'estimated_cost': float(estimated_cost),
                            'profit_margin': float(load.max_budget - estimated_cost),
                            'capacity_utilization': round((load.weight_kg / driver.truck_capacity_kg) * 100, 1)
                        })

                except Exception as e:
                    logger.warning(f"Error calculating suitability for load {load.id}: {str(e)}")
                    continue

            # Sort by profit margin (descending)
            suitable_loads.sort(key=lambda x: x['profit_margin'], reverse=True)

            return suitable_loads

        except Exception as e:
            logger.warning(f"Error getting suitable loads: {str(e)}")
            return []


class BulkDriverAvailabilityAPIView(APIView):
    """
    Bulk update availability for multiple drivers (admin only)
    POST /api/drivers/availability/bulk/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Bulk update driver availability
        """
        try:
            # Check if user has permission (you can add custom permission classes)
            if not request.user.is_staff:
                return Response(
                    {'error': 'Admin access required'},
                    status=status.HTTP_403_FORBIDDEN
                )

            updates = request.data.get('updates', [])

            if not isinstance(updates, list) or not updates:
                return Response(
                    {'error': 'updates field must be a non-empty list'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            results = []
            errors = []

            with transaction.atomic():
                for update in updates:
                    try:
                        driver_id = update.get('driver_id')
                        is_available = update.get('is_available')

                        if driver_id is None or is_available is None:
                            errors.append({
                                'driver_id': driver_id,
                                'error': 'driver_id and is_available are required'
                            })
                            continue

                        driver = Driver.objects.get(id=driver_id)
                        previous_status = driver.is_available

                        driver.is_available = is_available
                        driver.save(update_fields=['is_available'])

                        # Cache the new status
                        self._cache_driver_availability(driver)

                        results.append({
                            'driver_id': driver.id,
                            'driver_name': driver.user.get_full_name() or driver.user.username,
                            'previous_status': previous_status,
                            'new_status': is_available,
                            'status_changed': previous_status != is_available
                        })

                    except Driver.DoesNotExist:
                        errors.append({
                            'driver_id': driver_id,
                            'error': 'Driver not found'
                        })
                    except Exception as e:
                        errors.append({
                            'driver_id': driver_id,
                            'error': str(e)
                        })

            # Invalidate related caches
            self._bulk_invalidate_matches()

            response_data = {
                'successful_updates': len(results),
                'failed_updates': len(errors),
                'results': results
            }

            if errors:
                response_data['errors'] = errors

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error in bulk availability update: {str(e)}")
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _cache_driver_availability(self, driver):
        """
        Cache driver availability status
        """
        cache_key = f"driver_availability:{driver.id}"
        cache_data = {
            'is_available': driver.is_available,
            'home_city': driver.home_city,
            'truck_capacity_kg': driver.truck_capacity_kg,
            'hourly_rate': float(driver.hourly_rate),
            'updated_at': timezone.now().isoformat()
        }
        cache.set(cache_key, cache_data, 3600)
