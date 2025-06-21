import pandas as pd


weekday_map = {
    'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
    'Friday': 4, 'Saturday': 5, 'Sunday': 6
}



def count_weekdays(start, end, weekday_name):
  try:
    weekday_num = weekday_map[weekday_name]
    dates = pd.date_range(start, end, freq='D')
    return sum(d.weekday() == weekday_num for d in dates)
  except:
    return 0


def group_date_ranges(dates, expected_gap_days=7):
    dates = pd.to_datetime(dates)
    dates = pd.Series(dates).sort_values().reset_index(drop=True)

    groups = []
    start = dates[0]

    for i in range(1, len(dates)):
        gap = (dates[i] - dates[i-1]).days
        if gap != expected_gap_days:
            groups.append(f"{start.date()} - {dates[i-1].date()}")
            start = dates[i]
    groups.append(f"{start.date()} - {dates.iloc[-1].date()}")

    return groups