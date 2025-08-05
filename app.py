import sys
import os
import json
import random
from datetime import datetime, timedelta
from faker import Faker
import io
import requests
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE = os.getenv("DEEPSEEK_BASE", "").rstrip("/")

# Faker for synthetic names/streets
fake = Faker('en_US')

# Cache dictionaries
_highschool_cache = {}
_area_code_cache = {}

# Files
NAMES_FILE = "generated_names.txt"
AREA_CODES_FILE = "areacodes.txt"
HIGH_SCHOOLS_FILE = "high_schools.txt"

# City → State mapping
CITY_TO_STATE = {
    "Atlanta": "Georgia",
    "Boston": "Massachusetts",
    "Buffalo": "New York",
    "Charlotte": "North Carolina",
    "Chicago": "Illinois",
    "Dallas": "Texas",
    "Denver": "Colorado",
    "Detroit": "Michigan",
    "Houston": "Texas",
    "Kansas City": "Missouri",
    "Los Angeles": "California",
    "Manassas": "Virginia",
    "McAllen": "Texas",
    "Miami": "Florida",
    "Nashville": "Tennessee",
    "New York": "New York",
    "Omaha": "Nebraska",
    "Phoenix": "Arizona",
    "Salt Lake City": "Utah",
    "San Francisco": "California",
    "St. Louis": "Missouri",
    "Seattle": "Washington"
}

# State → abbreviation
STATE_ABBR = {
    "California": "CA", "Texas": "TX", "Florida": "FL", "New York": "NY",
    "Illinois": "IL", "Georgia": "GA", "Massachusetts": "MA", "North Carolina": "NC",
    "Colorado": "CO", "Michigan": "MI", "Missouri": "MO", "Virginia": "VA",
    "Tennessee": "TN", "Nebraska": "NE", "Arizona": "AZ", "Utah": "UT", "Washington": "WA"
}

# Fallback schools and area codes
FALLBACK_HIGH_SCHOOLS = {"Generic City": ["Generic High School"]}
FALLBACK_AREA_CODES = {"Generic": ["555"]}

# ---------------- DeepSeek API Helper ----------------
def deepseek_get(path: str, params: dict | None = None):
    if not DEEPSEEK_API_KEY or not DEEPSEEK_BASE:
        return None
    headers = {"Authorization": f"Bearer {DEEPSEEK_API_KEY}", "Accept": "application/json"}
    url = f"{DEEPSEEK_BASE}/{path.lstrip('/')}"
    try:
        resp = requests.get(url, headers=headers, params=params or {}, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None

# ---------------- Names Management ----------------
def load_used_names():
    if not os.path.exists(NAMES_FILE):
        return set()
    with open(NAMES_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_new_names(names):
    with open(NAMES_FILE, "a") as f:
        for name in names:
            f.write(name + "\n")

used_names = load_used_names()

# ---------------- Area Codes Loader ----------------
def load_area_codes(file_path=AREA_CODES_FILE):
    area_codes = {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or ":" not in line:
                    continue
                city, codes_str = line.split(":", 1)
                codes = [c.strip() for c in codes_str.split(",") if c.strip()]
                area_codes[city.strip()] = codes
    except FileNotFoundError:
        print(f"[Warning] Area codes file not found: {file_path}")
    return area_codes

CITY_AREA_CODES = load_area_codes()

# ---------------- High Schools Loader ----------------
def load_high_schools(filepath=HIGH_SCHOOLS_FILE):
    schools_by_city = {}
    current_city = None
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            for line in file:
                stripped = line.strip()
                if not stripped:
                    continue
                if ':' in line:
                    city, school = line.split(':', 1)
                    current_city = city.strip()
                    schools_by_city[current_city] = [school.strip()] if school.strip() else []
                else:
                    if current_city:
                        schools_by_city[current_city].append(stripped)
    except FileNotFoundError:
        print(f"[Warning] High schools file not found: {filepath}")
    return schools_by_city

CITY_HIGH_SCHOOLS = load_high_schools()

# ---------------- ZIP Code Fetch (Real) ----------------
def fetch_zip_for_city_state(city, state):
    abbr = STATE_ABBR.get(state)
    if not abbr:
        return None
    try:
        url = f"http://api.zippopotam.us/us/{abbr}/{city.replace(' ', '%20')}"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if "places" in data and data["places"]:
                return data["places"][0].get("post code")
    except Exception as e:
        print(f"[Warning] ZIP fetch failed for {city}, {state}: {e}")
    return None

# ---------------- Generators ----------------
def generate_name(gender):
    while True:
        first = fake.first_name_male() if gender == "Male" else fake.first_name_female()
        last = fake.last_name()
        name = f"{first} {last}"
        if name not in used_names:
            used_names.add(name)
            save_new_names([name])
            return name

def generate_birth_date_2010():
    start_date = datetime(2010, 1, 1)
    end_date = datetime(2010, 12, 31)
    return start_date + timedelta(days=random.randrange((end_date - start_date).days))

def choose_high_school_state_city():
    city = get_next_city()
    state = CITY_TO_STATE[city]
    schools = CITY_HIGH_SCHOOLS.get(city, FALLBACK_HIGH_SCHOOLS.get("Generic City"))
    school = random.choice(schools)
    return f"{school}, {city}", state, city

def generate_address_with_real_zip(city, state):
    zip_code = fetch_zip_for_city_state(city, state)
    if not zip_code:
        # Fallback: generate a random 5-digit ZIP code
        zip_code = f"{random.randint(10000, 99999)}"
    return zip_code



def generate_phone_number_from_state_city(state, city=None):
    if city and city in CITY_AREA_CODES and CITY_AREA_CODES[city]:
        area = random.choice(CITY_AREA_CODES[city])
    else:
        area_codes = FALLBACK_AREA_CODES.get(state, ["555"])
        area = random.choice(area_codes)
    # Return as a continuous string: area + 7 random digits
    return f"{area}{random.randint(200, 999)}{random.randint(0, 9999):04d}"

def generate_demographic_profile(gender):
    name = generate_name(gender)
    high_school_full, state, city = choose_high_school_state_city()
    phone = generate_phone_number_from_state_city(state, city)
    address = generate_address_with_real_zip(city, state)
    return {
        "Name": name,
        "Phone Number": phone,
        "Date of Birth": generate_birth_date_2010().strftime("%Y-%m-%d"),
        "State": state,
        "City": city,
        "Zip Code": address,
        "High School": high_school_full,
    }

def convert_to_csv(profiles_df):
    output = io.StringIO()
    profiles_df.to_csv(output, index=False)
    return output.getvalue()

def convert_to_txt(profiles_df):
    output = io.StringIO()
    for idx, row in profiles_df.iterrows():
        output.write(f"{idx+1}.\n")
        output.write(f"   Name: {row['Name']}\n")
        output.write(f"   Phone Number: {row['Phone Number']}\n")
        output.write(f"   Date of Birth: {row['Date of Birth']}\n")
        output.write(f"   State: {row['State']}\n")
        output.write(f"   City: {row['City']}\n")
        output.write(f"   Zip Code: {row['Zip Code']}\n")
        output.write(f"   High School: {row['High School']}\n\n")
    return output.getvalue()

# ---------------- Streamlit UI ----------------
def run_streamlit_app():
    import streamlit as st
    st.set_page_config(page_title="Evolveme Profiles Generator", page_icon="👥", layout="wide")
    st.title("Evolveme Profiles Generator")
    st.markdown("Generate random profiles ")
    st.info("👈 Use the sidebar to configure and generate the profiles")

    st.sidebar.header("⚙️ Settings")
    generated_for = st.sidebar.text_input("Who are you generating this data for?", placeholder="Enter name")
    gender = st.sidebar.radio("Select Gender:", ["Male", "Female"])
    num_records = st.sidebar.number_input("Number of profiles:", min_value=1, max_value=10000, value=10, step=1)
    file_format = st.sidebar.selectbox("Select file format:", ["CSV", "TXT"])
    generate_button = st.sidebar.button("🎲 Generate Profiles", type="primary")

    if generate_button:
        if not generated_for:
            st.error("Please enter who you are generating for.")
            return

        profiles = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i in range(num_records):
            profiles.append(generate_demographic_profile(gender))
            progress_bar.progress((i + 1) / num_records)
            status_text.text(f"Generating profile {i + 1} of {num_records}...")

        progress_bar.empty()
        status_text.empty()

        df = pd.DataFrame(profiles)
        st.success(f"✅ Generated {num_records} profiles for {generated_for}")
        st.dataframe(df, use_container_width=True)

        if file_format == "CSV/TXT":
            csv_data = convert_to_csv(df)
            st.download_button(
                "📥 Download as CSV",
                csv_data,
                f"{generated_for.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "text/csv"
            )

           
        else:  # TSV
            txt_data = convert_to_txt(df)
            st.download_button(
                "📄 Download as TXT",
                txt_data,
                f"{generated_for.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "text/plain"
            )

# ---------------- CLI Bare Mode ----------------
def run_bare_mode():
    generated_for = input("Who are you generating this data for? ").strip()
    while not generated_for:
        generated_for = input("Please enter a valid name: ").strip()

    gender = input("Select Gender (Male/Female): ").strip().capitalize()
    while gender not in ["Male", "Female"]:
        gender = input("Invalid. Enter Male or Female: ").strip().capitalize()

    try:
        num_records = int(input("Number of profiles (1-10000): ").strip())
        if not (1 <= num_records <= 10000):
            raise ValueError
    except ValueError:
        print("Invalid number, defaulting to 10")
        num_records = 10

    profiles = [generate_demographic_profile(gender) for _ in range(num_records)]
    df = pd.DataFrame(profiles)
    file_name = f"{generated_for.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(file_name, index=False)
    print(f"\n✅ Generated {num_records} profiles for '{generated_for}'. Saved to {file_name}")

# ---------------- City Queue ----------------
_city_queue = []

def get_next_city():
    global _city_queue
    if not _city_queue:
        _city_queue = list(CITY_TO_STATE.keys())
        random.shuffle(_city_queue)
    return _city_queue.pop()

# ---------------- Entry Point ----------------
if __name__ == "__main__":
    if "--bare" in sys.argv:
        run_bare_mode()
    else:
        run_streamlit_app()
