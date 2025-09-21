# Import python packages

import streamlit as st
import pandas as pd
from snowflake.snowpark.functions import col   # keep only if you'll sort with Snowpark
import requests                                 # only needed if you call external APIs later
from urllib.parse import quote

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_fruityvice(search_key: str) -> pd.DataFrame:
    url = f"https://my.smoothiefroot.com/api/fruit/{quote(str(search_key).strip().lower())}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return pd.json_normalize(r.json())



# ----- UI header -----
st.set_page_config(page_title="Customize Your Smoothies", page_icon="🥤")
st.title("Customize Your Smoothies")
st.caption("Choose the fruits you want in your smoothie.")

# ----- Single, consistent textbox (normalized) -----
def _normalize_name():
    s = st.session_state.get("name_on_order", "")
    st.session_state["name_on_order"] = " ".join(s.strip().split())

name_on_order = st.text_input(
    "Name on smoothie",
    key="name_on_order",
    placeholder="e.g., Mia S.",
    on_change=_normalize_name,   # normalize on blur/Enter
)
st.write("The name on the smoothie will be", name_on_order if name_on_order else "—")

# ----- Connection + Session (cached) -----
@st.cache_resource(show_spinner="Connecting to Snowflake…")
def get_session():
    conn = st.connection("snowflake", type="snowflake")
    return conn.session()  # requires snowflake-snowpark-python

session = get_session()

# ----- Load fruit options (Snowpark -> pandas) -----
sp_df = (
    session.table("SMOOTHIES.PUBLIC.FRUIT_OPTIONS")
           .select("FRUIT_ID", "FRUIT_NAME", "SEARCH_ON")
           # .sort(col("FRUIT_NAME").asc())   # optional, if you want Snowflake-side sort
           .limit(1000)
)
pd_df = sp_df.to_pandas()
pd_df["FRUIT_ID"] = pd.to_numeric(pd_df["FRUIT_ID"], errors="coerce").astype("Int64")

# ----- Multiselect: options are IDs; UI shows names -----
id_to_name = dict(zip(pd_df["FRUIT_ID"], pd_df["FRUIT_NAME"]))

ingredients_list = st.multiselect(
    "Choose up to 5 ingredients:",
    options=pd_df["FRUIT_ID"].tolist(),        # no .dropna(); you said table has no nulls
    format_func=lambda fid: id_to_name.get(fid, f"ID {fid}"),
    max_selections=5,
)


ingredients_string = ""  # ensure defined even if nothing selected

if ingredients_list:
    picked_names = []
    for fruit_id in ingredients_list:
        rows = pd_df.loc[pd_df["FRUIT_ID"].eq(fruit_id), ["FRUIT_NAME"]]
        if rows.empty:
            continue
        picked_names.append(str(rows.iloc[0]["FRUIT_NAME"]).strip())

    ingredients_string = " ".join(picked_names) + " "  # ← trailing space on purpose


# Build space-separated names WITH a trailing space (important for HASH match)
ingredients_string = ""
if ingredients_list:
    picked_names = []
    for fruit_id in ingredients_list:
        rows = pd_df.loc[pd_df["FRUIT_ID"].eq(fruit_id), ["FRUIT_NAME"]]
        if rows.empty:
            continue
        picked_names.append(str(rows.iloc[0]["FRUIT_NAME"]).strip())

    ingredients_string = " ".join(picked_names) + " "  # ← trailing space on purpose
    st.markdown("**Ingredients:** " + ingredients_string)

# ----- Safe insert (no SQL string concat) -----
submit = st.button("Submit Order")

if submit:
    if not ingredients_string.strip() or not name_on_order:
        st.error("Please enter a name and pick at least one ingredient.")
    else:
        ing_esc  = ingredients_string.replace("'", "''")
        name_esc = name_on_order.replace("'", "''")

        # Default to unfilled; we’ll update specific names next
        session.sql(f"""
            INSERT INTO SMOOTHIES.PUBLIC.ORDERS
              (INGREDIENTS, NAME_ON_ORDER, ORDER_TS, ORDER_FILLED)
            VALUES
              ('{ing_esc}', '{name_esc}', CURRENT_TIMESTAMP(), FALSE)
        """).collect()
        st.success("Order saved.", icon="✅")
