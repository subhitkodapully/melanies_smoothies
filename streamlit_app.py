# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col 
import pandas as pd
import requests

# Write directly to the app
st.title(f" :cup_with_straw: Customize Your Smoothies :cup_with_straw:")
st.caption("Choose the fruits you want in your smoothie.")

# Connection + Session (robust)
@st.cache_resource(show_spinner="Connecting to Snowflake…")
def get_session():
    try:
        conn = st.connection("snowflake", type="snowflake")  # explicit type
        return conn.session()  # requires snowflake-snowpark-python installed
    except Exception as e:
        st.error(
            "Snowflake connection failed. Check .streamlit/secrets.toml, package versions, and network access."
        )
        st.exception(e)
        st.stop()

session = get_session()

name_on_order = st.text_input("Name on Smoothie:")
display = st.session_state.get("name_on_order", "")
if display:
    st.markdown(f"The name on the smoothie will be **{display}**")
else:
    st.caption("Enter a name above to continue.")



# my_dataframe = session.table("smoothies.public.fruit_options").select(col('fruit_name'),col('search_on'))
# st.dataframe(data=my_dataframe, width=True)

# Convert the Snowpark Dataframe to a Pandas Dataframe so we can use the LOC function
my_dataframe = session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS").select("FRUIT_ID","FRUIT_NAME","SEARCH_ON")
pd_df = my_dataframe.limit(1000).to_pandas()


# pd_df = my_dataframe.to_pandas()
# st.dataframe(pd_df)
# st.stop()

# ingredients_list = st.multiselect(
#    'Choose upto 5 ingredients:'
#    ,my_dataframe
#    ,max_selections = 5
# )

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=sorted(my_dataframe["FRUIT_NAME"].dropna().unique().tolist()),
    max_selections=5,
    key="ingredients_names",
)



name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on the smoothie will be", name_on_order)



if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        search_on=pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        # st.write('The search value for ', fruit_chosen,' is ', search_on, '.')
    
        st.subheader(fruit_chosen + ' Nutrition Information')
        smoothiefruit_response = requests.get("https://fruityvice.com/api/api/fruit/" + search_on)
        sf_df = st.dataframe(data=smoothiefruit_response.json(), use_container_width=True)
                     
        smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")
        sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
        st.stop()


    
# st.write(ingredients_list)
# st.text(ingredients_list)
    
# st.write("ingredients_string=" + ingredients_string)

my_insert_statement = """ insert into smoothies.public.orders(ingredients,name_on_order) values ('""" + ingredients_string + """','""" +name_on_order+ """') """


st.write("my_insert_statement = " + my_insert_statement)

time_to_insert = st.button('Submit Button')

if time_to_insert:
    session.sql(my_insert_statement).collect()
    st.success('Your smoothie is ordered!',icon="✅")        

#    if  ingredients_string:
#        session.sql(my_insert_statement).collect()   
#        st.success('Your smoothie is ordered!', '""" +name_on_order+ """' ,icon="✅")
