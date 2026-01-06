"""Demo of TravellerCalendar functionality.

Shows how to use the Imperial calendar with 13 months of 28 days.
"""

from t5code.T5Basics import TravellerCalendar


def main():
    cal = TravellerCalendar()

    print("Traveller Imperial Calendar Demo")
    print("=" * 50)
    print()

    # Holiday
    print("Day 001 (Holiday):")
    info = cal.get_month_info(1)
    print(f"  Month: {info['month']}")
    print(f"  Is Holiday: {info['is_holiday']}")
    print()

    # Sample days throughout the year
    sample_days = [1, 2, 15, 30, 100, 200, 338, 365]

    print("Sample days throughout the year:")
    print("-" * 50)
    for day in sample_days:
        info = cal.get_month_info(day)
        month = info['month']
        day_of_month = info['day_of_month']

        if info['is_holiday']:
            print(f"Day {day:03d}: Holiday")
        else:
            next_month_start = cal.get_next_month_start(day)
            print(f"Day {day:03d}: Month {month:2d}, Day {day_of_month:2d} "
                  f"(next month starts on day {next_month_start:03d})")
    print()

    # All month boundaries
    print("Month boundaries:")
    print("-" * 50)
    for month in range(1, 14):
        first_day = cal.get_first_day_of_month(month)
        last_day = first_day + 27
        print(f"Month {month:2d}: Days {first_day:03d}-{last_day:03d}")
    print()

    # Current day example
    current_day = 180  # Mid-year
    info = cal.get_month_info(current_day)
    next_start = cal.get_next_month_start(current_day)

    print(f"If today is day {current_day:03d}:")
    print(f"  We are in Month {info['month']}, Day {info['day_of_month']}")
    print(f"  Next month starts on day {next_start:03d}")
    print()

    # Integration with Traveller date format (DDD-YYYY)
    print("Integration example with Traveller date format:")
    print("-" * 50)
    traveller_date = "180-1105"
    day_of_year = int(traveller_date.split('-')[0])
    year = traveller_date.split('-')[1]

    info = cal.get_month_info(day_of_year)
    print(f"Date: {traveller_date}")
    print(f"  Month: {info['month']}")
    print(f"  Day of Month: {info['day_of_month']}")
    print(f"  Next month starts: "
          f"{cal.get_next_month_start(day_of_year):03d}-{year}")


if __name__ == "__main__":
    main()
