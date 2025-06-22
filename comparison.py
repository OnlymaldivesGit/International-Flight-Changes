from ramis_cleaning import ramis_cleaning_fun
from macl_cleaning import macl_cleaning_fun
import pandas as pd
import calendar
from ramis_functions import group_date_ranges
from datetime import time


def comparison_fun(ramis_int,macl_int, curr_date, Start_Period_date,End_Period_date):
    _, _,expanded_ramis=ramis_cleaning_fun(ramis_int, curr_date, Start_Period_date,End_Period_date )
    _, _,macl_expanded=macl_cleaning_fun(macl_int, curr_date, Start_Period_date,End_Period_date)


    expanded_ramis = expanded_ramis[expanded_ramis["Flight Date"] > curr_date]
    expanded_ramis = expanded_ramis[
        ((expanded_ramis["Type"] == "Arrival") &
            (expanded_ramis["Scheduled Time"] > time(4, 0, 0)) &
            (expanded_ramis["Scheduled Time"] < time(17, 0, 0)))|
            (expanded_ramis["Type"] == "Departure")]
    expanded_ramis=expanded_ramis[expanded_ramis['Connecting Flight Entries']==expanded_ramis['Weekday Count']]


    macl_expanded["Date"] = pd.to_datetime(macl_expanded["Date"])
    macl_expanded['Time'] = pd.to_datetime(macl_expanded['Time'], format='%H:%M:%S').dt.time
    macl_expanded = macl_expanded[macl_expanded["Date"] > curr_date]
    macl_expanded = macl_expanded[
        ((macl_expanded["Type"] == "Arrival") &
        (macl_expanded["Time"] > time(4, 0, 0)) &
        (macl_expanded["Time"] < time(17, 0, 0)))|
        (macl_expanded["Type"] == "Departure")]

    macl_expanded.columns=['AIRLINE', 'A/C TYPE', 'ROUTE', 'Flight ID', 'Scheduled Time', 'SEATS',
        'Type', 'Flight Date']


    macl_expanded["key"] = (
    macl_expanded["Flight ID"].astype(str) +
    macl_expanded["Flight Date"].astype(str)
    )

    expanded_ramis["key"] = (
        expanded_ramis["Flight ID"].astype(str) +
        expanded_ramis["Flight Date"].astype(str)
    )

    merged_df=macl_expanded.merge(expanded_ramis, on=["key"], how='outer',indicator=True)
    
    merged_df.columns=['AIRLINE_macl', 'A/C TYPE_macl', 'ROUTE_macl', 'Flight ID_macl', 'Scheduled Time_macl',
       'SEATS_macl',  'Type_macl',  'Flight Date_macl', 'key',
       'Flight ID_ramis', 'Type_ramis', 'Flight Date_ramis', 'Scheduled Time_ramis', "Connecting Flight Entries	ramis","Weekday Count	ramis",
       '_merge']


    merged_df["Diff_time"] = merged_df.apply(
    lambda row: "Modified"
    if (row["Scheduled Time_macl"] != row["Scheduled Time_ramis"]) and row["_merge"] == "both"
    else "-",
    axis=1
    )


    Added=merged_df[merged_df["_merge"]=="left_only"]
    Added=Added[["Flight ID_macl","Scheduled Time_macl","Flight Date_macl"]]
    Added["Weekday"]=Added['Flight Date_macl'].apply(lambda x: calendar.day_name[x.weekday()])
    Added.columns=['Flight ID','Scheduled Time','Flight Date','Weekday']
    Added.reset_index(drop=True, inplace=True)


    Deleted=merged_df[merged_df["_merge"]=="right_only"]
    Deleted=Deleted[["Flight ID_ramis","Scheduled Time_ramis","Flight Date_ramis"]]
    Deleted["Weekday"]=Deleted['Flight Date_ramis'].apply(lambda x: calendar.day_name[x.weekday()])
    Deleted.columns=['Flight ID','Scheduled Time','Flight Date','Weekday']
    Deleted.reset_index(drop=True, inplace=True)


    modified =merged_df[merged_df["Diff_time"]=="Modified"]
    modified=modified[["Flight ID_macl","Flight Date_macl","Scheduled Time_ramis","Scheduled Time_macl"]]
    modified.columns=["Flight ID","Flight Date","Time_ramis","Time_macl"]
    modified["Weekday"]=modified['Flight Date'].apply(lambda x: calendar.day_name[x.weekday()])
    


    clubbed_added = Added.groupby(["Flight ID", "Scheduled Time", "Weekday"]).agg(list).reset_index()
    clubbed_added["Flight_Date"] = clubbed_added["Flight Date"].apply(group_date_ranges)
    clubbed_added.drop(columns=["Flight Date"], inplace=True)
    clubbed_added=clubbed_added.explode("Flight_Date").reset_index(drop=True)
    clubbed_added[['Start Date', 'End Date']] = clubbed_added['Flight_Date'].str.split(' - ', expand=True).apply(lambda x: x.str.strip())
    clubbed_added.drop(["Flight_Date"], axis=1, inplace=True)


    clubbed_modified = modified.groupby(["Flight ID", "Time_ramis","Time_macl", "Weekday"]).agg(list).reset_index()
    clubbed_modified["Flight_Date"] = clubbed_modified["Flight Date"].apply(group_date_ranges)
    clubbed_modified.drop(columns=["Flight Date"], inplace=True)
    clubbed_modified=clubbed_modified.explode("Flight_Date").reset_index(drop=True)
    clubbed_modified[['Start Date', 'End Date']] = clubbed_modified['Flight_Date'].str.split(' - ', expand=True).apply(lambda x: x.str.strip())
    clubbed_modified.drop(["Flight_Date"], axis=1, inplace=True)


    clubbed_deleted = Deleted.groupby(["Flight ID", "Scheduled Time", "Weekday"]).agg(list).reset_index()
    clubbed_deleted["Flight_Date"] = clubbed_deleted["Flight Date"].apply(group_date_ranges)
    clubbed_deleted.drop(columns=["Flight Date"], inplace=True)
    clubbed_deleted=clubbed_deleted.explode("Flight_Date").reset_index(drop=True)
    clubbed_deleted[['Start Date', 'End Date']] = clubbed_deleted['Flight_Date'].str.split(' - ', expand=True).apply(lambda x: x.str.strip())
    clubbed_deleted.drop(["Flight_Date"], axis=1, inplace=True)

    return clubbed_added,clubbed_modified,clubbed_deleted