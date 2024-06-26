import jq
import os
import requests

from requests_html import HTML
from urllib.parse import urlencode
from urllib.request import urlretrieve
from datetime import datetime, timedelta

URL_BASE = "https://www1.hkexnews.hk"
SEARCH_PATH = "/search/titlesearch.xhtml?lang=en"
PREFIX_PATH = "/search/partial.do?"
VERB = "POST"
OUTPUT_FOLDER_PATH = "out"

# FROM_DATE = "20070625"    # Download all historical reports
FROM_DATE = (datetime.today() + timedelta(days=-365)).strftime("%Y%m%d")    # Only download latest reports from the last year
TO_DATE = datetime.today().strftime("%Y%m%d")

STOCK_CODE_LIST = [
    1,
    2,
    3,
    5,
    6,
    11,
    12,
    16,
    17,
    27,
    66,
    101,
    175,
    241,
    267,
    288,
    291,
    316,
    322,
    386,
    388,
    669,
    688,
    700,
    762,
    823,
    836,
    857,
    868,
    881,
    883,
    939,
    941,
    960,
    968,
    981,
    992,
    1038,
    1044,
    1088,
    1093,
    1099,
    1109,
    1113,
    1177,
    1209,
    1211,
    1299,
    1378,
    1398,
    1810,
    1876,
    1928,
    1929,
    1997,
    2015,
    2020,
    2269,
    2313,
    2318,
    2319,
    2331,
    2359,
    2382,
    2388,
    2628,
    2688,
    2899,
    3690,
    3692,
    3968,
    3988,
    6098,
    6618,
    6690,
    6862,
    9618,
    9633,
    9888,
    9961,
    9988,
    9999
]

# list of report types to download and their query args (minus stockId filter which is added at runtime)
REPORT_TYPE_ARGUMENTS = {
    "Annual Report": {
        "lang":"EN", 
        "category":0, 
        "market":"SEHK", 
        "searchType":1, 
        "documentType":-1, 
        "t1code":40000, 
        "t2Gcode":-2, 
        "t2code":40100,  
        "from":FROM_DATE, 
        "to":TO_DATE, 
        "MB-Daterange":0, 
        "title": ''
    },
    "ESG": {
        "lang":"EN", 
        "category":0, 
        "market":"SEHK", 
        "searchType":1, 
        "documentType":-1, 
        "t1code":40000, 
        "t2Gcode":-2, 
        "t2code":40400,  
        "from":FROM_DATE, 
        "to":TO_DATE, 
        "MB-Daterange":0, 
        "title": ''
    }
}

def filter_pdf_and_sort(links):
    return sorted(
        [
            l 
            for l in links 
            if l[:10] == "/listedco/" and l[-4:] == ".pdf"
        ], 
        reverse=True
    )

def get_stock_info(stock_code):
    query = {
        "callback":"callback",
        "lang":"EN",
        "type":"A",
        "name": stock_code,
        "market=SEHK"
        "_": int(datetime.now().timestamp() * 1000)
    }

    prefix_url = "".join([URL_BASE, PREFIX_PATH, urlencode(query)])
    x = requests.get(prefix_url)
    
    # callback({"more":"0","stockInfo":[{"stockId":1,"code":"00001","name":"CKH HOLDINGS"}, ...]});
    return jq.compile('.stockInfo[]').input_text(x.text[9:-4]).first()


def download_reports(stock_info, report_type, stock_output_path):
    print(f"Downloading {report_type}(s) from {FROM_DATE} to {TO_DATE} for {stock_info} ...")

    report_output_path = os.path.join(stock_output_path, report_type)
    if not os.path.exists(report_output_path):
        os.mkdir(report_output_path)

    search_url = "".join([URL_BASE, SEARCH_PATH])
    form_data = REPORT_TYPE_ARGUMENTS[report_type].copy()
    form_data["stockId"] = stock_info["stockId"]
    x = requests.post(search_url, data=form_data)
    html = HTML(html=x.text)
    report_links = filter_pdf_and_sort(html.links)

    for report_path in report_links:
        download_single_report_link(report_path, report_output_path)


def download_single_report_link(report_path, output_path):
    output_file = report_path.split("/")[-1]
    report_url = f"{URL_BASE}{report_path}"
    output_filepath = os.path.join(output_path, output_file)

    if os.path.exists(output_filepath):
        print(f"Report {output_filepath} already exists, skipping...")
        return
    
    print(f"Downloading report {report_url} to {output_filepath}...")
    urlretrieve(url=report_url, filename=output_filepath)

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_FOLDER_PATH):
        os.mkdir(OUTPUT_FOLDER_PATH)

    for stock_code in STOCK_CODE_LIST:
        # {"stockId":1,"code":"00001","name":"CKH HOLDINGS"}
        stock_info = get_stock_info(stock_code)

        stock_output_path = os.path.join(OUTPUT_FOLDER_PATH, f'{stock_info["code"]}-{stock_info["name"]}')
        if not os.path.exists(stock_output_path):
            os.mkdir(stock_output_path)

        for report_type in REPORT_TYPE_ARGUMENTS.keys():
            download_reports(stock_info, report_type, stock_output_path)
            print()

    print("Finished downloading.")
    