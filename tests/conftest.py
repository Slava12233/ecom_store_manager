import pytest
import urllib3
import os
import sys
import warnings
import requests

# הוספת נתיב הפרויקט ל-PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# השבתת אזהרות HTTPS לא מאומתות מיד עם אתחול הבדיקות
warnings.filterwarnings(
    "ignore",
    message="Unverified HTTPS request is being made to host.*",
    category=urllib3.exceptions.InsecureRequestWarning
)

@pytest.fixture(scope="session", autouse=True)
def disable_insecure_requests_warnings():
    """
    משבית אזהרות של בקשות HTTPS לא מאומתות במהלך הבדיקות.
    בסביבת פרודקשן יש להשתמש באימות תעודות מלא.
    """
    # השבתת אזהרות של urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # השבתת אזהרות של requests
    warnings.filterwarnings('ignore', category=requests.packages.urllib3.exceptions.InsecureRequestWarning)
    
    # השבתת כל האזהרות הקשורות ל-HTTPS
    warnings.filterwarnings('ignore', message='Unverified HTTPS request') 