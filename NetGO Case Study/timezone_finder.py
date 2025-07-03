from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import pytz
from typing import Optional, Tuple
import pandas as pd

def get_timezone(country: str, city: str, zipcode: str, street: str = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Get timezone information for a given location.
    
    Args:
        country (str): Country name
        city (str): City name
        zipcode (str): Postal/ZIP code
        street (str, optional): Street address. Defaults to None.
        
    Returns:
        Tuple[Optional[str], Optional[str]]: A tuple containing (timezone_name, error_message)
        If successful, error_message will be None
        If failed, timezone_name will be None and error_message will contain the error
    """
    try:
        # Initialize the geocoder
        geolocator = Nominatim(user_agent="timezone_finder")
        
        # Create the location string with street if provided
        location_parts = []
        if street:
            location_parts.append(street)
        location_parts.extend([zipcode, city, country])
        location_str = ", ".join(location_parts)
        
        # Get the location
        location = geolocator.geocode(location_str)
        
        if location is None:
            return None, f"Could not find location for {location_str}"
        
        # Initialize TimezoneFinder
        tf = TimezoneFinder()
        
        # Get timezone name
        timezone_name = tf.timezone_at(lat=location.latitude, lng=location.longitude)
        
        if timezone_name is None:
            return None, f"Could not determine timezone for {location_str}"
        
        # Get timezone object
        timezone = pytz.timezone(timezone_name)
        
        return timezone_name, None
        
    except Exception as e:
        return None, f"Error occurred: {str(e)}"

def apply_timezone_to_df(df: pd.DataFrame, country_col: str, city_col: str, zipcode_col: str, street_col: str = None) -> pd.DataFrame:
    """
    Apply timezone finding to a DataFrame.
    
    Args:
        df (pd.DataFrame): Input DataFrame
        country_col (str): Name of the country column
        city_col (str): Name of the city column
        zipcode_col (str): Name of the zipcode column
        street_col (str, optional): Name of the street column. Defaults to None.
        
    Returns:
        pd.DataFrame: DataFrame with added timezone and timezone_error columns
    """
    # Create a copy of the DataFrame to avoid modifying the original
    result_df = df.copy()
    
    # Apply the get_timezone function to each row
    timezone_results = result_df.apply(
        lambda row: get_timezone(
            row[country_col],
            row[city_col],
            row[zipcode_col],
            row[street_col] if street_col else None
        ),
        axis=1
    )
    
    # Split the results into timezone and error columns
    result_df['timezone'] = timezone_results.apply(lambda x: x[0])
    result_df['timezone_error'] = timezone_results.apply(lambda x: x[1])
    
    return result_df

# Example usage
if __name__ == "__main__":
    # Example DataFrame
    test_data = {
        'street': ['350 5th Ave', '10 Downing Street', '1-1-1 Chiyoda'],
        'country': ['United States', 'United Kingdom', 'Japan'],
        'city': ['New York', 'London', 'Tokyo'],
        'zipcode': ['10001', 'SW1A 1AA', '100-0001']
    }
    test_df = pd.DataFrame(test_data)
    
    # Apply timezone finding to the DataFrame
    result_df = apply_timezone_to_df(
        test_df,
        country_col='country',
        city_col='city',
        zipcode_col='zipcode',
        street_col='street'
    )
    print("\nDataFrame with timezone information:")
    print(result_df) 