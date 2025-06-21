import pandas as pd
import numpy as np

from macl_functions import extract_start_end,transform_flt_code,classify_direction,replace_flt_no,split_list,convert_to_time,expanded_macl
from ramis_functions import group_date_ranges


def macl_cleaning_fun(macl_data, curr_date, Start_Period_date,End_Period_date):

    # Step-1 : Convert the Effective Date to Start and End Date and see if any issues
    macl_data[['Start Date', 'End Date']] = macl_data['EFFECTIVE'].apply(extract_start_end)
    macl_data['Start Date'] = pd.to_datetime(macl_data['Start Date'], dayfirst=True, errors='coerce')
    macl_data['End Date'] = pd.to_datetime(macl_data['End Date'], dayfirst=True, errors='coerce')
    macl_data["Date error"]=macl_data["Start Date"].isna() | macl_data["End Date"].isna()


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
    Feedback_macl_1=macl_data[(macl_data["Date error"]==True) | (macl_data["Time error"]==True)]
    Feedback_macl_1.drop(['First_Flt', 'Second_Flt','First_Direction', 'Second_Direction','Direction','Start Date', 'End Date'],axis=1,inplace=True)


    # Step-6 : Seprate Arrivals and Departure and vstack them   

    arrivals_1 = macl_data[macl_data['First_Direction'] == 'Arrival'][[
    'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
    'Category',  'Start Date', 'End Date', 'First_Flt', 'STA'
    ]].copy()
    arrivals_1.columns = [
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
        'Category',  'Start Date', 'End Date', 'Flight Code', 'Time'
    ]
    arrivals_1['Type'] = 'Arrival'

    arrivals_2 = macl_data[macl_data['Second_Direction'] == 'Arrival'][[
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
        'Category',  'Start Date', 'End Date', 'Second_Flt', 'STA'
    ]].copy()
    arrivals_2.columns = [
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
        'Category',  'Start Date', 'End Date', 'Flight Code', 'Time'
    ]
    arrivals_2['Type'] = 'Arrival'

    arrival_df = pd.concat([arrivals_1, arrivals_2], ignore_index=True)

    # DEPARTURES
    departures_1 = macl_data[macl_data['First_Direction'] == 'Departure'][[
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
        'Category',  'Start Date', 'End Date', 'First_Flt', 'STD'
    ]].copy()
    departures_1.columns = [
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
        'Category',  'Start Date', 'End Date', 'Flight Code', 'Time'
    ]
    departures_1['Type'] = 'Departure'

    departures_2 = macl_data[macl_data['Second_Direction'] == 'Departure'][[
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
        'Category',  'Start Date', 'End Date', 'Second_Flt', 'STD'
    ]].copy()
    departures_2.columns = [
        'AIRLINE', 'DAYS OF OPS', 'A/C TYPE', 'ROUTE', 'SEATS',
        'Category',  'Start Date', 'End Date', 'Flight Code', 'Time'
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


    # Step-9 : Split rows on Date level
    Feedback_macl_2=macl_expanded[["Flight Code","Time","Date"]]
    Feedback_macl_2 = Feedback_macl_2.groupby(["Flight Code", "Date"])[["Time"]].agg(list).reset_index()
    Feedback_macl_2["Count1"]=Feedback_macl_2["Time"].apply(len)
    Feedback_macl_2=Feedback_macl_2[Feedback_macl_2["Count1"]>1]
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
    Feedback_macl_2
    
    return Feedback_macl_1,Feedback_macl_2,macl_expanded
