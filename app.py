import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder,GridUpdateMode
import io as io_module
from ramis_cleaning import ramis_cleaning_fun
from macl_cleaning import macl_cleaning_fun
from comparison import comparison_fun



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

    AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.NO_UPDATE,  # ✅ Key change
        height=400,
        width='100%',
        allow_unsafe_jscode=True
    )

# === Cleaning Functions (Customize as per your logic) ===
def clean_ramis(df):
    Feedback_ramis_1,Feedback_ramis_2,expanded_ramis=ramis_cleaning_fun(df, curr_date, Start_Period_date,End_Period_date )
    return Feedback_ramis_1,Feedback_ramis_2,expanded_ramis

def clean_macl(df):
    Feedback_macl_1,Feedback_macl_2,macl_expanded=macl_cleaning_fun(df, curr_date, Start_Period_date,End_Period_date )
    return Feedback_macl_1,Feedback_macl_2,macl_expanded

def changes(df1,df2):
    clubbed_added,clubbed_modified,clubbed_deleted=comparison_fun(df1,df2, curr_date, Start_Period_date,End_Period_date)
    return clubbed_added,clubbed_modified,clubbed_deleted





# === Main Views ===
if selected == "Ramis Cleaning":
    st.title("🧹 RAMIS Data Cleaner")
    uploaded_file = st.file_uploader("Upload RAMIS Excel File", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file,sheet_name="Connecting Flight Plans")
        if st.button("Clean RAMIS Data"):
            with st.spinner("Cleaning RAMIS data..."):
                Feedback_ramis_1,Feedback_ramis_2,expanded_ramis=clean_ramis(df)
                
                with st.expander("📝 Feedback 1", expanded=True):
                    show_aggrid(Feedback_ramis_1)
                
                with st.expander("📝 Feedback 2", expanded=True):
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
elif selected == "MACL Cleaning":
    st.title("🧹 MACL Data Cleaner")
    uploaded_file = st.file_uploader("Upload MACL Excel File", type=["xlsx"])
    if uploaded_file:
        df = pd.read_excel(uploaded_file,sheet_name="Data")
        if st.button("Clean MACL Data"):
            with st.spinner("Cleaning RAMIS data..."):
                Feedback_macl_1,Feedback_macl_2,macl_expanded=clean_macl(df)
                
                with st.expander("📝 Feedback 1", expanded=True):
                    show_aggrid(Feedback_macl_1)
                
                with st.expander("📝 Feedback 2", expanded=True):
                    show_aggrid(Feedback_macl_2)
                
                
                output = io_module.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    Feedback_macl_1.to_excel(writer, sheet_name='Feedback 1', index=False)
                    Feedback_macl_2.to_excel(writer, sheet_name='Feedback 2', index=False)
                output.seek(0)

                st.download_button(
                    label="📥 Download Feedback Excel",
                    data=output,
                    file_name="ramis_feedback.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

elif selected == "International Flight Changes":
    st.title("🧹 International Flight Changes")
    uploaded_file_1 = st.file_uploader("Upload Ramis Excel File", type=["xlsx"])
    uploaded_file_2 = st.file_uploader("Upload MACL File", type=["xlsx"])
    if uploaded_file_1 and uploaded_file_2:
        df_ramis = pd.read_excel(uploaded_file_1,sheet_name="Connecting Flight Plans")
        df_macl = pd.read_excel(uploaded_file_2,sheet_name="Data")
        if st.button("Find Changes"):
            with st.spinner("Looking for Changes ..."):
                clubbed_added,clubbed_modified,clubbed_deleted=changes(df_ramis,df_macl)
                
                with st.expander("📝 New Added Flights", expanded=True):
                    show_aggrid(clubbed_added)
                
                with st.expander("📝 Deleted Flights", expanded=True):
                    show_aggrid(clubbed_deleted)

                with st.expander("📝 Modified Flights", expanded=True):
                    show_aggrid(clubbed_modified)
                
                
                output = io_module.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    clubbed_added.to_excel(writer, sheet_name='New Flights', index=False)
                    clubbed_deleted.to_excel(writer, sheet_name='Deleted Flights', index=False)
                    clubbed_modified.to_excel(writer, sheet_name='Modified Flights', index=False)
                output.seek(0)

                st.download_button(
                    label="📥 Download Change sheet",
                    data=output,
                    file_name="Changes.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )