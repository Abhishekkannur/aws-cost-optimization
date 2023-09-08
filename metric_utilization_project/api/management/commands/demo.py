from django.core.management.base import BaseCommand
from subprocess import call
from views import Get_Detailed_AWS_Cost  # Import your view
import argparse
import datetime
import os
DATETIME_NOW = datetime.utcnow()
AWS_COST_EXPLORER_SERVICE_KEY = "ce"
OUTPUT_FILE_NAME = "report.csv"
DEFAULT_PROFILE_NAME = "default"
OUTPUT_FILE_HEADER_LINE = ",".join(
            ["Time Period", "Linked Account", "Service", "Amount",
            "Unit", "Estimated", "\n"])
CURRENT_FOLDER_PATH = os.path.abspath(os.path.curdir)
DEFAULT_OUTPUT_FILE_PATH = os.path.join(CURRENT_FOLDER_PATH, OUTPUT_FILE_NAME)
COST_EXPLORER_GRANULARITY_MONTHLY = "MONTHLY"
COST_EXPLORER_GRANULARITY_DAILY = "DAILY"
COST_EXPLORER_GROUP_BY = [
            {"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"},
            {"Type": "DIMENSION", "Key": "SERVICE"}]
class Command(BaseCommand):
    help = 'Start the server after running AWS cost analysis'

    def add_arguments(self, parser):
        # Add the same arguments as your create_parser method
        parser.add_argument("-output", dest="fpath", default=DEFAULT_OUTPUT_FILE_PATH, help="output file path")
        parser.add_argument("-profile-name", dest="profile_name", default=DEFAULT_PROFILE_NAME, help="Profile name on your AWS account")
        parser.add_argument("-days", type=int, dest="days", default=None, help="get data for daily usage and cost by given days")
        parser.add_argument("-months", type=int, dest="months", default=None, help="get data for monthly usage and cost by given months")
        parser.add_argument("-disable-total", action="store_true", default=False, help="Do not output total cost per day, or month unit")

    def handle(self, *args, **options):
        # Include your AWS-related logic here
        view = Get_Detailed_AWS_Cost()
        response = view.get(request=None, daily=options['days'], monthly=options['months'], enable_total=not options['disable_total'])

        # Start the development server
        call(['python', 'manage.py', 'runserver'])
