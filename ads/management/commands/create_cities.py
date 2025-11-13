from django.core.management.base import BaseCommand
from ads.models import City

class Command(BaseCommand):
    help = 'Populate database with major Canadian cities'

    def handle(self, *args, **options):
        cities_data = [
            # Ontario (20 cities)
            {'name': 'Toronto', 'province': 'ON'},
            {'name': 'Ottawa', 'province': 'ON'},
            {'name': 'Mississauga', 'province': 'ON'},
            {'name': 'Brampton', 'province': 'ON'},
            {'name': 'Hamilton', 'province': 'ON'},
            {'name': 'London', 'province': 'ON'},
            {'name': 'Markham', 'province': 'ON'},
            {'name': 'Vaughan', 'province': 'ON'},
            {'name': 'Kitchener', 'province': 'ON'},
            {'name': 'Windsor', 'province': 'ON'},
            {'name': 'Richmond Hill', 'province': 'ON'},
            {'name': 'Oakville', 'province': 'ON'},
            {'name': 'Burlington', 'province': 'ON'},
            {'name': 'Oshawa', 'province': 'ON'},
            {'name': 'Barrie', 'province': 'ON'},
            {'name': 'St. Catharines', 'province': 'ON'},
            {'name': 'Cambridge', 'province': 'ON'},
            {'name': 'Waterloo', 'province': 'ON'},
            {'name': 'Guelph', 'province': 'ON'},
            {'name': 'Kingston', 'province': 'ON'},
            
            # Quebec (15 cities)
            {'name': 'Montreal', 'province': 'QC'},
            {'name': 'Quebec City', 'province': 'QC'},
            {'name': 'Laval', 'province': 'QC'},
            {'name': 'Gatineau', 'province': 'QC'},
            {'name': 'Longueuil', 'province': 'QC'},
            {'name': 'Sherbrooke', 'province': 'QC'},
            {'name': 'Saguenay', 'province': 'QC'},
            {'name': 'Lévis', 'province': 'QC'},
            {'name': 'Trois-Rivières', 'province': 'QC'},
            {'name': 'Terrebonne', 'province': 'QC'},
            {'name': 'Saint-Jean-sur-Richelieu', 'province': 'QC'},
            {'name': 'Repentigny', 'province': 'QC'},
            {'name': 'Brossard', 'province': 'QC'},
            {'name': 'Drummondville', 'province': 'QC'},
            {'name': 'Saint-Jérôme', 'province': 'QC'},
            
            # British Columbia (15 cities)
            {'name': 'Vancouver', 'province': 'BC'},
            {'name': 'Surrey', 'province': 'BC'},
            {'name': 'Burnaby', 'province': 'BC'},
            {'name': 'Richmond', 'province': 'BC'},
            {'name': 'Abbotsford', 'province': 'BC'},
            {'name': 'Coquitlam', 'province': 'BC'},
            {'name': 'Kelowna', 'province': 'BC'},
            {'name': 'Victoria', 'province': 'BC'},
            {'name': 'Langley', 'province': 'BC'},
            {'name': 'Delta', 'province': 'BC'},
            {'name': 'Kamloops', 'province': 'BC'},
            {'name': 'Nanaimo', 'province': 'BC'},
            {'name': 'Prince George', 'province': 'BC'},
            {'name': 'Chilliwack', 'province': 'BC'},
            {'name': 'Vernon', 'province': 'BC'},
            
            # Alberta (12 cities)
            {'name': 'Calgary', 'province': 'AB'},
            {'name': 'Edmonton', 'province': 'AB'},
            {'name': 'Red Deer', 'province': 'AB'},
            {'name': 'Lethbridge', 'province': 'AB'},
            {'name': 'St. Albert', 'province': 'AB'},
            {'name': 'Medicine Hat', 'province': 'AB'},
            {'name': 'Grande Prairie', 'province': 'AB'},
            {'name': 'Airdrie', 'province': 'AB'},
            {'name': 'Fort McMurray', 'province': 'AB'},
            {'name': 'Spruce Grove', 'province': 'AB'},
            {'name': 'Leduc', 'province': 'AB'},
            {'name': 'Okotoks', 'province': 'AB'},
            
            # Manitoba (5 cities)
            {'name': 'Winnipeg', 'province': 'MB'},
            {'name': 'Brandon', 'province': 'MB'},
            {'name': 'Steinbach', 'province': 'MB'},
            {'name': 'Thompson', 'province': 'MB'},
            {'name': 'Portage la Prairie', 'province': 'MB'},
            
            # Saskatchewan (5 cities)
            {'name': 'Saskatoon', 'province': 'SK'},
            {'name': 'Regina', 'province': 'SK'},
            {'name': 'Prince Albert', 'province': 'SK'},
            {'name': 'Moose Jaw', 'province': 'SK'},
            {'name': 'Swift Current', 'province': 'SK'},
            
            # Nova Scotia (5 cities)
            {'name': 'Halifax', 'province': 'NS'},
            {'name': 'Dartmouth', 'province': 'NS'},
            {'name': 'Sydney', 'province': 'NS'},
            {'name': 'Truro', 'province': 'NS'},
            {'name': 'New Glasgow', 'province': 'NS'},
            
            # New Brunswick (5 cities)
            {'name': 'Moncton', 'province': 'NB'},
            {'name': 'Saint John', 'province': 'NB'},
            {'name': 'Fredericton', 'province': 'NB'},
            {'name': 'Dieppe', 'province': 'NB'},
            {'name': 'Bathurst', 'province': 'NB'},
            
            # Newfoundland and Labrador (4 cities)
            {'name': "St. John's", 'province': 'NL'},
            {'name': 'Mount Pearl', 'province': 'NL'},
            {'name': 'Corner Brook', 'province': 'NL'},
            {'name': 'Conception Bay South', 'province': 'NL'},
            
            # Prince Edward Island (2 cities)
            {'name': 'Charlottetown', 'province': 'PE'},
            {'name': 'Summerside', 'province': 'PE'},
            
            # Yukon (1 city)
            {'name': 'Whitehorse', 'province': 'YT'},
            
            # Northwest Territories (1 city)
            {'name': 'Yellowknife', 'province': 'NT'},
            
            # Nunavut (1 city)
            {'name': 'Iqaluit', 'province': 'NU'},
        ]
        
        created_count = 0
        existing_count = 0
        
        for city_data in cities_data:
            city, created = City.objects.get_or_create(
                name=city_data['name'],
                province=city_data['province'],
                defaults=city_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created city: {city_data["name"]}, {city_data["province"]}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'- City already exists: {city_data["name"]}, {city_data["province"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n=== Summary ===')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Cities created: {created_count}')
        )
        self.stdout.write(
            self.style.WARNING(f'Cities already existing: {existing_count}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Total cities in database: {City.objects.count()}')
        )