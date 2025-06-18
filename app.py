import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import io

st.set_page_config(page_title="Data Cleaner", layout="wide")

# Sidebar Navigation
selected = option_menu(
    menu_title="Main Menu",
    options=["Ramis Cleaning", "MACL Cleaning", "International Flight Changes"],
    icons=["funnel-fill", "file-earmark-excel", "bar-chart"],
    menu_icon="gear", default_index=0
)

# === Cleaning Functions (Customize as per your logic) ===
def clean_ramis(df):
    # Example RAMIS cleaning logic
    df = df.dropna()
    return df

def clean_macl(df):
    # Example MACL cleaning logic
    df = df.drop_duplicates()
    return df

def generate_results(ramis_df, macl_df):
    return pd.DataFrame({"Status": ["Success"], "Ramis Rows": [len(ramis_df)], "MACL Rows": [len(macl_df)]})


# === Helper: Display AgGrid with features ===
def show_aggrid(df):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum')
    gb.configure_pagination(enabled=True, paginationPageSize=10)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_side_bar(filters_panel=True)
    grid_options = gb.build()

    AgGrid(df, gridOptions=grid_options, height=400, width='100%', allow_unsafe_jscode=True)


# === Main Views ===
if selected == "Ramis Cleaning":
    st.title("🧹 RAMIS Data Cleaner")
    uploaded_file = st.file_uploader("Upload RAMIS Excel File", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file)
        show_aggrid(df)

        if st.button("Clean RAMIS Data"):
            with st.spinner("Cleaning RAMIS data..."):
                cleaned_df = clean_ramis(df)
                show_aggrid(cleaned_df)
                st.download_button("Download Cleaned File", data=cleaned_df.to_excel(index=False), file_name="cleaned_ramis.xlsx")

# elif selected == "MACL Cleaning":
#     st.title("🧹 MACL Data Cleaner")
#     uploaded_file = st.file_uploader("Upload MACL Excel File", type=["xlsx"])
#     if uploaded_file:
#         df = pd.read_excel(uploaded_file)
#         st.dataframe(df.head())
#         if st.button("Clean & Download"):
#             with st.spinner("Cleaning MACL data..."):
#                 cleaned_df = clean_macl(df)
#                 output = io.BytesIO()
#                 cleaned_df.to_excel(output, index=False, engine='openpyxl')
#                 st.download_button("Download Cleaned File", data=output.getvalue(), file_name="cleaned_macl.xlsx")

# elif selected == "International Flight Changes":
#     st.title("📊 Generate Results")
#     ramis_file = st.file_uploader("Upload Cleaned RAMIS File", type=["xlsx"], key="ramis")
#     macl_file = st.file_uploader("Upload Cleaned MACL File", type=["xlsx"], key="macl")

#     if ramis_file and macl_file:
#         ramis_df = pd.read_excel(ramis_file)
#         macl_df = pd.read_excel(macl_file)
#         if st.button("Generate Result"):
#             with st.spinner("Generating results..."):
#                 result_df = generate_results(ramis_df, macl_df)
#                 st.dataframe(result_df)
#                 output = io.BytesIO()
#                 result_df.to_excel(output, index=False, engine='openpyxl')
#                 st.download_button("Download Result", data=output.getvalue(), file_name="result.xlsx")
