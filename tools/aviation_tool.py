import os
import re
import requests
import airportsdata
import pycountry
from dotenv import load_dotenv

load_dotenv()

# AviationStack API credentials and configuration
API_KEY = (
    os.getenv("AVIATIONSTACK_API_KEY")
    or os.getenv("AVIATIONSTAck_API_KEY")
    or os.getenv("AVIATION_API_KEY")
    or ""
)

DEFAULT_ORIGIN_IATA = os.getenv("DEFAULT_ORIGIN_IATA", "DEL")

# Note: AviationStack free tier only supports HTTP
BASE_URL = "http://api.aviationstack.com/v1/flights"

# Load airport database keyed by IATA codes
AIRPORTS = airportsdata.load("IATA")
AIRPOTS = AIRPORTS  # alias for backwards compatibility

COUNTRY_ALIAS = {
    # North America
    "USA": "United States",
    "US": "United States",
    "AMERICA": "United States",
    "CAN": "Canada",
    "MEX": "Mexico",

    # Europe
    "UK": "United Kingdom",
    "GB": "United Kingdom",
    "BRITAIN": "United Kingdom",
    "GER": "Germany",
    "DE": "Germany",
    "FRA": "France",
    "FR": "France",
    "ITA": "Italy",
    "ESP": "Spain",
    "NED": "Netherlands",
    "RUS": "Russia",

    # Asia & Pacific
    "IND": "India",
    "IN": "India",
    "CHN": "China",
    "JPN": "Japan",
    "JP": "Japan",
    "KOR": "South Korea",
    "AUS": "Australia",
    "OZ": "Australia",
    "NZ": "New Zealand",
    "UAE": "United Arab Emirates",
    "SA": "Saudi Arabia",
    "BD": "Bangladesh",
    "SGP": "Singapore",
    "SG": "Singapore",

    # South America & Africa
    "BRA": "Brazil",
    "ARG": "Argentina",
    "RSA": "South Africa",
    "EGY": "Egypt",
}

COUNTRY_MAIN_AIRPORT = {
    # Asia & Pacific
    "IND": "DEL",  # Indira Gandhi International Airport (Delhi)
    "IN": "DEL",
    "INDIA": "DEL",
    "BD":  "DAC",  # Hazrat Shahjalal International Airport (Dhaka)
    "CHN": "PEK",  # Beijing Capital International Airport
    "JPN": "HND",  # Tokyo Haneda Airport
    "JP":  "HND",
    "KOR": "ICN",  # Incheon International Airport (Seoul)
    "SGP": "SIN",  # Singapore Changi Airport
    "SG":  "SIN",
    "SINGAPORE": "SIN",
    "THA": "BKK",  # Suvarnabhumi Airport (Bangkok)
    "THAILAND": "BKK",
    "UAE": "DXB",  # Dubai International Airport
    "DUBAI": "DXB",
    "SA":  "JED",  # King Abdulaziz International Airport (Jeddah)
    "AUS": "SYD",  # Sydney Kingsford Smith Airport
    "AUSTRALIA": "SYD",
    "NZ":  "AKL",  # Auckland Airport
    "MYS": "KUL",  # Kuala Lumpur International Airport
    "MALAYSIA": "KUL",
    "IDN": "CGK",  # Soekarno-Hatta International Airport (Jakarta)
    "INDONESIA": "CGK",
    "BALI": "DPS", # Ngurah Rai International Airport

    # North & South America
    "USA": "JFK",  # John F. Kennedy International Airport (New York)
    "US":  "JFK",
    "CAN": "YYZ",  # Toronto Pearson International Airport
    "MEX": "MEX",  # Mexico City International Airport
    "BRA": "GRU",  # São Paulo/Guarulhos International Airport
    "ARG": "EZE",  # Ezeiza International Airport (Buenos Aires)

    # Europe
    "UK":  "LHR",  # London Heathrow Airport
    "GB":  "LHR",
    "FRA": "CDG",  # Charles de Gaulle Airport (Paris)
    "FR":  "CDG",
    "FRANCE": "CDG",
    "GER": "FRA",  # Frankfurt Airport
    "DE":  "FRA",
    "GERMANY": "FRA",
    "ITA": "FCO",  # Leonardo da Vinci–Fiumicino Airport (Rome)
    "ITALY": "FCO",
    "ESP": "MAD",  # Adolfo Suárez Madrid–Barajas Airport
    "SPAIN": "MAD",
    "NED": "AMS",  # Amsterdam Airport Schiphol
    "NETHERLANDS": "AMS",
    "RUS": "SVO",  # Sheremetyevo International Airport (Moscow)
    "TUR": "IST",  # Istanbul Airport
    "TURKEY": "IST",

    # Africa
    "RSA": "JNB",  # O. R. Tambo International Airport (Johannesburg)
    "EGY": "CAI",  # Cairo International Airport
    "KEN": "NBO",  # Jomo Kenyatta International Airport (Nairobi)
}

POPULAR_CITIES = {
    # India
    "delhi": "DEL",
    "new delhi": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bangalore": "BLR",
    "bengaluru": "BLR",
    "chennai": "MAA",
    "madras": "MAA",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "hyderabad": "HYD",
    "goa": "GOI",
    "ahmedabad": "AMD",
    "pune": "PNQ",
    "jaipur": "JAI",
    "kochi": "COK",
    "cochin": "COK",
    # Global
    "singapore": "SIN",
    "dubai": "DXB",
    "bangkok": "BKK",
    "kuala lumpur": "KUL",
    "phuket": "HKT",
    "bali": "DPS",
    "doha": "DOH",
    "colombo": "CMB",
    "kathmandu": "KTM",
    "male": "MLE",
    "maldives": "MLE",
    "london": "LHR",
    "paris": "CDG",
    "tokyo": "HND",
    "new york": "JFK",
    "nyc": "JFK",
    "san francisco": "SFO",
    "toronto": "YYZ",
    "sydney": "SYD",
    "melbourne": "MEL",
    "rome": "FCO",
    "amsterdam": "AMS",
    "frankfurt": "FRA",
    "istanbul": "IST",
    "hong kong": "HKG"
}

def clean_text(text: str) -> str:
    """
    Cleans the input query by removing special characters and common stop words.
    """
    if not text or not isinstance(text, str):
        return ""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    stop_words = [
        "flight", "flights", "ticket", "tickets", "trip", "travel",
        "plan", "complete", "days", "day", "including", "hotel",
        "hotels", "sightseeing", "under", "budget", "info", "information",
        "please", "find", "show", "search", "give", "me", "want", "book"
    ]
    words = [w for w in text.split() if w not in stop_words]
    return " ".join(words).strip()

def resolve_airport(location: str) -> str | None:
    """
    Resolves a country code, country name, city, or IATA code to a 3-letter IATA airport code.
    """
    if not location or not isinstance(location, str):
        return None

    raw = location.strip().lower()
    upper = raw.upper()

    # 1. Direct country main airport match (e.g. IND -> DEL, SGP -> SIN)
    if upper in COUNTRY_MAIN_AIRPORT:
        return COUNTRY_MAIN_AIRPORT[upper]

    # 2. Known popular city match (e.g. delhi -> DEL, singapore -> SIN)
    if raw in POPULAR_CITIES:
        return POPULAR_CITIES[raw]

    # 3. Direct valid IATA code in airports dataset (e.g. DEL, SIN, JFK)
    if len(upper) == 3 and upper in AIRPORTS:
        return upper

    # 4. Search in airportsdata city fields
    for code, data in AIRPORTS.items():
        city = (data.get("city") or "").lower()
        if city and (city == raw or raw == city.split()[0]):
            return code

    # 5. Fuzzy country match using pycountry
    try:
        c_matches = pycountry.countries.search_fuzzy(raw)
        if c_matches:
            c = c_matches[0]
            for code_attr in ("alpha_3", "alpha_2"):
                val = getattr(c, code_attr, None)
                if val and val in COUNTRY_MAIN_AIRPORT:
                    return COUNTRY_MAIN_AIRPORT[val]
    except Exception:
        pass

    # 6. Fallback: check individual words/tokens
    for token in raw.split():
        if token in POPULAR_CITIES:
            return POPULAR_CITIES[token]
        if token.upper() in COUNTRY_MAIN_AIRPORT:
            return COUNTRY_MAIN_AIRPORT[token.upper()]
        if len(token) == 3 and token.upper() in AIRPORTS:
            return token.upper()

    return None

def extract_route(query: str) -> tuple[str | None, str | None]:
    """
    Extracts origin and destination from common travel query patterns.
    Examples:
      - 'plan a trip from ind to singapore' -> ('ind', 'singapore')
      - 'flights to singapore from delhi' -> ('delhi', 'singapore')
      - 'delhi to singapore' -> ('delhi', 'singapore')
      - 'trip to singapore' -> (None, 'singapore')
    """
    if not query:
        return None, None

    q = query.lower().strip()

    # Pattern 1: from <origin> to <destination>
    m1 = re.search(r"from\s+([a-z0-9\s]+?)\s+to\s+([a-z0-9\s]+)", q)
    if m1:
        return m1.group(1).strip(), m1.group(2).strip()

    # Pattern 2: to <destination> from <origin>
    m2 = re.search(r"to\s+([a-z0-9\s]+?)\s+from\s+([a-z0-9\s]+)", q)
    if m2:
        return m2.group(2).strip(), m2.group(1).strip()

    # Pattern 3: <origin> to <destination>
    m3 = re.search(r"([a-z0-9\s]+?)\s+to\s+([a-z0-9\s]+)", q)
    if m3:
        return m3.group(1).strip(), m3.group(2).strip()

    # Pattern 4: to <destination>
    m4 = re.search(r"to\s+([a-z0-9\s]+)", q)
    if m4:
        return None, m4.group(1).strip()

    return None, None

def flight_search(query: str = "", origin: str = None, destination: str = None, limit: int = 5) -> str:
    """
    Searches flights using the AviationStack API for queries like:
    'plan a trip from ind to singapore', or explicit origin and destination.

    Returns a clean markdown formatted string with flight details.
    """
    raw_origin = origin
    raw_dest = destination

    # Extract route from query if not explicitly passed
    if not raw_origin or not raw_dest:
        ext_orig, ext_dest = extract_route(query)
        raw_origin = raw_origin or ext_orig
        raw_dest = raw_dest or ext_dest

    # If destination couldn't be parsed from 'to ...', try clean_text on query
    if not raw_dest and query:
        raw_dest = clean_text(query)

    # Resolve origin airport code
    dep_iata = resolve_airport(raw_origin) if raw_origin else None
    if not dep_iata:
        dep_iata = resolve_airport(DEFAULT_ORIGIN_IATA) or "DEL"

    # Resolve destination airport code
    arr_iata = resolve_airport(raw_dest) if raw_dest else None
    if not arr_iata:
        return (
            f"Could not identify destination airport from query: '{query}'. "
            "Please specify a valid destination city or country (e.g., Singapore, Dubai, London)."
        )

    if not API_KEY:
        return "AviationStack API key is missing. Please set AVIATIONSTACK_API_KEY in your .env file."

    params = {
        "access_key": API_KEY,
        "dep_iata": dep_iata,
        "arr_iata": arr_iata,
        "limit": limit,
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=15)

        if response.status_code != 200:
            return f"AviationStack API Error ({response.status_code}): {response.text}"

        data = response.json()

        if "error" in data:
            err_msg = data["error"].get("message", "Unknown error")
            return f"AviationStack API Error: {err_msg}"

        flights = data.get("data", [])
        if not flights:
            return (
                f"No scheduled/active flights found between **{dep_iata}** and **{arr_iata}** "
                "at this moment via AviationStack."
            )

        results = [
            f"### Flight Information ({dep_iata} -> {arr_iata})\n"
            f"*Found {len(flights)} flight(s) matching your route:*\n"
        ]

        for i, f in enumerate(flights, 1):
            airline = f.get("airline", {}).get("name") or "Unknown Airline"
            flight_info = f.get("flight", {})
            flight_num = flight_info.get("iata") or flight_info.get("number") or "N/A"
            status = (f.get("flight_status") or "Scheduled").capitalize()

            dep = f.get("departure", {})
            arr = f.get("arrival", {})

            dep_airport = dep.get("airport") or dep_iata
            arr_airport = arr.get("airport") or arr_iata

            dep_time = dep.get("scheduled") or "N/A"
            arr_time = arr.get("scheduled") or "N/A"

            # Clean time format if ISO timestamp
            if "T" in dep_time:
                dep_time = dep_time.replace("T", " ").split("+")[0]
            if "T" in arr_time:
                arr_time = arr_time.replace("T", " ").split("+")[0]

            dep_terminal = dep.get("terminal")
            arr_terminal = arr.get("terminal")
            terminal_info = []
            if dep_terminal:
                terminal_info.append(f"Dep Terminal: {dep_terminal}")
            if arr_terminal:
                terminal_info.append(f"Arr Terminal: {arr_terminal}")
            term_str = f" | {', '.join(terminal_info)}" if terminal_info else ""

            flight_block = (
                f"{i}. **{airline}** (`{flight_num}`)\n"
                f"   - **Route:** {dep_airport} ({dep_iata}) -> {arr_airport} ({arr_iata})\n"
                f"   - **Departure:** {dep_time} UTC{term_str}\n"
                f"   - **Arrival:** {arr_time} UTC\n"
                f"   - **Status:** {status}"
            )
            results.append(flight_block)

        return "\n\n".join(results)

    except Exception as e:
        return f"Error during flight search: {str(e)}"

# Aliases for easy importing across the project
aviation_flight_search = flight_search
get_flight_details = flight_search
