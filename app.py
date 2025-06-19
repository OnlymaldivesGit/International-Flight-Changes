import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import io as io_module
from ramis_cleaning import ramis_cleaning_fun

st.set_page_config(page_title="Data Cleaner", layout="wide")


curr_date = pd.to_datetime("2025-06-04")

Start_Period_date = pd.to_datetime("2025-05-30")
End_Period_date = pd.to_datetime("2025-10-25")

# Sidebar Navigation
selected = option_menu(
    menu_title="Main Menu",
    options=["Ramis Cleaning", "MACL Cleaning", "International Flight Changes"],
    icons=["funnel-fill", "file-earmark-excel", "bar-chart"],
    menu_icon="gear", default_index=0
)

def show_aggrid(df):
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum')
    gb.configure_pagination(enabled=True, paginationPageSize=10)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_side_bar(filters_panel=True)
    grid_options = gb.build()

    AgGrid(df, gridOptions=grid_options, height=400, width='100%', allow_unsafe_jscode=True)

# === Cleaning Functions (Customize as per your logic) ===
def clean_ramis(df):
    Feedback_ramis_1,Feedback_ramis_2=ramis_cleaning_fun(df, curr_date, Start_Period_date,End_Period_date )
    return Feedback_ramis_1,Feedback_ramis_2



# === Main Views ===
if selected == "Ramis Cleaning":
    st.title("🧹 RAMIS Data Cleaner")
    uploaded_file = st.file_uploader("Upload RAMIS Excel File", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file,sheet_name="Connecting Flight Plans")
        if st.button("Clean RAMIS Data"):
            with st.spinner("Cleaning RAMIS data..."):
                Feedback_ramis_1,Feedback_ramis_2=clean_ramis(df)
                st.subheader("📝 Feedback 1")
                show_aggrid(Feedback_ramis_1)

                st.subheader("📝 Feedback 2")
                show_aggrid(Feedback_ramis_2)
                
                output = io_module.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    Feedback_ramis_1.to_excel(writer, sheet_name='Feedback 1', index=False)
                    Feedback_ramis_2.to_excel(writer, sheet_name='Feedback 2', index=False)
                output.seek(0)

                st.download_button(
                    label="📥 Download Feedback Excel",
                    data=output,
                    file_name="ramis_feedback.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )