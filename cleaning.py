import numpy as np
import pandas as pd
from pycountry import countries
from fuzzywuzzy import process

def clean_type(raw_shark_attack_df):
    """
    Cleans the 'Type' column of the shark attack DataFrame.

    This function standardizes the values in the 'Type' column by mapping various
    unconfirmed or questionable entries to 'Unconfirmed', standardizing capitalization,
    and ensuring consistent terminology for attack types like 'Unprovoked', 'Provoked',
    and 'Watercraft'.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.

    Returns:
        pd.DataFrame: A new DataFrame with the 'Type' column cleaned.
    """
    shark_attack_df = raw_shark_attack_df.copy()
    shark_attack_df['Type'] = shark_attack_df['Type'].replace({'?': 'Unconfirmed', 
                                                          'Unverified': 'Unconfirmed', 
                                                          'Invalid': 'Unconfirmed',
                                                          'Questionable': 'Unconfirmed',
                                                          pd.NA: 'Unconfirmed',
                                                          'unprovoked': 'Unprovoked',
                                                          ' Provoked': 'Provoked',
                                                          'Boat': 'Watercraft'})
    return shark_attack_df

def clean_sex(raw_shark_attack_df):
    """
    Cleans the 'Sex' column of the shark attack DataFrame.

    This function standardizes the 'Sex' column by stripping whitespace, converting
    to uppercase, and mapping various non-standard entries to 'M' (Male) or NaN
    for unknown values.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.

    Returns:
        pd.DataFrame: A new DataFrame with the 'Sex' column cleaned.
    """
    shark_attack_df = raw_shark_attack_df.copy()
    shark_attack_df['Sex'] = shark_attack_df['Sex'].str.strip()
    shark_attack_df['Sex'] = shark_attack_df['Sex'].str.upper()
    shark_attack_df['Sex'] = shark_attack_df['Sex'].replace('.', np.nan)
    shark_attack_df['Sex'] = shark_attack_df['Sex'].replace({'LLI': 'M', 
                                                          'M X 2': 'M', 
                                                          'N': 'M',
                                                          '.': np.nan})
    return shark_attack_df

def clean_age(raw_shark_attack_df):
    """
    Cleans the 'Age' column of the shark attack DataFrame.

    This function converts the 'Age' column to a numeric type, coercing any
    non-numeric values to NaN. It then casts the column to an integer type
    that supports missing values.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.

    Returns:
        pd.DataFrame: A new DataFrame with the 'Age' column cleaned.
    """
    shark_attack_df = raw_shark_attack_df.copy()
    shark_attack_df['Age'] = pd.to_numeric(shark_attack_df['Age'], errors='coerce').astype('Int64')
    return shark_attack_df

def drop_useless_columns(raw_shark_attack_df):
    """
    Drops useless columns from the shark attack DataFrame.

    This function removes columns that are not needed for analysis, such as
    'Case Number', 'Name', 'Source', etc.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.

    Returns:
        pd.DataFrame: A new DataFrame with the useless columns removed.
    """
    return raw_shark_attack_df.drop(columns=['Case Number'
                                                    , 'Name'
                                                    , 'Source'
                                                    , 'pdf'
                                                    , 'href formula'
                                                    , 'href', 'Case Number.1'
                                                    , 'original order'
                                                    ,'Unnamed: 21','Unnamed: 22', 'Location', 'Time'
                                                    ], errors='ignore')

def clean_date(raw_shark_attack_df):
    """
    Cleans the date-related columns of the shark attack DataFrame.

    This function extracts the month and year from the 'Date' and 'Year' columns,
    creates new 'Month' and 'Year' columns, and drops the original 'Date' and 'Year' columns.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.

    Returns:
        pd.DataFrame: A new DataFrame with cleaned date columns.
    """
    shark_attack_df = raw_shark_attack_df.copy()
    
    # Extract month from Date column
    shark_attack_df['Month'] = shark_attack_df['Date'].str.extract(r'(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', expand=False)
    
    # Map abbreviated months to full names
    month_map = {'Jan': 'January', 'Feb': 'February', 'Mar': 'March', 'Apr': 'April', 
                 'Jun': 'June', 'Jul': 'July', 'Aug': 'August', 'Sep': 'September', 
                 'Oct': 'October', 'Nov': 'November', 'Dec': 'December'}
    shark_attack_df['Month'] = shark_attack_df['Month'].replace(month_map)
    
    # Clean Year column - convert to integer, handle 0 values
    shark_attack_df['Fixed Year'] = pd.to_numeric(shark_attack_df['Year'], errors='coerce')
    shark_attack_df.loc[shark_attack_df['Fixed Year'] == 0, 'Fixed Year'] = np.nan
    
    # Extract year from Date column when Fixed Year is missing
    date_year = shark_attack_df['Date'].str.extract(r'(\d{4})', expand=False)
    shark_attack_df['Fixed Year'] = shark_attack_df['Fixed Year'].fillna(pd.to_numeric(date_year, errors='coerce')).astype('Int64')

    # drop column 'Year' and 'Date'
    shark_attack_df = shark_attack_df.drop(columns=['Year', 'Date'], errors='ignore')

    # rename 'Fixed Year' to 'Year'
    shark_attack_df = shark_attack_df.rename(columns={'Fixed Year': 'Year'})
    
    return shark_attack_df

def clean_state(raw_shark_attack_df, score_cutoff):
    """
    Cleans the 'State' column of the shark attack DataFrame.

    This function standardizes the 'State' column by using fuzzy matching to correct
    misspellings and variations. It uses a predefined list of states for major
    countries to ensure consistency.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.
        score_cutoff (int): The minimum score for a fuzzy match to be considered valid.

    Returns:
        pd.DataFrame: A new DataFrame with the 'State' column cleaned.
    """
    shark_attack_df = raw_shark_attack_df.copy()
    
    # State mappings for major countries
    state_mappings = {
        'United States': ['Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado', 'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York', 'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming'],
        'Australia': ['New South Wales', 'Victoria', 'Queensland', 'Western Australia', 'South Australia', 'Tasmania', 'Northern Territory', 'Australian Capital Territory'],
        'Canada': ['Alberta', 'British Columbia', 'Manitoba', 'New Brunswick', 'Newfoundland and Labrador', 'Northwest Territories', 'Nova Scotia', 'Nunavut', 'Ontario', 'Prince Edward Island', 'Quebec', 'Saskatchewan', 'Yukon'],
        'Brazil': ['Acre', 'Alagoas', 'Amapá', 'Amazonas', 'Bahia', 'Ceará', 'Distrito Federal', 'Espírito Santo', 'Goiás', 'Maranhão', 'Mato Grosso', 'Mato Grosso do Sul', 'Minas Gerais', 'Pará', 'Paraíba', 'Paraná', 'Pernambuco', 'Piauí', 'Rio de Janeiro', 'Rio Grande do Norte', 'Rio Grande do Sul', 'Rondônia', 'Roraima', 'Santa Catarina', 'São Paulo', 'Sergipe', 'Tocantins']
    }
    
    def match_state(row):
        state = row['State']
        country = row['Country']
        
        if pd.isna(state) or pd.isna(country):
            return state
            
        state = str(state).strip()
        if not state:
            return state
            
        # Get states for the country
        country_states = state_mappings.get(country, [])
        if not country_states:
            return state
            
        # Use fuzzy matching
        match = process.extractOne(state, country_states, score_cutoff=score_cutoff)
        return match[0] if match else state
    
    shark_attack_df['State'] = shark_attack_df.apply(match_state, axis=1)
    return shark_attack_df

def clean_country(raw_shark_attack_df, score_cutoff=80):
    """
    Cleans the 'Country' column of the shark attack DataFrame.

    This function standardizes the 'Country' column by using fuzzy matching to correct
    misspellings and variations. It uses a list of all country names from the
    pycountry library to ensure consistency.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.
        score_cutoff (int): The minimum score for a fuzzy match to be considered valid.

    Returns:
        pd.DataFrame: A new DataFrame with the 'Country' column cleaned.
    """
    shark_attack_df = raw_shark_attack_df.copy()
    
    # Get list of all country names
    country_names = [country.name for country in countries]
    
    def match_country(name):
        if pd.isna(name):
            return name
        name = str(name).strip()
        if not name:
            return name
        
        # Direct replacements for common cases
        replacements = {
            'USA': 'United States',
            'AUSTRALIA': 'Australia',
            'CEYLON (SRI LANKA)': 'Sri Lanka',
            'SOUTH AFRICA': 'South Africa'
        }
        
        if name in replacements:
            return replacements[name]
        
        # Use fuzzy matching for other cases
        match = process.extractOne(name, country_names, score_cutoff=score_cutoff)
        return match[0] if match else name
    
    shark_attack_df['Country'] = shark_attack_df['Country'].apply(match_country)
    return shark_attack_df

def clean_activity(raw_shark_attack_df):
    """
    Cleans the 'Activity' column of the shark attack DataFrame.

    This function categorizes the activities into a predefined set of categories
    such as 'Swimming', 'Surfing', 'Diving', etc. It uses keyword matching and
    fuzzy matching to normalize the activity descriptions.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.

    Returns:
        pd.DataFrame: A new DataFrame with the 'Activity' column cleaned.
    """
    shark_attack_df = raw_shark_attack_df.copy()
    
    # Activity categories and keywords
    activity_map = {
        'Swimming': ['swimming', 'bathing', 'wading', 'floating'],
        'Surfing': ['surfing', 'surf', 'bodyboarding', 'boogie boarding'],
        'Diving': ['diving', 'snorkeling', 'free diving', 'scuba'],
        'Fishing': ['fishing', 'spearfishing', 'angling'],
        'Boating': ['boating', 'sailing', 'kayaking', 'canoeing'],
        'Other': ['walking', 'standing', 'fell overboard', 'unknown']
    }
    
    # Flatten all keywords for fuzzy matching
    all_keywords = [keyword for keywords in activity_map.values() for keyword in keywords]
    
    def normalize_activity(activity):
        if pd.isna(activity):
            return 'Unknown'
        activity = str(activity).lower().strip()
        
        # First try exact keyword matching
        for category, keywords in activity_map.items():
            if any(keyword in activity for keyword in keywords):
                return category
        
        # Try fuzzy matching for unmapped activities
        match = process.extractOne(activity, all_keywords, score_cutoff=60)
        if match:
            matched_keyword = match[0]
            for category, keywords in activity_map.items():
                if matched_keyword in keywords:
                    return category
        
        return 'Other'
    
    shark_attack_df['Activity'] = shark_attack_df['Activity'].apply(normalize_activity)
    return shark_attack_df

def clean_species(raw_shark_attack_df, score_cutoff=70):
    """
    Cleans the 'Species' column of the shark attack DataFrame.

    This function standardizes the shark species names using a predefined list of
    common species. It uses a combination of direct name mapping and fuzzy matching
    to normalize the data.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.
        score_cutoff (int): The minimum score for a fuzzy match to be considered valid.

    Returns:
        pd.DataFrame: A new DataFrame with the 'Species' column cleaned.
    """
    shark_attack_df = raw_shark_attack_df.copy()
    
    # Real shark species list
    shark_species = [
        'Great White Shark', 'Tiger Shark', 'Bull Shark', 'Blacktip Shark', 'Sandbar Shark',
        'Nurse Shark', 'Lemon Shark', 'Hammerhead Shark', 'Mako Shark', 'Blue Shark',
        'Sand Tiger Shark', 'Reef Shark', 'Wobbegong Shark', 'Thresher Shark', 'Dusky Shark',
        'Spinner Shark', 'Silky Shark', 'Bronze Whaler Shark', 'Galapagos Shark', 'Grey Reef Shark',
        'Blacktip Reef Shark', 'Whitetip Reef Shark', 'Caribbean Reef Shark', 'Silvertip Shark',
        'Oceanic Whitetip Shark', 'Porbeagle Shark', 'Basking Shark', 'Whale Shark', 'Goblin Shark',
        'Angel Shark', 'Leopard Shark', 'Dogfish Shark', 'Sevengill Shark', 'Sixgill Shark'
    ]
    
    def normalize_species(species):
        if pd.isna(species):
            return 'Unknown'
        
        species = str(species).strip()
        if not species:
            return 'Unknown'
        
        # Handle invalid/unconfirmed cases
        invalid_terms = ['invalid', 'questionable', 'not confirmed', 'unconfirmed', 'not stated']
        if any(term in species.lower() for term in invalid_terms):
            return 'Unknown'
        
        # Handle size descriptions without species
        if "'" in species or 'm' in species.lower() or 'shark' not in species.lower():
            if 'shark' not in species.lower():
                return 'Unknown'
        
        # Common name mappings
        name_mappings = {
            'white shark': 'Great White Shark',
            'great white': 'Great White Shark',
            'bull shark': 'Bull Shark',
            'tiger shark': 'Tiger Shark',
            'blacktip shark': 'Blacktip Shark',
            'sand tiger': 'Sand Tiger Shark',
            'wobbegong': 'Wobbegong Shark',
            'hammerhead': 'Hammerhead Shark',
            'mako': 'Mako Shark',
            'blue shark': 'Blue Shark',
            'nurse shark': 'Nurse Shark',
            'lemon shark': 'Lemon Shark',
            'spinner shark': 'Spinner Shark',
            'dusky shark': 'Dusky Shark',
            'silky shark': 'Silky Shark',
            'bronze whaler': 'Bronze Whaler Shark',
            'galapagos shark': 'Galapagos Shark',
            'grey reef shark': 'Grey Reef Shark',
            'blacktip reef shark': 'Blacktip Reef Shark',
            'whitetip reef shark': 'Whitetip Reef Shark',
            'caribbean reef shark': 'Caribbean Reef Shark',
            'silvertip shark': 'Silvertip Shark',
            'oceanic whitetip shark': 'Oceanic Whitetip Shark',
            'porbeagle shark': 'Porbeagle Shark',
            'basking shark': 'Basking Shark',
            'whale shark': 'Whale Shark',
            'goblin shark': 'Goblin Shark',
            'angel shark': 'Angel Shark',
            'leopard shark': 'Leopard Shark',
            'dogfish shark': 'Dogfish Shark',
            'sevengill shark': 'Sevengill Shark',
            'sixgill shark': 'Sixgill Shark',
            'reef shark': 'Reef Shark',
            'sandbar shark': 'Sandbar Shark',
            'thresher shark': 'Thresher Shark',
            'reef': 'Reef Shark',
            'sand tiger shark': 'Sand Tiger Shark',
            'sand tiger': 'Sand Tiger Shark',
            'unconfirmed': 'Unknown',
            'Unconfirmed': 'Unknown',
            'unknown': 'Unknown'
        }
        
        species_lower = species.lower()
        for key, value in name_mappings.items():
            if key in species_lower:
                return value
        
        # Fuzzy matching
        match = process.extractOne(species, shark_species, score_cutoff=score_cutoff)
        return match[0] if match else 'Unknown'
    
    # Handle column name with trailing space
    species_col = 'Species ' if 'Species ' in shark_attack_df.columns else 'Species'
    shark_attack_df['Species'] = shark_attack_df[species_col].apply(normalize_species)
    
    # Drop the original column if it had trailing space
    if species_col == 'Species ':
        shark_attack_df = shark_attack_df.drop(columns=['Species '])
    
    return shark_attack_df

def clean_injury(raw_shark_attack_df):
    """
    Cleans the 'Injury' column of the shark attack DataFrame.

    This function categorizes the injuries into a predefined set of body parts
    such as 'Leg / Foot', 'Arm', 'Hand / Fingers', etc. It uses keyword matching
    to normalize the injury descriptions.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.

    Returns:
        pd.DataFrame: A new DataFrame with a 'Body Part' column and the 'Injury' column removed.
    """
    shark_attack_df = raw_shark_attack_df.copy()

    def categorize_body_part(injury):
        injury = str(injury).lower()

        if "leg" in injury or "thigh" in injury or "calf" in injury or "foot" in injury:
            return "Leg / Foot"
        elif "arm" in injury or "bicep" in injury or "wrist" in injury:
            return "Arm"
        elif "hand" in injury or "finger" in injury:
            return "Hand / Fingers"
        elif "shoulder" in injury:
            return "Shoulder"
        elif "abdomen" in injury or "stomach" in injury or "torso" in injury or "body" in injury:
            return "Body / Abdomen"
        elif "head" in injury or "face" in injury or "neck" in injury:
            return "Head / Neck"
        else:
            return "Unspecified / Multiple"
    
    shark_attack_df['Body Part'] = shark_attack_df['Injury'].apply(categorize_body_part)
    shark_attack_df = shark_attack_df.drop(columns=['Injury'], errors='ignore')
    return shark_attack_df

def clean_fatal(raw_shark_attack_df):
    """
    Cleans the 'Fatal Y/N' column of the shark attack DataFrame.

    This function standardizes the 'Fatal Y/N' column by mapping various
    yes/no representations to 'Yes' and 'No', and handling unknown values.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.

    Returns:
        pd.DataFrame: A new DataFrame with the 'Fatal Y/N' column cleaned.
    """
    shark_attack_df = raw_shark_attack_df.copy()
    shark_attack_df['Fatal Y/N'] = shark_attack_df['Fatal Y/N'].fillna('')
    shark_attack_df['Fatal Y/N'] = shark_attack_df['Fatal Y/N'].str.strip().str.upper()
    shark_attack_df['Fatal Y/N'] = shark_attack_df['Fatal Y/N'].replace({
        'Y': 'Yes',
        'Y X 2': 'Yes',
        'F': 'Yes',
        'N': 'No',
        'NQ': 'No'
    })
    shark_attack_df['Fatal Y/N'] = shark_attack_df['Fatal Y/N'].apply(lambda x: x if x in ['Yes', 'No'] else 'Unknown')
    return shark_attack_df

def clean_data(raw_shark_attack_df):
    """
    Performs a full cleaning of the shark attack DataFrame.

    This function applies all the individual cleaning functions to the DataFrame
    in the correct order.

    Args:
        raw_shark_attack_df (pd.DataFrame): The raw DataFrame containing shark attack data.

    Returns:
        pd.DataFrame: A new, fully cleaned DataFrame.
    """
    shark_attack_df = drop_useless_columns(raw_shark_attack_df)
    shark_attack_df = clean_date(shark_attack_df)
    shark_attack_df = clean_sex(shark_attack_df)
    shark_attack_df = clean_age(shark_attack_df)
    shark_attack_df = clean_type(shark_attack_df)
    shark_attack_df = clean_country(shark_attack_df, 60)
    shark_attack_df = clean_state(shark_attack_df, 60)
    shark_attack_df = clean_activity(shark_attack_df)
    shark_attack_df = clean_species(shark_attack_df)
    shark_attack_df = clean_injury(shark_attack_df)
    shark_attack_df = clean_fatal(shark_attack_df)
    return shark_attack_df