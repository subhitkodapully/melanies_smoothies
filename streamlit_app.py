# Import python packages
import streamlit as st
# from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col 
from snowflake.snowpark.functions import col, when_matched
import pandas as pd
import requests

# Write directly to the app
st.title(f" :cup_with_straw: Customize Your Smoothies :cup_with_straw:")
st.write(
    """ Choose the fruits you want in your Soomthie!    
    """
)
