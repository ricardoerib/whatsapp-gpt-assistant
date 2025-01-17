import schedule
import time
from app.dynamodb_client import table

def delete_old_data():
    cutoff = int(time.time()) - (12 * 30 * 24 * 60 * 60)
    response = table.scan()
    for item in response["Items"]:
        if item["timestamp"] < cutoff:
            table.delete_item(Key={"phone": item["phone"]})

def start_scheduler():
    schedule.every().day.at("00:00").do(delete_old_data)
    while True:
        schedule.run_pending()
        time.sleep(1)
