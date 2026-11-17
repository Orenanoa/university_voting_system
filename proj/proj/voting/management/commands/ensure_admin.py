from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create (or reset) the required superuser: admin / admin123"

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(username="admin")
        user.is_staff = True
        user.is_superuser = True
        user.set_password("admin123")
        user.save()
        self.stdout.write(self.style.SUCCESS(
            f"Superuser 'admin' {'created' if created else 'updated'}."))
