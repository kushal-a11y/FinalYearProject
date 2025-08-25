# Python code to download directly
import requests

datasets = {
    "Individual": "https://aws-icpsr-36151.s3.us-east-2.amazonaws.com/36151-0002-Data.dta",
    "Household": "https://aws-icpsr-36151.s3.us-east-2.amazonaws.com/36151-0003-Data.dta"
}

for name, url in datasets.items():
    print(f"Downloading {name} dataset...")
    r = requests.get(url)
    with open(f"ihds_{name.lower()}.dta", "wb") as f:
        f.write(r.content)
    print(f"✓ Saved {name} data")