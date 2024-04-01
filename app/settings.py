from django.contrib.auth.models import User
from django.utils.deprecation import MiddlewareMixin


class AutoLoginMiddleware(MiddlewareMixin):
    def process_request(self, request):
        user, created = User.objects.get_or_create(
            username='admin',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        request.user = user
