import sys
import pandas as pd
import random
from datetime import datetime, timedelta
from faker import Faker
import io

# Initialize Faker for US locale
fake = Faker('en_US')

# High schools data from major US states
HIGH_SCHOOLS = {
    'California': ['Lowell High School', 'Washington High School', 'Lincoln High School', 'Roosevelt High School', 'Jefferson High School', 'Kennedy High School', 'Wilson High School', 'Adams High School', 'Madison High School', 'Monroe High School', 'Jackson High School', 'Grant High School'],
    'Texas': ['Austin High School', 'Houston High School', 'Dallas High School', 'San Antonio High School', 'Fort Worth High School', 'El Paso High School', 'Arlington High School', 'Corpus Christi High School', 'Plano High School', 'Lubbock High School', 'Garland High School', 'Irving High School'],
    'Florida': ['Miami High School', 'Tampa High School', 'Orlando High School', 'Jacksonville High School', 'St. Petersburg High School', 'Hialeah High School', 'Tallahassee High School', 'Fort Lauderdale High School', 'Cape Coral High School', 'Pembroke Pines High School', 'Hollywood High School', 'Gainesville High School'],
    'New York': ['Stuyvesant High School', 'Bronx High School of Science', 'Brooklyn Technical High School', 'LaGuardia High School', 'Townsend Harris High School', 'Staten Island Technical High School', 'Queens High School for the Sciences', 'High School for Mathematics Science and Engineering', 'Eleanor Roosevelt High School', 'Midwood High School', 'Forest Hills High School', 'Benjamin N. Cardozo High School'],
    'Pennsylvania': ['Central High School', 'Northeast High School', 'South Philadelphia High School', 'West Philadelphia High School', 'Masterman School', 'Science Leadership Academy', 'Pittsburgh High School', 'Allentown High School', 'Erie High School', 'Scranton High School', 'Reading High School', 'Bethlehem High School'],
    'Illinois': ['Walter Payton College Prep', 'Northside College Prep', 'Jones College Prep', 'Whitney M. Young Magnet High School', 'Lincoln Park High School', 'Lane Technical High School', 'Von Steuben Metropolitan Science Center', 'Taft High School', 'Roosevelt High School', 'Schurz High School', 'Steinmetz College Prep', 'Foreman High School'],
    'Ohio': ['Walnut Hills High School', 'School for Creative and Performing Arts', 'Hughes STEM High School', 'Cleveland School of the Arts', 'John Hay High School', 'Columbus Alternative High School', 'Toledo School for the Arts', 'Akron Early College High School', 'Dayton Early College Academy', 'Youngstown Early College', 'Canton McKinley High School', 'Massillon Washington High School'],
    'Georgia': ['North Atlanta High School', 'Grady High School', 'Midtown High School', 'Maynard Jackson High School', 'Benjamin E. Mays High School', 'Charles Drew High School', 'Frederick Douglass High School', 'Jean Childs Young Middle School', 'KIPP Atlanta Collegiate', 'Atlanta Classical Academy', 'Coretta Scott King Young Women\'s Leadership Academy', 'B.E.S.T. Academy'],
    'North Carolina': ['East Mecklenburg High School', 'Myers Park High School', 'Independence High School', 'Providence High School', 'South Mecklenburg High School', 'West Charlotte High School', 'Olympic High School', 'Hough High School', 'Mallard Creek High School', 'North Mecklenburg High School', 'Rocky River High School', 'Vance High School'],
    'Michigan': ['Cass Technical High School', 'Renaissance High School', 'Martin Luther King Jr. High School', 'Osborn High School', 'Pershing High School', 'Southeastern High School', 'Western International High School', 'East English Village Preparatory Academy', 'Mumford High School', 'Denby High School', 'Finney High School', 'Ford High School']
}

# Generate name based on gender
def generate_name(gender):
    return fake.name_male() if gender == "Male" else fake.name_female()

# Generate random birth date in 2010
def generate_birth_date_2010():
    start_date = datetime(2010, 1, 1)
    end_date = datetime(2010, 12, 31)
    days_between = (end_date - start_date).days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

# Generate address
def generate_address():
    return fake.address().replace('\n', ', ')

# Generate high school
def generate_high_school():
    state = random.choice(list(HIGH_SCHOOLS.keys()))
    school = random.choice(HIGH_SCHOOLS[state])
    return f"{school}, {state}"

# Generate single profile
def generate_demographic_profile(gender):
    return {
        'Name': generate_name(gender),
        'Date of Birth': generate_birth_date_2010().strftime('%Y-%m-%d'),
        'Address': generate_address(),
        'High School': generate_high_school()
    }

# Convert DataFrame to CSV
def convert_to_csv(profiles_df):
    output = io.StringIO()
    profiles_df.to_csv(output, index=False)
    return output.getvalue()

# ---- STREAMLIT APP ----
def run_streamlit_app():
    import streamlit as st
    st.set_page_config(page_title="Evolveme Profiles Generator", page_icon="👥", layout="wide")
    st.title("Evolveme Profiles Generator")
    st.markdown("Generate random profiles")
    
    st.sidebar.header("⚙️ Generation Settings")
    generated_for = st.sidebar.text_input("Who are you generating this data for? (e.g., 'John Doe')", placeholder="Enter name ")
    gender = st.sidebar.radio("Select Gender:", ["Male", "Female"])
    num_records = st.sidebar.number_input("Number of profiles to generate:", min_value=1, max_value=10000, value=10, step=1)
    generate_button = st.sidebar.button("🎲 Generate Profiles", type="primary")
    
    if generate_button:
        if not generated_for:
            st.error("Please specify who you are generating this data for.")
            return

        st.success(f"Generating {num_records} {gender.lower()} demographic profiles for: **{generated_for}**")
        progress_bar = st.progress(0)
        status_text = st.empty()
        profiles = []
        for i in range(num_records):
            profiles.append(generate_demographic_profile(gender))
            progress = (i + 1) / num_records
            progress_bar.progress(progress)
            status_text.text(f'Generating profile {i + 1} of {num_records}...')
        progress_bar.empty()
        status_text.empty()
        df = pd.DataFrame(profiles)
        st.success(f"✅ Successfully generated {num_records} profiles for **{generated_for}**!")
        st.subheader("📊 Generated Profiles")
        st.dataframe(df, use_container_width=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Total Profiles", len(df))
        with col2: st.metric("States Represented", len(set([school.split(', ')[-1] for school in df['High School']])))
        with col3: st.metric("Unique Schools", len(df['High School'].unique()))
        with col4: st.metric("Birth Months", pd.to_datetime(df['Date of Birth']).dt.month.nunique())
        st.subheader("💾 Download Data")
        csv_data = convert_to_csv(df)
        st.download_button(
            label="📥 Download as CSV",
            data=csv_data,
            file_name=f"{generated_for.replace(' ', '_')}.csv",
            mime="text/csv"
        )
        with st.expander("🔍 View Sample Profile Details"):
            if len(df) > 0:
                sample_profile = df.iloc[random.randint(0, len(df) - 1)]
                st.write(f"**Name:** {sample_profile['Name']}")
                st.write(f"**Date of Birth:** {sample_profile['Date of Birth']}")
                st.write(f"**Address:** {sample_profile['Address']}")
                st.write(f"**High School:** {sample_profile['High School']}")
    else:
        st.info("👈 Use the sidebar to configure and generate the profiles")

# ---- BARE MODE ----
def run_bare_mode():
    generated_for = input("Who are you generating this data for? (e.g., Jane Doe): ").strip()
    while not generated_for:
        generated_for = input("Please enter a valid name: ").strip()

    gender = input("Select Gender (Male/Female): ").strip().capitalize()
    while gender not in ["Male", "Female"]:
        gender = input("Invalid input. Please enter Male or Female: ").strip().capitalize()

    try:
        num_records = int(input("Number of profiles to generate (1-10000): ").strip())
        if num_records < 1 or num_records > 10000:
            raise ValueError
    except ValueError:
        print("Invalid number. Defaulting to 10.")
        num_records = 10

    profiles = [generate_demographic_profile(gender) for _ in range(num_records)]
    df = pd.DataFrame(profiles)
    file_name = f"{generated_for.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(file_name, index=False)
    print(f"\n✅ Successfully generated {num_records} {gender.lower()} profiles for '{generated_for}'.")
    print(f"📁 File saved as: {file_name}")

# ---- ENTRY POINT ----
if __name__ == "__main__":
    if "--bare" in sys.argv:
        run_bare_mode()
    else:
        run_streamlit_app()
