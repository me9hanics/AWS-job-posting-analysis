#Scrape website
import datetime
from collections import OrderedDict
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font
import time

import sys
import os
schedule_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.join(schedule_path, "..")
sys.path.append(parent_path)
from methods import actions, sites

KEYWORDS = sites.BASE_KEYWORDS
RANKINGS = sites.BASE_RANKINGS
SALARY_BEARABLE = sites.SALARY_BEARABLE

def reduce_url(url):
    return url.split("www.")[1] if "www." in url else url.split("://")[1] if "://" in url else url

def get_postings(keywords =KEYWORDS, rankings=RANKINGS, salary_bearable=SALARY_BEARABLE, prefix ="postings",
                 path="source/save/postings/", path_excel="source/save/excels/"):
    karriere_at = sites.KarriereATScraper(keywords=keywords, rankings=rankings, salary_bearable=salary_bearable)
    results = karriere_at.gather_data(verbose=False, descriptions=True)
    desired_order = ["title", "company",  "salary_monthly_guessed",
                     "locations", "keywords",
                     "points", "url", 
                     "snippet", "description", "salary",
                     "employmentTypes", "salary_guessed",
                     "collected_on", "date", "id", "isHomeOffice", "isActive", "source"]

    results = {
        key: OrderedDict(
            sorted(value.items(), key=lambda item: desired_order.index(item[0]) if item[0] in desired_order else len(desired_order))
        )
        for key, value in results.items()
    }

    raiffeisen = sites.RaiffeisenScraper(rules={"request_wait_time": 0.3}, keywords=keywords, rankings=rankings,
                                         salary_bearable=salary_bearable)
    results2 = raiffeisen.gather_data(descriptions=True, verbose=False)

    results = {**results, **results2}
    results = {k: v for k, v in sorted(results.items(), key=lambda item: item[1]["points"], reverse=True)}
    actions.save_data(results, with_date=True, path=path)

    gf_df = pd.DataFrame.from_dict(results,
                        orient = 'index')[['title', 'company', 'salary_monthly_guessed', 'locations', 'keywords', 'url', 'description', 'isHomeOffice', 'points']]
    gf_df = gf_df.rename(columns ={"points": "hanics_points"})
    gf_df["url"] = gf_df["url"].apply(lambda x: reduce_url(x))

    x = pd.DataFrame.from_dict(results, orient='index')
    x["locations"] = x["locations"].apply(lambda x: x if type(x) == list else [])
    companies = list(x[x['locations'].apply(lambda locs: any("wien" in loc.lower() or "vienna" in loc.lower() for loc in locs))]['company'].unique())
    file_name = actions.get_filename_from_dir(path, index = -2)
    added, removed = actions.compare_postings(results, f'{path}{file_name}', print_attrs =[])

    excel_file_path = None
    if path_excel:
        excel_file_path =f"{path_excel}{prefix}_{datetime.datetime.now().strftime('%Y-%m-%d')}.xlsx"
        gf_df.to_excel(excel_file_path, index = False)
        time.sleep(1)
        workbook = load_workbook(excel_file_path)
        sheet = workbook.active
        column_widths = {
            "A": 38,
            "B": 24,
            "C": 6.56,
            "D": 14.33,
            "E": 50.44,
            "F": 20.44,
            "G": 32,
            "H": 8,
            "I": 11,
        }
        for column, width in column_widths.items():
            sheet.column_dimensions[column].width = width

        #Make row bold, and columns bold
        for cell in sheet[1]:
            cell.font = Font(bold=True)

        for row in sheet.iter_rows(min_row=1, max_row=len(gf_df)+1):
            for cell in row:
                if cell.column_letter in ["B", "D", "E"]:
                    cell.font = Font(bold=True)
                if cell.column_letter == "F" and cell.row > 1:
                    #make it point to a link
                    cell.hyperlink = cell.value #"https://www." + cell.value
                    cell.style = 'Hyperlink'

        workbook.save(excel_file_path)

    output_dict = {
        "results": results,
        "added": added,
        "removed": removed,
        "companies": companies,
        "excel_file_path": excel_file_path,
    }
    return output_dict

def send_email(results, to_email, file_path = None, subject="Daily report", from_email=None):
    import smtplib
    #from email import encoders
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    body = f"Dear User, here is your report of the current relevant job postings.\n\nNew posting not seen before:\
            {'\n'.join(result['title'] + '\n\t at ' + result['company'] for id, result in results['added'].values())}\
            \n\nCurrently relevant companies: {'\n'.join(results['companies'])}\nBest regards,\n\tHanicsBot"
    msg = MIMEMultipart()
    msg.attach(MIMEText(body, 'plain'))

    with open("config.txt", "r") as f:
        pw = f.readline().split("\n")[0]
        if not from_email:
            from_email = f.readline()

    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    #msg['Bcc'] = from_email+"2"
    with open(file_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
        msg.attach(part)
    
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(from_email, pw)
        smtp.send_message(msg)

if __name__ == "__main__":
    data = get_postings()
    print("Found:" , len(data["results"]), "postings")
    #print(data) #find a nice format
