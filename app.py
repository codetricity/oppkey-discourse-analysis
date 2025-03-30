import streamlit as st
import pandas as pd
from streamlit_pdf_viewer import pdf_viewer
import matplotlib.pyplot as plt
from datetime import datetime
import pytz
import pydeck as pdk
import os
from pathlib import Path
import altair as alt

# Set page config including browser tab title
st.set_page_config(
    page_title="Oppkey Lead Platform",
    page_icon="📊",
    layout="wide"
)

# Password Protection
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == st.secrets["passwords"]["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Please enter the password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input(
            "Please enter the password", 
            type="password", 
            on_change=password_entered, 
            key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if not check_password():
    st.stop()  # Do not continue if check_password is not True.

# Define timezone options
TIMEZONE_OPTIONS = {
    "UTC": "UTC",
    "United States (Pacific)": "America/Los_Angeles",
    "United States (Mountain)": "America/Denver",
    "United States (Central)": "America/Chicago",
    "United States (Eastern)": "America/New_York",
    "Japan": "Asia/Tokyo",
    "India": "Asia/Kolkata",
    "United Kingdom": "Europe/London",
    "European Union (Central)": "Europe/Paris",
    "Australia (Sydney)": "Australia/Sydney"
}

# Initialize session state for PDF viewers
if 'show_pdf1' not in st.session_state:
    st.session_state.show_pdf1 = False
if 'show_pdf2' not in st.session_state:
    st.session_state.show_pdf2 = False

with st.sidebar:
    # Add this line to make the sidebar collapsed by default
    st.markdown('<style>#root > div:nth-child(1) > div.withScreencast > div > div > div > section.css-163ttbj.e1fqkh3o11 {visibility: collapse;} </style>', unsafe_allow_html=True)
    
    st.header("Feedback Reports")
    
    # Get list of markdown files in feedback directory
    feedback_dir = Path("./feedback")
    markdown_files = list(feedback_dir.glob("*.md"))
    
    # Create buttons for each markdown file
    for md_file in markdown_files:
        if st.button(md_file.stem.replace("_", " ").title()):
            with open(md_file, "r") as f:
                markdown_content = f.read()
            # Show the markdown content in the main area
            st.markdown(markdown_content)
            # Add a divider for better visual separation
            st.divider()

st.title("360Camera B2B Sales Leads")


# users_org_data = pd.read_csv("users_org.csv")
# users_no_org_data = pd.read_csv("no-org.csv")
# users_no_org2_data = pd.read_csv("no-org2.csv")

# Read data from Google Drive
file_id_1 = st.secrets["data"]["gdrive_file_id_1"]
file_id_2 = st.secrets["data"]["gdrive_file_id_2"]
file_id_3 = st.secrets["data"]["gdrive_file_id_3"]

# Create URLs for each file
url_1 = f"https://docs.google.com/spreadsheets/d/{file_id_1}/export?format=csv"
url_2 = f"https://docs.google.com/spreadsheets/d/{file_id_2}/export?format=csv"
url_3 = f"https://docs.google.com/spreadsheets/d/{file_id_3}/export?format=csv"

# Read the CSV files from Google Drive
users_org_data = pd.read_csv(url_1)
users_no_org_data = pd.read_csv(url_2)
users_no_org2_data = pd.read_csv(url_3)

all_data = pd.concat([users_org_data, users_no_org_data, users_no_org2_data])
all_data['organization'] = all_data['organization'].replace(
    ['x', 'a', 'no', 'tests', 'none', ' ', '--', 'none none'], 
    None
)

filtered_data = all_data[~all_data['organization'].isin([None])]

# Total number of users
unique_user_ids = all_data['username'].dropna().nunique() 

# Total org
unique_orgs = filtered_data['organization'].dropna().nunique()


# Total countries
def extract_countries(location):
    if isinstance(location, str):
        parts = location.split(',')
        if len(parts) == 0:
            return parts[0]
        return parts[-1]
    return None


all_data['country'] = all_data['last_ip_country'].apply(extract_countries)
users_per_country = all_data.groupby('country')['user_id'].nunique()
countries = users_per_country.dropna().nunique()

# Writing data
col1, col2, col3 = st.columns(3)
col1.metric(label="360 Camera Devs", value=unique_user_ids, border=True)
col2.metric(label="Unique Organizations", value=unique_orgs, border=True)

with col3:
    st.markdown(
        f"""
        <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 10px; border: 1px solid #eee; border-radius: 8px;'>
            <div style='font-size: 18px; color: gray;'>Countries</div>
            <div style='font-size: 36px; font-weight: bold; color: black;'>{countries}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Bar chart with country
st.write("Top 10 Countries With Most Users")

# Prepare the data
top_countries = users_per_country.nlargest(10).reset_index()
top_countries.columns = ['Country', 'Users']

# Sort by Users ascending for left-to-right
top_countries = top_countries.sort_values('Users', ascending=False)

# Create horizontal bar chart
chart = alt.Chart(top_countries).mark_bar().encode(
    x='Users:Q',
    y=alt.Y('Country:N', sort=top_countries['Country'].tolist())
).properties(
    height=500,
    width=700
)

st.altair_chart(chart)

# Add the 9 years image at 60% width
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.image("images/9_years.png", use_container_width=True)

st.write("9 years of businesses building 360 camera products")


# B2B Sales Leads by Geo section moved to top
st.header("B2B Sales Leads by Geo")


# Add region filter dropdown
region_filter = st.selectbox(
    "Filter by region",
    ["All Regions", "United States", "European Union", "Japan", "India"]
)

# Create a dataframe with lat/long and tooltip info for mapping
map_data = all_data[['last_ip_latitude', 'last_ip_longitude', 'last_ip_country', 
                     'last_ip_is_eu_member', 'organization', 'last_ip_city', 
                     'last_ip_state', 'username', 'posts_read']].copy()
map_data.columns = ['latitude', 'longitude', 'country', 'is_eu', 
                    'organization', 'city', 'state', 'username', 'posts_read']  # Rename for clarity

# Apply region filters
if region_filter == "United States":
    map_data = map_data[map_data['country'] == 'United States']
elif region_filter == "European Union":
    map_data = map_data[map_data['is_eu'] == True]
elif region_filter == "Japan":
    map_data = map_data[map_data['country'] == 'Japan']
elif region_filter == "India":
    map_data = map_data[map_data['country'] == 'India']

# Keep all columns for tooltip display
map_data = map_data.dropna(subset=['latitude', 'longitude'])

# Add organization_html to the data
map_data['organization_html'] = map_data['organization'].apply(
    lambda x: f"<b>Organization:</b> {x}<br/>" if pd.notna(x) else ""
)

# Create the deck map
view_state = pdk.ViewState(
    latitude=20,
    longitude=0,
    zoom=1,
    pitch=0
)

scatter_layer = pdk.Layer(
    'ScatterplotLayer',
    map_data,
    get_position=['longitude', 'latitude'],
    get_color=[255, 0, 0, 140],  # Red with some transparency
    get_radius=25000,  # Reduced size of the points
    radius_min_pixels=3,  # Minimum radius when zoomed out
    radius_max_pixels=15,  # Maximum radius when zoomed in
    pickable=True,
    auto_highlight=True,
    highlight_color=[255, 0, 0, 200]  # Highlight color when hovering
)

# Create and display the map
deck = pdk.Deck(
    layers=[scatter_layer],
    initial_view_state=view_state,
    map_style='mapbox://styles/mapbox/light-v9',
    tooltip={
        "html": "<b>Username:</b> {username}<br/>"
                "{organization_html}"
                "<b>Location:</b> {city}, {state}, {country}<br/>"
                "<b>Posts Read:</b> {posts_read}",
        "style": {
            "backgroundColor": "white",
            "color": "black",
            "fontSize": "0.8em",
            "padding": "5px"
        }
    }
)

st.pydeck_chart(deck)

# Show the count of displayed points
st.caption(f"Showing {len(map_data)} locations in {region_filter}")

# Add time-based analysis section
st.header("360 Camera Developer Registration Trends")

# Add the 400 developers image at 60% width
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.image("images/400_developers.png", use_container_width=True)

# Convert created_at to datetime
all_data['created_at'] = pd.to_datetime(all_data['created_at'])

# Get min and max dates for the slider
min_date = all_data['created_at'].min().to_pydatetime()
max_date = all_data['created_at'].max().to_pydatetime()

# Print date range for debugging
st.write(f"Data range: {min_date} to {max_date}")

# Create date range slider
date_range = st.slider(
    "Select Date Range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
    format="YYYY-MM-DD"
)

# Add granularity selector
granularity = st.radio(
    "Select Time Granularity",
    ["Daily", "Monthly"],
    horizontal=True,
    index=1  # Set Monthly as default (index 1)
)

# Filter data based on selected date range
mask = (all_data['created_at'] >= pd.Timestamp(date_range[0])) & (all_data['created_at'] <= pd.Timestamp(date_range[1]))
filtered_time_data = all_data[mask]

# Print filtered data info for debugging
st.write(f"Number of records in selected range: {len(filtered_time_data)}")

# Group by date and count registrations based on selected granularity
if granularity == "Daily":
    registrations = filtered_time_data.groupby(filtered_time_data['created_at'].dt.date).size()
    xlabel = "Date"
else:
    # For monthly view, use start_time of month instead of period to preserve timezone
    registrations = filtered_time_data.groupby(filtered_time_data['created_at'].dt.to_period('M').dt.start_time).size()
    # Format the datetime index to show just year-month
    registrations.index = registrations.index.strftime('%Y-%m')
    xlabel = "Month"

# Create line chart
fig, ax = plt.subplots(figsize=(10, 6))
registrations.plot(kind='line', ax=ax, marker='o')
plt.title(f'{granularity} Developer Registrations')
plt.xlabel(xlabel)
plt.ylabel('Number of Registrations')
plt.grid(True)
plt.xticks(rotation=45)
st.pyplot(fig)

# Print registration counts for debugging
st.write("Registration counts by period:")
st.write(registrations)

# Show summary metrics for the selected period
col1, col2, col3 = st.columns(3)
col1.metric("Total Registrations in Period", len(filtered_time_data))
col2.metric("Average Monthly Registrations", round(len(filtered_time_data) / ((max_date - min_date).days / 30), 1))
col3.metric("Highest Monthly Registrations", registrations.max())

# Additional Analytics Section
st.header("Additional Analytics")

# Add the posts read image at 60% width
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.image("images/read_logged_in.png", use_container_width=True)

# Create tabs for different visualizations
tab1, tab2, tab3 = st.tabs(["Developer Engagement", "Geographic Distribution", "Registration Patterns"])

with tab1:
    # User Engagement Analysis
    st.subheader("Developer Engagement Over Time")
    
    # Show total posts read across all time
    total_posts_read = all_data['posts_read'].sum()
    st.metric("Total Posts Read (All Time)", f"{total_posts_read:,}")
    
    engagement_data = all_data[['created_at', 'posts_read']].copy()
    engagement_data['created_at'] = pd.to_datetime(engagement_data['created_at'])
    engagement_data['date'] = engagement_data['created_at'].dt.date
    
    # Calculate cumulative posts read over time
    daily_posts = engagement_data.groupby('date')['posts_read'].sum()
    cumulative_posts = daily_posts.cumsum()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    cumulative_posts.plot(kind='line', ax=ax, marker='o')
    plt.title('Cumulative Posts Read Over Time')
    plt.xlabel('Date')
    plt.ylabel('Total Posts Read')
    plt.grid(True)
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # Engagement by Region
    st.subheader("Engagement by Region")
    region_engagement = all_data.groupby('country')['posts_read'].mean().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(10, 6))
    region_engagement.head(10).plot(kind='bar', ax=ax)
    plt.title('Top 10 Countries by Average Engagement')
    plt.xlabel('Country')
    plt.ylabel('Average Posts Read')
    plt.xticks(rotation=45)
    st.pyplot(fig)

with tab2:
    # Geographic Distribution
    st.subheader("Registration Density by Country")
    country_counts = all_data['country'].value_counts()
    fig, ax = plt.subplots(figsize=(12, 6))
    country_counts.head(15).plot(kind='bar', ax=ax)
    plt.title('Top 15 Countries by Registration Count')
    plt.xlabel('Country')
    plt.ylabel('Number of Registrations')
    plt.xticks(rotation=45)
    st.pyplot(fig)
    
    # EU vs Non-EU Distribution
    st.subheader("EU vs Non-EU Distribution")
    eu_counts = all_data['last_ip_is_eu_member'].value_counts()
    fig, ax = plt.subplots(figsize=(8, 6))
    eu_counts.plot(kind='pie', autopct='%1.1f%%', ax=ax)
    plt.title('Distribution of EU vs Non-EU Developers')
    plt.axis('equal')
    st.pyplot(fig)

    # US States Distribution
    st.subheader("Top US States Distribution")
    us_data = all_data[all_data['last_ip_country'] == 'United States']
    state_counts = us_data['last_ip_state'].value_counts()
    
    fig, ax = plt.subplots(figsize=(12, 6))
    state_counts.head(15).plot(kind='bar', ax=ax)
    plt.title('Top 15 US States by Registration Count')
    plt.xlabel('State')
    plt.ylabel('Number of Registrations')
    plt.xticks(rotation=45)
    st.pyplot(fig)

with tab3:
    # Registration Time Analysis
    st.subheader("Registration Time Patterns")
    
    # Add timezone selector
    selected_timezone = st.selectbox(
        "Select Timezone",
        list(TIMEZONE_OPTIONS.keys()),
        index=0
    )
    
    # Convert UTC times to selected timezone
    tz = pytz.timezone(TIMEZONE_OPTIONS[selected_timezone])
    try:
        # Try to convert directly if already timezone-aware
        all_data['local_time'] = all_data['created_at'].dt.tz_convert(tz)
    except TypeError:
        # If not timezone-aware, localize to UTC first
        all_data['local_time'] = all_data['created_at'].dt.tz_localize('UTC').dt.tz_convert(tz)
    
    all_data['hour'] = all_data['local_time'].dt.hour
    all_data['day_of_week'] = all_data['local_time'].dt.day_name()
    
    # Hourly distribution
    hourly_registrations = all_data.groupby('hour').size()
    fig, ax = plt.subplots(figsize=(10, 6))
    hourly_registrations.plot(kind='bar', ax=ax)
    plt.title(f'Registrations by Hour of Day ({selected_timezone})')
    plt.xlabel(f'Hour ({selected_timezone})')
    plt.ylabel('Number of Registrations')
    plt.grid(True)
    st.pyplot(fig)
    
    # Day of week distribution
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_registrations = all_data.groupby('day_of_week').size().reindex(day_order)
    fig, ax = plt.subplots(figsize=(10, 6))
    daily_registrations.plot(kind='bar', ax=ax)
    plt.title(f'Registrations by Day of Week ({selected_timezone})')
    plt.xlabel('Day of Week')
    plt.ylabel('Number of Registrations')
    plt.grid(True)
    st.pyplot(fig)

# Add the 700 developers image before B2B Leads Listing
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.image("images/700_developers.png", use_container_width=True)

# Filters section
st.header("B2B Leads Listing")
col1, col2, col3 = st.columns(3)

with col1:
    country_filter = st.text_input("Filter by country:")

with col2:
    show_only_with_org = st.toggle("Show only entries with organizations")

with col3:
    exclude_ricoh_oppkey = st.toggle("Exclude Ricoh and Oppkey")

# Apply filters
filtered_display = all_data.copy()

# Apply organization filter if toggle is on
if show_only_with_org:
    filtered_display = filtered_display[filtered_display['organization'].notna()]

# Apply country filter if there's input
if country_filter:
    filtered_display = filtered_display[filtered_display['country'].str.lower().str.contains(country_filter.lower(), na=False)]

# Exclude Ricoh and Oppkey if toggle is on
if exclude_ricoh_oppkey:
    filtered_display = filtered_display[~filtered_display['organization'].str.lower().str.contains('ricoh|oppkey', case=False, na=False)]

# Create a new column for the links
filtered_display['profile_link'] = filtered_display['username'].apply(
    lambda x: f"https://community.theta360.guide/u/{x}/summary" if pd.notna(x) else ''
)

# Remove specified columns
columns_to_remove = ['user_id', 'Username', 'last_ip_latitude', 'last_ip_longitude', 
                    'registration_ip_longitude', 'hour', 'day_of_week', 
                    'registration_ip_latitude']
filtered_display = filtered_display.drop(columns=columns_to_remove, errors='ignore')

# Reorder columns to show organization, country, state, then name
remaining_columns = filtered_display.columns.tolist()

# Safely remove columns if they exist
for col in ['organization', 'country', 'last_ip_state', 'name', 'profile_link']:
    if col in remaining_columns:
        remaining_columns.remove(col)

new_column_order = ['organization', 'country', 'last_ip_state', 'name', 'profile_link'] + remaining_columns

filtered_display = filtered_display[new_column_order]

# Display filtered data without index
st.dataframe(
    filtered_display, 
    hide_index=True,
    column_config={
        "name": "Name",
        "last_ip_state": "State",
        "profile_link": st.column_config.LinkColumn(
            "Profile",
            help="Click to view user profile",
            width="small",
            display_text="View"
        )
    }
)

# Add the posts read image before Sales Kit Sample
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.image("images/posts_read.png", use_container_width=True)

# View Reports section
st.header("Sales Kit Sample")

# Dropdown for report selection
report_selection = st.selectbox(
    "Select a report to view",
    ["Select a report", "360 Camera Sales Kit", "DeveloperWeek Report", "Close viewer"],
    key="report_selector"
)

# Handle report selection
if report_selection == "360 Camera Sales Kit":
    try:
        pdf_viewer("reports/camera360-sales.pdf", width=1000)
    except Exception as e:
        st.error(f"Error loading PDF: {str(e)}")
elif report_selection == "DeveloperWeek Report":
    try:
        pdf_viewer("reports/360camera-developerweek.pdf", width=1000)
    except Exception as e:
        st.error(f"Error loading PDF: {str(e)}")
elif report_selection == "Close viewer":
    # This will effectively close the viewer by not showing any PDF
    pass
