import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder,GridUpdateMode,JsCode
import io as io_module
from ramis_cleaning import ramis_cleaning_fun
from macl_cleaning import macl_cleaning_fun
from comparison import comparison_fun
from datetime import date





st.set_page_config(page_title="International Flight Changes", layout="wide")


curr_date = pd.to_datetime("2025-06-04")
Start_Period_date = pd.to_datetime("2025-05-30")
End_Period_date = pd.to_datetime("2025-10-25")

# # Sidebar Navigation
# selected = option_menu(
#     menu_title="Main Menu",
#     options=["Ramis Cleaning", "MACL Cleaning", "International Flight Changes"],
#     icons=["funnel-fill", "file-earmark-excel", "bar-chart"],
#     menu_icon="gear", default_index=0
# )




# Sidebar Navigation (Vertical Left)
with st.sidebar:
    selected = option_menu(
        menu_title="Modules",  # Sidebar title
        options=[
            "Ramis data Validator", 
            "MACL data Validator", 
            "Schedule Change Tracker"
        ],
        icons=["file-earmark-excel", "file-earmark-excel", "bar-chart"],
        menu_icon="gear",  # Top icon
        default_index=0,
        orientation="vertical"  # Ensures vertical left-side layout
    )



def show_aggrid(df):
    gb = GridOptionsBuilder.from_dataframe(df)
    
    for col in df.columns:
        gb.configure_column(col, autoWidth=True)
    gb.configure_default_column(filter=True,sortable=True,groupable=True, value=True, enableRowGroup=True, aggFunc='sum')
    if len(df) > 10:
        gb.configure_pagination(enabled=True, paginationPageSize=10)
    else:
        gb.configure_pagination(enabled=False)
    # gb.configure_pagination(enabled=True, paginationPageSize=10)
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_side_bar(filters_panel=True)
    gb.configure_grid_options(rowGroupPanelShow='always')

    grid_options = gb.build()
    grid_height = min(400, 40 + len(df) * 35)
    AgGrid(
        df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.NO_UPDATE,
        height=grid_height,
        width='100%',
        allow_unsafe_jscode=True,
        fit_columns_on_grid_load=True
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
if selected == "Ramis data Validator":
    st.title("🧹 RAMIS Data Cleaner")
    uploaded_file = st.file_uploader("Upload RAMIS Excel File", type=["xlsx"])

    col1, col2 = st.columns(2)
    with col1:
        curr_date = st.date_input("Select current date", format="YYYY-MM-DD")

    with col2:
        Start_Period_date, End_Period_date = st.date_input(
        "Select MACL date range",
        value=(date(2025, 5, 30), date(2025, 10, 25)),
        format="YYYY-MM-DD"
        )

    curr_date=pd.Timestamp(curr_date)
    Start_Period_date=pd.Timestamp(Start_Period_date)
    End_Period_date=pd.Timestamp(End_Period_date)



    if uploaded_file and curr_date:
        df = pd.read_excel(uploaded_file,sheet_name="Connecting Flight Plans")
        if st.button("Execute Cleanup"):
            with st.spinner("Checking RAMIS data..."):
                Feedback_ramis_1,Feedback_ramis_2,expanded_ramis=clean_ramis(df)

                st.markdown("The table below highlights data points with missing values, " \
                "incorrect formatting, or discrepancies in flight counts between the " \
                "specified dates and the values recorded in the table")
                
                with st.expander("📝 Validation Issues Summary", expanded=True):
                    show_aggrid(Feedback_ramis_1)

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown(
                "The table below lists Flight IDs that appear more than once on a given date. "
                "Corresponding comments are provided in the **Comment** column.<br>"
                "**Note:** This feedback is generated after removing data flagged in the previous validation step. "
                "Please Ensure to revalidate once the above identified issues are addressed, as additional flights might " \
                "still breach this logic.",
                unsafe_allow_html=True
                )

                with st.expander("📝 Flight Duplication Log", expanded=True):
                    show_aggrid(Feedback_ramis_2)
                
                
                output = io_module.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    Feedback_ramis_1.to_excel(writer, sheet_name='Feedback 1', index=False)
                    Feedback_ramis_2.to_excel(writer, sheet_name='Feedback 2', index=False)
                output.seek(0)

                st.download_button(
                    label="📥 Download Feedback Sheet",
                    data=output,
                    file_name="ramis_feedback.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
elif selected == "MACL data Validator":
    st.title("🧹 MACL Data Cleaner")
    uploaded_file = st.file_uploader("Upload MACL Excel File", type=["xlsx"])


    col1, col2 = st.columns(2)
    with col1:
        curr_date = st.date_input("Select current date", format="YYYY-MM-DD")

    with col2:
        Start_Period_date, End_Period_date = st.date_input(
        "Select MACL date range",
        value=(date(2025, 5, 30), date(2025, 10, 25)),
        format="YYYY-MM-DD"
        )

    curr_date=pd.Timestamp(curr_date)
    Start_Period_date=pd.Timestamp(Start_Period_date)
    End_Period_date=pd.Timestamp(End_Period_date)


    if uploaded_file and curr_date and Start_Period_date and  End_Period_date:
        df = pd.read_excel(uploaded_file,sheet_name="Data")
        if st.button("Execute Cleanup"):
            with st.spinner("Checking MACL data..."):
                Feedback_macl_1,Feedback_macl_2,macl_expanded=clean_macl(df)

                st.markdown("The table below highlights data points with errors"
                " in date and time values, formatting issues, or data discrepancies.")
                
                with st.expander("📝 Date - Time Error Summary", expanded=True):
                    show_aggrid(Feedback_macl_1)

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown(
                "The table below lists Flight IDs that appear more than once on a given date. "
                "Corresponding comments are provided in the **Comment** column.<br>"
                "**Note:** This feedback is generated after removing data flagged in the previous validation step. "
                "Please Ensure to revalidate once the above identified issues are addressed, as additional flights might " \
                "still breach this logic.",
                unsafe_allow_html=True
                )
                
                with st.expander("📝 Flight Duplication Log", expanded=True):
                    show_aggrid(Feedback_macl_2)

                
                
                
                output = io_module.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    Feedback_macl_1.to_excel(writer, sheet_name='Feedback 1', index=False)
                    Feedback_macl_2.to_excel(writer, sheet_name='Feedback 2', index=False)
                output.seek(0)

                st.download_button(
                    label="📥 Download Feedback Sheet",
                    data=output,
                    file_name="macl_feedback.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

elif selected == "Schedule Change Tracker":
    st.title("🧹 International Flight Changes")
    uploaded_file_1 = st.file_uploader("Upload Ramis Excel File", type=["xlsx"])
    uploaded_file_2 = st.file_uploader("Upload MACL File", type=["xlsx"])

    col1, col2 = st.columns(2)
    with col1:
        curr_date = st.date_input("Select current date", format="YYYY-MM-DD")

    with col2:
        Start_Period_date, End_Period_date = st.date_input(
        "Select MACL date range",
        value=(date(2025, 5, 30), date(2025, 10, 25)),
        format="YYYY-MM-DD"
        )

    curr_date=pd.Timestamp(curr_date)
    Start_Period_date=pd.Timestamp(Start_Period_date)
    End_Period_date=pd.Timestamp(End_Period_date)

    if uploaded_file_1 and uploaded_file_2 and curr_date and Start_Period_date and  End_Period_date:
        df_ramis = pd.read_excel(uploaded_file_1,sheet_name="Connecting Flight Plans")
        df_macl = pd.read_excel(uploaded_file_2,sheet_name="Data")
        if st.button("Find Changes"):
            with st.spinner("Looking for Changes ..."):
                clubbed_added,clubbed_modified,clubbed_deleted=changes(df_ramis,df_macl)


                st.markdown(
                "The table below displays flights that have been newly introduced in the MACL schedule.",
                unsafe_allow_html=True
                )
                
                with st.expander("📝 New Added Flights", expanded=True):
                    show_aggrid(clubbed_added)

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown(
                "The table below displays flights from the RAMIS schedule that are no " \
                "longer present in the updated MACL data.",
                unsafe_allow_html=True
                )
                
                with st.expander("📝 Deleted Flights", expanded=True):
                    show_aggrid(clubbed_deleted)

                st.markdown("<br>", unsafe_allow_html=True)

                st.markdown(
                "The table below highlights flights with changes in timing or " \
                "other details between the RAMIS and MACL schedules",
                unsafe_allow_html=True
                )

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