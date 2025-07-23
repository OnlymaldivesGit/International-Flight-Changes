import pandas as pd
from datetime import timedelta


def extract_start_end(date_str):
    if '-' in date_str:
        start, end = date_str.split('-')
    else:
        start = end = date_str
    return pd.Series([start.strip(), end.strip()])



def transform_flt_code(code):
    if pd.isna(code) or '-' not in code:
        return code  # Return as-is if invalid

    prefix, suffix = code.split('-')
    num_digits_to_replace = len(suffix)
    new_value = prefix[:-num_digits_to_replace] + suffix
    return f"{prefix} - {new_value}"

def classify_direction(route):
    if pd.isna(route):
        return 'Unknown'

    has_in = '-MLE' in route
    has_out = 'MLE-' in route

    if has_in and has_out:
        in_index = route.find('-MLE')
        out_index = route.find('MLE-')
        return 'Arrival-Departure' if in_index < out_index else 'Departure-Arrival'
    elif has_in:
        return 'Arrival'
    elif has_out:
        return 'Departure'
    else:
        return 'Unknown'

def replace_flt_no(row):
    flt = str(row['FLT NO'])
    direction = row['Direction']

    if '-' not in flt and direction in ['Arrival-Departure', 'Departure-Arrival']:
        if direction == 'Arrival-Departure':
            return f"{flt}-{flt}D"
        else:  # Departure-Arrival
            return f"{flt}D-{flt}"
    return flt


def split_list(row):
    if isinstance(row, list):
        first = row[0]
        second = row[1] if len(row) > 1 else '-'
        return pd.Series([first, second])
    else:
        return pd.Series(['-', '-'])  # fallback for invalid rows


def convert_to_time(val):
    try:
        if val == "-":
            return val
        val = str(val).zfill(3)
        minutes = val[-2:]
        hours = val[:-2] or '0'
        return pd.to_datetime(f'{hours}:{minutes}', format='%H:%M').time()
    except:
        return pd.NaT  # Fallback if parsing fails


def get_operating_days(day_str):
    return [int(char) for i, char in enumerate(day_str) if char != '0']  # Mon=1, ..., Sun=7


def expanded_macl(macl_int):
    schedule_rows_v1 = []
    for _, row in macl_int.iterrows():
        days_of_week = get_operating_days(row['DAYS OF OPS'])
        current_date = row['Start Date']
        while current_date <= row['End Date']:
            # Convert Python weekday (Mon=0 to Sun=6) to 1-based (Mon=1 to Sun=7)
            if (current_date.weekday() + 1) in days_of_week:
                schedule_rows_v1.append({
                    'AIRLINE': row['AIRLINE'],
                    'A/C TYPE': row['A/C TYPE'],
                    'ROUTE': row['ROUTE'],
                    'Flight Code': row['Flight Code'],
                    'Time': row['Time'],
                    'SEATS': row['SEATS'],
                    'Type': row['Type'],
                    'status': row['status'],
                    'Date': current_date.strftime('%Y-%m-%d')
                })
            current_date += timedelta(days=1)
    macl_expanded = pd.DataFrame(schedule_rows_v1)
    # macl_expanded.drop_duplicates(inplace=True)
    macl_expanded["Date"] = pd.to_datetime(macl_expanded["Date"]).dt.date

    return macl_expanded