# Import python packages
import streamlit as st
# from snowflake.snowpark.context import get_active_session
from snowflake.snowpark.functions import col 
from snowflake.snowpark.functions import when_matched
import pandas as pd
import requests


cnx = st.connection("snowflake")
session = cnx.session()


my_dataframe = session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))
st.dataframe(data=my_dataframe, width=True)

# Write directly to the app
st.title(f" :cup_with_straw: Customize Your Smoothies :cup_with_straw:")
st.write(
    """ Choose the fruits you want in your Soomthie!    
    """
)

# option = st.selectbox(
#    "What is your favorite fruit",
#    ("Banana", "Strawberries", "Peaches"),
#    index=None, )

name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on the smoothie will be", name_on_order)


# Convert the Snowpark Dataframe to a Pandas Dataframe so we can use the LOC function
pd_df = my_dataframe.to_pandas()
# st.dataframe(pd_df)
# st.stop()


ingredients_list = st.multiselect(
    'Choose upto 5 ingredients:'
    ,my_dataframe
    ,max_selections = 5
)

if ingredients_list:
    ingredients_string = ''

    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ' '

        search_on=pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        # st.write('The search value for ', fruit_chosen,' is ', search_on, '.')
    
        st.subheader(fruit_chosen + ' Nutrition Information')
        fruityvice_response = requests.get("https://fruityvice.com/api/api/fruit/" + search_on)
        fv_df = st.dataframe(data=fruityvice_response.json, use_container_width=True)
                     
        smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")
        sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
        st.stop()


    
# st.write(ingredients_list)
st.text(ingredients_list)

        

   
    
    
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
