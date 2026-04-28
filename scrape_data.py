import json
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


DATA_URL = "https://www.gladtidingsdata.com/data_Create/"
OUTPUT_FILE = "data/data_plans.json"


NETWORKS = {
    "1": "MTN",
    "2": "GLO",
    "3": "AIRTEL",
    "6": "9MOBILE",
}


DATA_TYPES = [
    "GIFTING",
    "CORPORATE GIFTING",
    "SME",
    "SME2",
    "DATA COUPONS",
    "DATA SHARE",
    "MTN AWOOF",
    "TALKMORE",
    "SPECIAL",
]


def clean_price(price_text):
    price_text = price_text.replace("₦", "").strip()
    price_text = re.sub(r"\s+", "", price_text)
    return float(price_text)


def parse_plan_text(text):
    clean_text = re.sub(r"\s+", " ", text).strip()

    data_match = re.search(r"(\d+(\.\d+)?\s?(MB|GB))", clean_text, re.IGNORECASE)
    validity_match = re.search(r"(\d+\s?(day|days|month|months))", clean_text, re.IGNORECASE)
    note_match = re.search(r"\[(.*?)\]", clean_text)

    return {
        "raw_text": clean_text,
        "data": data_match.group(1).upper().replace(" ", "") if data_match else None,
        "validity": validity_match.group(1) if validity_match else None,
        "note": note_match.group(1) if note_match else None,
    }


driver = webdriver.Chrome()
driver.get(DATA_URL)

input("Log in manually, open the data page, then press ENTER here to continue...")

print("Starting scraper...")
print("Current page:", driver.current_url)

all_plans = []

for network_value, network_name in NETWORKS.items():
    print(f"Selecting network: {network_name}")
    network_select = Select(driver.find_element(By.ID, "id_network"))
    network_select.select_by_value(network_value)
    time.sleep(2)

    for data_type in DATA_TYPES:
        print(f"  Selecting data type: {data_type}")
        try:
            data_type_select = Select(driver.find_element(By.ID, "id_data_type"))
            data_type_select.select_by_value(data_type)
            time.sleep(2)

            plan_select = driver.find_element(By.ID, "id_plan")
            options = plan_select.find_elements(By.TAG_NAME, "option")

            for option in options:
                plan_id = option.get_attribute("value")

                if not plan_id:
                    continue

                plan_type = option.get_attribute("plantype")
                amount_text = option.get_attribute("amt")
                option_text = option.text

                if not amount_text:
                    continue

                parsed = parse_plan_text(option_text)

                plan_data = {
                    "network": network_name,
                    "plan_id": plan_id,
                    "plan_type": plan_type,
                    "price": clean_price(amount_text),
                    "data": parsed["data"],
                    "validity": parsed["validity"],
                    "note": parsed["note"],
                    "raw_text": parsed["raw_text"],
                    "source": "GladTidingsData",
                }

                all_plans.append(plan_data)

        except Exception as e:
            print(f"Skipped {network_name} - {data_type}: {e}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(all_plans, file, indent=4, ensure_ascii=False)

print(f"Done. Saved {len(all_plans)} plans to {OUTPUT_FILE}")

driver.quit()