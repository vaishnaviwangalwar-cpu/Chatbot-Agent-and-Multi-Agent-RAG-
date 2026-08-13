"""
DY Patil University Campus FAQ Knowledge Base Data.
Organized as key-value pairs for topic lookups and RAG baseline context.
"""
from typing import Dict

CAMPUS_FAQS: Dict[str, str] = {
    "library hours": "The central library is open Monday through Saturday from 8:00 AM to 10:00 PM, and Sundays from 10:00 AM to 4:00 PM.",
    "hostel fees": "Hostel accommodation fees for the current academic year are 85,000 INR per year (including mess and Wi-Fi services).",
    "exam schedule": "Mid-term examinations start on October 15th, and End-semester examinations begin on December 1st.",
    "wifi access": "Students can connect to 'DYP-Student-WiFi' using their PRN registration number as username and default portal password.",
    "campus shuttle": "Free campus shuttle buses run every 15 minutes between the main gate, academic blocks, and student hostels from 7:30 AM to 8:30 PM.",
    "canteen": "The central food court offers vegetarian and non-vegetarian meals from 8:00 AM to 7:00 PM.",
}
