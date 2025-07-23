import pandas as pd
import numpy as np
import uuid


from macl_functions import extract_start_end,transform_flt_code,classify_direction,replace_flt_no,split_list,convert_to_time,expanded_macl
from ramis_functions import group_date_ranges


def macl_cleaning_fun(macl_data, curr_date, Start_Period_date,End_Period_date):

    macl_data['ID'] = [uuid.uuid4().hex for _ in range(len(macl_data))]
    initial_copy=macl_data.copy()

    # Step-1 : Convert the Effective Date to Start and End Date and see if any issues
    macl_data[['Start Date', 'End Date']] = macl_data['EFFECTIVE'].apply(extract_start_end)
    macl_data['Start Date'] = pd.to_datetime(macl_data['Start Date'], format='%d.%m.%y', dayfirst=True, errors='coerce')
    macl_data['End Date'] = pd.to_datetime(macl_data['End Date'], format='%d.%m.%y', dayfirst=True, errors='coerce')
    macl_data["Date error"] = (macl_data["Start Date"].isna() | macl_data["End Date"].isna() |(macl_data["End Date"] < macl_data["Start Date"]))

    # Step-2 : Convert the Text Time to STA and STD and see if any issues
    macl_data['STA'] = macl_data['STA'].astype(str).str.strip()
    macl_data['STD'] = macl_data['STD'].astype(str).str.strip()
    macl_data['STA'] = macl_data['STA'].apply(convert_to_time)
    macl_data['STD'] = macl_data['STD'].apply(convert_to_time)

    macl_data["Time error"]=macl_data["STA"].isna() | macl_data["STD"].isna()


    # Step-3 : Find Direction based on Route
    macl_data["Direction"] = macl_data["ROUTE"].apply(classify_direction)



    # Step-4 : Transform Flight Code to Arrival and Departure and Put "D" for Departure Code for Flights having same code for Arrival and Departure   
    macl_data['FLT NO'] = macl_data['FLT NO'].apply(transform_flt_code)
    macl_data['FLT NO'] = macl_data.apply(replace_flt_no, axis=1)


    # Step-5 : Split Direction and FLT Code to Different Columns   
    macl_data['Direction'] = macl_data['Direction'].str.split(r'\s*-\s*')
    macl_data[['First_Direction', 'Second_Direction']] = macl_data['Direction'].apply(split_list)

    macl_data['FLT NO'] = macl_data['FLT NO'].str.split(r'\s*-\s*')
    macl_data[['First_Flt', 'Second_Flt']] = macl_data['FLT NO'].apply(split_list)

    # First Feedback: Tells about error in Date or Time format
    Feedback_macl_1 = macl_data.copy()
    Feedback_macl_1["Issues"] = (Feedback_macl_1["Date error"] | Feedback_macl_1["Time error"] )
    Feedback_macl_1.drop(['First_Flt', 'Second_Flt','First_Direction', 'Second_Direction','Direction','Start Date', 'End Date'],axis=1,inplace=True)
    Feedback_macl_1=initial_copy.merge(Feedback_macl_1, on='ID', how='left', suffixes=('', '_y'))
    l=list(initial_copy.columns)+["Date error","Time error","Issues"]
    Feedback_macl_1=Feedback_macl_1[l]
    Feedback_macl_1.drop(["ID"],axis=1,inplace=True)

    # Step-6 : Seprate Arrivals and Departure and vstack them   

    arrivals_1 = macl_data[macl_data['First_Direction'] == 'Arrival'][[
    'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
      'Start Date', 'End Date', 'First_Flt', 'STA',"status"
    ]].copy()
    arrivals_1.columns = [
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
          'Start Date', 'End Date', 'Flight Code', 'Time',"status"
    ]
    arrivals_1['Type'] = 'Arrival'

    arrivals_2 = macl_data[macl_data['Second_Direction'] == 'Arrival'][[
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
         'Start Date', 'End Date', 'Second_Flt', 'STA',"status"
    ]].copy()
    arrivals_2.columns = [
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
          'Start Date', 'End Date', 'Flight Code', 'Time',"status"
    ]
    arrivals_2['Type'] = 'Arrival'

    arrival_df = pd.concat([arrivals_1, arrivals_2], ignore_index=True)

    # DEPARTURES
    departures_1 = macl_data[macl_data['First_Direction'] == 'Departure'][[
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
          'Start Date', 'End Date', 'First_Flt', 'STD',"status"
    ]].copy()
    departures_1.columns = [
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
         'Start Date', 'End Date', 'Flight Code', 'Time',"status"
    ]
    departures_1['Type'] = 'Departure'

    departures_2 = macl_data[macl_data['Second_Direction'] == 'Departure'][[
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
          'Start Date', 'End Date', 'Second_Flt', 'STD',"status"
    ]].copy()
    departures_2.columns = [
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
          'Start Date', 'End Date', 'Flight Code', 'Time',"status"
    ]
    departures_2['Type'] = 'Departure'

    departure_df = pd.concat([departures_1, departures_2], ignore_index=True)

    # Combine all

    macl_data = pd.concat([arrival_df, departure_df], ignore_index=True)


    # Step-6 : Find rows which operation has been over completely and filter out them   

    macl_data["Ops status"]=macl_data["End Date"].apply(lambda x: "OPS COMPLETED" if x<=curr_date else "-" )
    macl_data=macl_data[macl_data["Ops status"]!="OPS COMPLETED"]


    # Step-7 : Split rows for Weekday level

    macl_data['DAYS_SPLIT'] = macl_data['DAYS OF OPS'].astype(str).apply(lambda x: [d for d in x if d != '0'])
    macl_data = macl_data.explode('DAYS_SPLIT')
    macl_data['DAYS OF OPS'] = macl_data['DAYS_SPLIT']
    macl_data = macl_data.drop(columns=['DAYS_SPLIT'])
    macl_data = macl_data.reset_index(drop=True)


    # Step-8 : Split rows on Date level
    macl_expanded=expanded_macl(macl_data)

    cols_to_check = [col for col in macl_expanded.columns if col != 'status']
    duplicated_rows = macl_expanded[macl_expanded.duplicated(subset=cols_to_check, keep=False)]
    df_1 = duplicated_rows[duplicated_rows["status"] == "Cancelled"]
    duplicated_rows = duplicated_rows[duplicated_rows["status"] != "Cancelled"]

    duplicated_rows["Has_Duplicate"] = duplicated_rows[cols_to_check].apply(
        lambda row: df_1[cols_to_check].apply(lambda x: x.equals(row), axis=1).any(), axis=1
    )

    Feedback_macl_3=duplicated_rows[duplicated_rows["Has_Duplicate"]==True]
    Feedback_macl_3["Weekday"] = Feedback_macl_3["Date"].apply(lambda x: x.strftime('%A'))
    Feedback_macl_3=Feedback_macl_3[["Flight Code","ROUTE","Time","Weekday","Type"]].drop_duplicates()

    macl_expanded=macl_expanded[macl_expanded["status"]!="Cancelled"]
    macl_expanded.drop(["status"],axis=1,inplace=True)

    # Step-9 : Split rows on Date level
    Feedback_macl_2=macl_expanded[["Flight Code","Time","Date"]]
    Feedback_macl_2 = Feedback_macl_2.groupby(["Flight Code", "Date"])[["Time"]].agg(list).reset_index()
    Feedback_macl_2["Count1"]=Feedback_macl_2["Time"].apply(len)
    Feedback_macl_2=Feedback_macl_2[Feedback_macl_2["Count1"]>1]
    if not Feedback_macl_2.empty:
        Feedback_macl_2["unique"]=Feedback_macl_2["Time"].apply(lambda x: list(np.unique(x)))
        Feedback_macl_2["Count2"]=Feedback_macl_2["unique"].apply(len)
        Feedback_macl_2["Feedback"] = Feedback_macl_2.apply(
            lambda row: "Same Flight Multiple time" if row["Count1"] == row["Count2"] else "Duplicate Entries",
            axis=1
        )
        Feedback_macl_2["Weekday"] = Feedback_macl_2["Date"].apply(lambda x: x.strftime('%A'))

        Feedback_macl_2=Feedback_macl_2[["Flight Code", "Feedback","Date","Weekday"]]

        Feedback_macl_2 = Feedback_macl_2.groupby(["Flight Code","Weekday", "Feedback"]).agg(list).reset_index()
        Feedback_macl_2["Flight_Date"] = Feedback_macl_2["Date"].apply(group_date_ranges)
        Feedback_macl_2.drop(columns=["Date"], inplace=True)
        Feedback_macl_2=Feedback_macl_2.explode("Flight_Date").reset_index(drop=True)
        Feedback_macl_2[['Start Date', 'End Date']] = Feedback_macl_2['Flight_Date'] \
            .str.split(' - ', expand=True).apply(lambda x: x.str.strip())
        Feedback_macl_2.drop(["Flight_Date"], axis=1, inplace=True)
    else:
        Feedback_macl_2 = pd.DataFrame(columns=["Flight ID", "Comment", "Weekday", "Start Date", "End Date"])
    
    return Feedback_macl_1,Feedback_macl_2,Feedback_macl_3,macl_expanded


