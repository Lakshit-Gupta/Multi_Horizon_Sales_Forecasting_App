import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# Load historical data (37 entries)
def generate_input():
    base_date = datetime(2017, 7, 1)
    store_nbr = "1"
    item_nbr = "96995"
    input_data = []

    for i in range(37):
        date = base_date + timedelta(days=i)
        log_sales = 1.0 + 0.01 * i  # slight upward trend
        on_promo = "1" if i % 7 == 0 else "0"  # simulate weekly promo
        holiday = "1" if i == 15 else "0"  # fake holiday
        transactions = 100 + (i % 10) * 3  # simulate some variation

        input_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "store_nbr": store_nbr,
            "item_nbr": item_nbr,
            "is_onpromotion": on_promo,
            "is_holiday": holiday,
            "transactions": transactions,
            "log_unit_sales": log_sales
        })

    return input_data


url = "http://127.0.0.1:5000/api/forecast"
payload = {
    "timeseries": generate_input(),
    "forecast_days": 7  # change to 30 for 30-day forecast
}

response = requests.post(url, json=payload)

try:
    data = response.json()
    if "prediction" in data:
        preds = data["prediction"][0]
        print("Success:")
        for i, val in enumerate(preds):
            print(f"Day {i+1}: {round(val, 2)}")

        # Plotting
        future_days = list(range(1, len(preds) + 1))
        plt.plot(future_days, preds, marker='o')
        plt.xlabel("Day")
        plt.ylabel("Predicted log_unit_sales")
        plt.title("Forecast")
        plt.grid(True)
        plt.show()
    else:
        print(" Error:")
        print(data)
except Exception as e:
    print(" Failed to parse response:", e)
