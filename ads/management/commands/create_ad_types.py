from django.core.management.base import BaseCommand
from ads.models import AdType

class Command(BaseCommand):
    help = 'Create initial ad types'

    def handle(self, *args, **options):
        ad_types_data = [
            {
                'name': 'Mechanic',
                'icon': '🔧'
            },
            {
                'name': 'Plumber',
                'icon': '🚰'
            },
            {
                'name': 'Electrician',
                'icon': '🔌'
            },
            {
                'name': 'Carpenter',
                'icon': '🪵'
            },
            {
                'name': 'Photographer',
                'icon': '📷'
            },
            {
                'name': 'Snow Removal',
                'icon': '❄️'
            },
            {
                'name': 'Landscaper',
                'icon': '🌳'
            },
            {
                'name': 'Moving Services',
                'icon': '🚚'
            },
            {
                'name': 'Cleaning Services',
                'icon': '🧹'
            },
            {
                'name': 'Website/App Development',
                'icon': '💻'
            },
            {
                'name': 'Electrical',
                'icon': '⚡'
            }
        ]
        
        for ad_type_data in ad_types_data:
            ad_type, created = AdType.objects.get_or_create(
                name=ad_type_data['name'],
                defaults=ad_type_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created ad type "{ad_type_data["name"]}"')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Ad type "{ad_type_data["name"]}" already exists')
                )