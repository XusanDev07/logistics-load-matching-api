from rest_framework.generics import CreateAPIView
from django.contrib.auth.models import User
from apps.drivers.models import Driver
from apps.loads.models import Load

from apps.authentication.serializers import RegisterSerializer
# company = User.objects.create_user(username='logistics_corp_1')
# driver_user = User.objects.create_user(username='john_driver_1', first_name='Ketmon', last_name='Toshmatov')

# driver = Driver.objects.create(
#     user_id=4,
#     home_city='Boston',
#     truck_capacity_kg=15000,
#     is_available=True,
#     hourly_rate=50.00,
#     experience_years=5
# )
#
# load = Load.objects.create(
#     company_id=3,
#     pickup_city='Oklahoma City',
#     delivery_city='New Orleans',
#     weight_kg=8000,
#     pickup_date=date.today() + timedelta(days=2),
#     max_budget=500.00,
#     status='POSTED'
# )
#
# print(f"Created load ID: {load.id}")



class RegisterAPIView(CreateAPIView):
    """
    user register view
    """

    permission_classes = ()
    authentication_classes = ()
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        pass
