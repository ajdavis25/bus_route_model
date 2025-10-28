import pandas as pd
from datetime import datetime, timedelta


def parse_time(tstr, base_date):
    """convert HH:MM string into datetime object on base_date"""
    if pd.isna(tstr):
        return None
    tstr = str(tstr).strip()[-5:]  # keep last 5 chars (HH:MM)
    try:
        t = datetime.strptime(tstr, "%H:%M").time()
        return datetime.combine(base_date, t)
    except ValueError:
        return None


def scheduled_bus_trips(schedule, stop_from, stop_to):
    """return scheduled bus departures, arrivals, and travel times"""
    base_date = datetime.today().date()
    trips = []

    for _, row in schedule.iterrows():
        dep = parse_time(row.get(stop_from), base_date)
        arr = parse_time(row.get(stop_to), base_date)
        if dep is None or arr is None:
            continue
        if arr <= dep:
            arr += timedelta(days=1)  # handle overnight trips
        travel = (arr - dep).total_seconds() / 60
        trips.append({
            "bus_departure": dep.strftime("%H:%M"),
            "bus_arrival": arr.strftime("%H:%M"),
            "travel_time (min)": round(travel, 1)
        })

    return pd.DataFrame(trips)


def stagger_501(schedule_501, stop_from, stop_to, interval_minutes, num_copies=1):
    """generate additional 501 buses staggered by interval_minutes"""
    all_rows = [schedule_501]  # include original

    for i in range(1, num_copies + 1):
        shifted = schedule_501.copy()
        for col in [stop_from, stop_to]:
            shifted[col] = shifted[col].apply(lambda t: (
                datetime.strptime(str(t).strip()[-5:], "%H:%M") + timedelta(minutes=i * interval_minutes)
            ).strftime("%H:%M") if pd.notna(t) else t)
        all_rows.append(shifted)

    # combine all and sort by departure time
    combined = pd.concat(all_rows, ignore_index=True)
    combined_sorted = scheduled_bus_trips(combined, stop_from, stop_to)
    combined_sorted = combined_sorted.sort_values(by="bus_departure").reset_index(drop=True)
    return combined_sorted


def offset_original(df, offset_minutes):
    """add fixed offset to both departure and arrival times in a scheduled_bus_trips DataFrame"""
    offset = timedelta(minutes=offset_minutes)
    new_df = df.copy()
    new_df["bus_departure"] = new_df["bus_departure"].apply(
        lambda t: (datetime.strptime(t, "%H:%M") + offset).strftime("%H:%M")
    )
    new_df["bus_arrival"] = new_df["bus_arrival"].apply(
        lambda t: (datetime.strptime(t, "%H:%M") + offset).strftime("%H:%M")
    )
    return new_df


if __name__ == "__main__":
    # load schedules
    schedule_501 = pd.read_csv("501schedule_northbound.csv")
    schedule_603 = pd.read_csv("603schedule_northbound.csv")

    # define stops
    stop_from = "Medical Center Transit Center"
    stop_to = "UTSA"

    # get scheduled trips
    df_501 = scheduled_bus_trips(schedule_501, stop_from, stop_to)
    df_603 = scheduled_bus_trips(schedule_603, stop_from, stop_to)

    # print results
    print("route 501:")
    print(df_501.to_string(index=False))
    print("\nroute 603:")
    print(df_603.to_string(index=False))

    """
    # show offset versions
    print("\nroute 501 offset by +15 minutes:")
    df_501_offset_15 = offset_original(df_501, 15)
    print(df_501_offset_15.to_string(index=False))

    print("\nroute 501 offset by +45 minutes:")
    df_501_offset_45 = offset_original(df_501, 45)
    print(df_501_offset_45.to_string(index=False))

    print("\nroute 603 offset by +15 minutes:")
    df_603_offset_15 = offset_original(df_603, 15)
    print(df_603_offset_15.to_string(index=False))

    print("\nroute 603 offset by +45 minutes:")
    df_603_offset_45 = offset_original(df_603, 45)
    print(df_603_offset_45.to_string(index=False))
    """

    print("\noriginal 501 + 1 staggered every 30 min:")
    df_501_stagger_30 = stagger_501(schedule_501, stop_from, stop_to, 30, num_copies=1)
    print(df_501_stagger_30.to_string(index=False))

    print("\n501 staggered to get ~15 min frequency (add 3 extra buses):")
    df_501_stagger_15 = stagger_501(schedule_501, stop_from, stop_to, 15, num_copies=3)
    print(df_501_stagger_15.to_string(index=False))

    print("\n501 staggered to get ~10 min frequency (add 5 extra buses):")
    df_501_stagger_10 = stagger_501(schedule_501, stop_from, stop_to, 10, num_copies=5)
    print(df_501_stagger_10.to_string(index=False))
