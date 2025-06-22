import pandas as pd
import numpy as np

from ramis_functions import count_weekdays, group_date_ranges

invalid_values = ['ARRTBA', 'DEPTBA', 'DMLED', 'MLE', 'MLED', 'RESARR', 'RESDEP','DMLE']


def ramis_cleaning_fun(ramis_int, curr_date, Start_Period_date,End_Period_date):


    # Possible error Resolutions

    required_columns = ['Flight ID', 'Start Date', 'End Date', 'Scheduled Day',
                    'Scheduled Time', 'Connecting Flight Entries', 'Type']
    missing_cols = [col for col in required_columns if col not in ramis_int.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in input data: {missing_cols}")


    ramis_int=ramis_int.drop(['Connecting Flight Created','Check-In Lead Time','Pseudo Flight','AirLine ID',"AirLine Name","Check-In Time"], axis=1)
    ramis_int = ramis_int[~ramis_int["Flight ID"].isin(invalid_values)]
    

    ramis_int["Start Date"] = pd.to_datetime(ramis_int['Start Date'], format='%d-%m-%Y', errors='coerce')
    ramis_int['End Date'] = pd.to_datetime(ramis_int['End Date'], format='%d-%m-%Y', errors='coerce')

# Flag rows where conversion failed
    ramis_int['Missing Value'] = ramis_int.apply(lambda row: any(pd.isna(x) or x == '' or x == ' ' for x in row), axis=1)
    ramis_int['Invalid Date'] = (ramis_int['Start Date'].isna()) | (ramis_int['End Date'].isna())
    ramis_int['Weekday Count'] = ramis_int.apply(lambda row: count_weekdays(row['Start Date'], row['End Date'], row['Scheduled Day']), axis=1)
    
    
    ramis_int["Ops status"]=ramis_int["End Date"].apply(lambda x: "OPS COMPLETED" if x<=curr_date else "-" )
    ramis_int["Unmatched Flight Counts"]= (ramis_int['Connecting Flight Entries']) != (ramis_int['Weekday Count'])


    temp_ramis_int=ramis_int[(ramis_int["Missing Value"]==False) & (ramis_int["Invalid Date"]==False)]
    Feedback_ramis_1=ramis_int[(ramis_int["Missing Value"]==True) | (ramis_int["Invalid Date"]==True) |  (ramis_int["Unmatched Flight Counts"]==True)]
    Feedback_ramis_1=Feedback_ramis_1[["Flight ID","Type","Start Date","End Date","Scheduled Day","Missing Value","Invalid Date","Unmatched Flight Counts"]]
    Feedback_ramis_1['Start Date'] = Feedback_ramis_1['Start Date'].dt.date.astype(str)
    Feedback_ramis_1['End Date'] = Feedback_ramis_1['End Date'].dt.date.astype(str)

    expanded_data = []
    

    for idx, row in temp_ramis_int.iterrows():
        day_abbr = row['Scheduled Day'][:3].upper()  # 'Sunday' -> 'SUN'
        matching_dates = pd.date_range(start=row['Start Date'], end=row['End Date'], freq=f'W-{day_abbr}')

        if len(matching_dates) == 0:
            continue

        # Repeat metadata for each matching date
        repeated_data = {
            'Flight ID': [row['Flight ID']] * len(matching_dates),
            'Type': [row['Type']] * len(matching_dates),
            'Flight Date': matching_dates.date,
            'Scheduled Time': [row['Scheduled Time']] * len(matching_dates),
            'Connecting Flight Entries': [row['Connecting Flight Entries']] * len(matching_dates),
            'Weekday Count': [row['Weekday Count']] * len(matching_dates)
        }

        expanded_data.append(pd.DataFrame(repeated_data))

    # Step 2: Combine all expanded rows
    expanded_ramis = pd.concat(expanded_data, ignore_index=True)
    expanded_ramis["Flight Date"] = pd.to_datetime(expanded_ramis["Flight Date"])
    expanded_ramis['Scheduled Time'] = pd.to_datetime(expanded_ramis['Scheduled Time'], format='%H:%M:%S').dt.time


    Feedback_ramis_2 = expanded_ramis.groupby(["Flight ID", "Flight Date"])[["Scheduled Time"]].agg(list).reset_index()
    Feedback_ramis_2["Total count"]=Feedback_ramis_2["Scheduled Time"].apply(len)
    Feedback_ramis_2 = Feedback_ramis_2[Feedback_ramis_2["Total count"] > 1]
    if not Feedback_ramis_2.empty:
        Feedback_ramis_2["unique"] = Feedback_ramis_2["Scheduled Time"].apply(lambda x: list(np.unique(x)))
        Feedback_ramis_2["Unique count"] = Feedback_ramis_2["unique"].apply(len)
        Feedback_ramis_2["Comment"] = Feedback_ramis_2.apply(
            lambda row: "This Flight is being Scheduled for Multiple different timings in a single day"
            if row["Total count"] == row["Unique count"]
            else "This Flight is being Scheduled for Multiple same timings in a single day",
            axis=1
        )

        Feedback_ramis_2["Weekday"] = Feedback_ramis_2["Flight Date"].apply(lambda x: x.strftime('%A'))
        Feedback_ramis_2 = Feedback_ramis_2[["Flight ID", "Comment", "Flight Date", "Weekday"]]
        Feedback_ramis_2 = Feedback_ramis_2.groupby(["Flight ID", "Weekday", "Comment"]).agg(list).reset_index()
        Feedback_ramis_2["Flight_Date"] = Feedback_ramis_2["Flight Date"].apply(group_date_ranges)
        Feedback_ramis_2.drop(columns=["Flight Date"], inplace=True)
        Feedback_ramis_2 = Feedback_ramis_2.explode("Flight_Date").reset_index(drop=True)
        Feedback_ramis_2[['Start Date', 'End Date']] = Feedback_ramis_2['Flight_Date'] \
            .str.split(' - ', expand=True).apply(lambda x: x.str.strip())
        Feedback_ramis_2.drop(["Flight_Date"], axis=1, inplace=True)
    else:
        # To maintain consistency in output
        Feedback_ramis_2 = pd.DataFrame(columns=["Flight ID", "Comment", "Weekday", "Start Date", "End Date"])
    return Feedback_ramis_1,Feedback_ramis_2,expanded_ramis
