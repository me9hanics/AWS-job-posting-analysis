#Scrape website
import datetime
from collections import OrderedDict
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font
import time
from copy import copy

import sys
import os
schedule_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.join(schedule_path, "..")
sys.path.append(parent_path)
from methods import actions, sites, macros
from methods.macros import *

KEYWORDS = macros.BASE_KEYWORDS.copy()
RANKINGS = macros.BASE_RANKINGS.copy()
SALARY_BEARABLE = macros.SALARY_BEARABLE
COLUMN_WIDTHS = {"A": 38, "B": 24, "C": 6.56, "D": 14.33, "E": 50.44,
                 "F": 20.44, "G": 6, "H": 11, "I": 114,
                } #TODO put macros in a separate file

def reduce_url(url):
    return url.split("www.")[1] if "www." in url else url.split("://")[1] if "://" in url else url

def get_postings(keywords =KEYWORDS, rankings=RANKINGS, salary_bearable=SALARY_BEARABLE, prefix ="postings", path=f"{RELATIVE_POSTINGS_PATH}/", 
                 path_excel=f"{RELATIVE_EXCELS_PATH}/", verbose=False, verbose_data_gathering=False, **kwargs):
    keywords['titlewords'] = list(set(keywords['titlewords']))
    karriere_at = sites.KarriereATScraper(keywords=keywords, rankings=rankings, salary_bearable=salary_bearable,
                                          extra_keywords=kwargs.get("karriereat_extra_keywords", kwargs.get("extra_keywords", {})),
                                          extra_titlewords=kwargs.get("karriereat_extra_titlewords", kwargs.get("extra_titlewords", [])),
                                          extra_locations=kwargs.get("karriereat_extra_locations", kwargs.get("extra_locations", [])))
    results = karriere_at.gather_data(verbose=verbose_data_gathering, descriptions=True)
    desired_order = ["title", "company",  "salary_monthly_guessed",
                     "locations", "keywords",
                     "points", "url", 
                     "snippet", "description", "salary",
                     "employmentTypes", "salary_guessed",
                     "collected_on", "date", "id", "isHomeOffice", "isActive", "source"]

    results = {
        key: dict(OrderedDict( #TODO Write function to sort dict keys, use actions.reorder_dict
            sorted(value.items(), key=lambda item: desired_order.index(item[0]) if item[0] in desired_order else len(desired_order))
        ))
        for key, value in results.items()
    }
    if verbose:
        print(f"Found {len(results)} postings on Karriere.at")

    raiffeisen = sites.RaiffeisenScraper(rules={"request_wait_time": 0.3}, keywords=keywords,
                                         extra_keywords=kwargs.get("raiffeisen_extra_keywords", kwargs.get("extra_keywords", {})),
                                         extra_titlewords=kwargs.get("raiffeisen_extra_titlewords", kwargs.get("extra_titlewords", [])),
                                         extra_locations=kwargs.get("raiffeisen_extra_locations", kwargs.get("extra_locations", [])),
                                         rankings=rankings, salary_bearable=salary_bearable)
    results2 = raiffeisen.gather_data(descriptions=True, verbose=verbose_data_gathering)

    if verbose:
        print(f"Found {len(results2)} postings on Raiffeisen.at")
    results = {**results, **results2}
    results = {k: v for k, v in sorted(results.items(), key=lambda item: item[1]["points"], reverse=True)}
    if verbose:
        print(f"Found {len(results)} postings in total")
    actions.save_data(results, with_date=True, path=path)

    gf_df = pd.DataFrame.from_dict(results,
                        orient = 'index')[['title', 'company', 'salary_monthly_guessed', 'locations', 'keywords', 'url', 'isHomeOffice', 'points', 'description',]]
    gf_df = gf_df.rename(columns ={"points": "hanics_points"})
    gf_df["url"] = gf_df["url"].apply(lambda x: reduce_url(x))

    x = pd.DataFrame.from_dict(results, orient='index')
    x["locations"] = x["locations"].apply(lambda x: x if type(x) == list else [])
    companies = list(x[x['locations'].apply(lambda locs: any("wien" in loc.lower() or "vienna" in loc.lower() for loc in locs))]['company'].unique())
    file_name = actions.get_filename_from_dir(path, index = -2) #if there is no file, returns None
    added, removed = actions.compare_postings(results, f'{path}{file_name}' if file_name else [], print_attrs =[])
    if verbose:
        print(f"Added {len(added)} postings, removed {len(removed)} postings")
    excel_file_path = None
    if path_excel:
        excel_file_path =f"{path_excel}{prefix}_{datetime.datetime.now().strftime('%Y-%m-%d')}.xlsx"
        gf_df.to_excel(excel_file_path, index = False)
        time.sleep(1)
        workbook = load_workbook(excel_file_path)
        sheet = workbook.active
        for column, width in COLUMN_WIDTHS.items():
            sheet.column_dimensions[column].width = width

        #Make row bold, and columns bold
        for cell in sheet[1]:
            cell.font = cell.font + Font(bold=True)

        #Make those rows green text which are in the added postings, and highlight title companies with red names
        added_titles = [instance["title"] for instance in added.values()]
        for row in sheet.iter_rows(min_row=2, max_row=len(gf_df)+1):
            if row[0].value in added_titles:
                for cell in row:
                    if cell.column_letter in ["A", "E"]:
                        font = copy(cell.font) #TODO pack this into a function - or class method e.g. cell.update_font(color = ..., ...)
                        font.color = "FF229F22"
                        cell.font = font
            if any(company_title in row[1].value.lower() for company_title in keywords["highlighted_company_titles"] if type(row[1].value) == str):
                for cell in row:
                    if cell.column_letter in ["B"]:
                        font = copy(cell.font)
                        font.color = "E30A0A"
                        cell.font = font

        #Bold columns, hyperlink
        for row in sheet.iter_rows(min_row=1, max_row=len(gf_df)+1):
            for cell in row:
                if cell.column_letter in ["B", "D", "E"]:
                    cell.font = cell.font + Font(bold=True)
                if cell.column_letter == "F" and cell.row > 1:
                    url = cell.value
                    if url and not (str(url).startswith("https://") or str(url).startswith("http://")):
                        url = "https://" + str(url)
                    cell.hyperlink = url
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
