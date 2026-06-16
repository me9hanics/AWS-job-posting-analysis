"""Output helpers for reports, Excel exports, and email notifications."""

import datetime
import os
import pandas as pd
from jobscraping.config.constants import EXCEL_COLUMNS
from jobscraping.config.configs import RELATIVE_EXCELS_PATH
from jobscraping.io.outputs_excel import create_excel_report
from jobscraping.utils.urls import reduce_url

def categorize_postings_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    Categorize postings by date ranges and return DataFrame sorted with separator markers.
    Categories: Last 7 days, Last 2 weeks, Last 4 weeks (2-4), Older than 4 weeks
    Adds a '_separator' column to mark group boundaries.
    """
    today = datetime.datetime.now()
    one_week_ago = today - datetime.timedelta(days=7)
    two_weeks_ago = today - datetime.timedelta(days=14)
    four_weeks_ago = today - datetime.timedelta(days=28)
    
    def get_category(row: pd.Series) -> int:
        try:
            if 'first_collected_on' in row and row['first_collected_on']:
                date = datetime.datetime.strptime(row['first_collected_on'], "%Y-%m-%d")
                if date >= one_week_ago:
                    return 0
                if date >= two_weeks_ago:
                    return 1
                if date >= four_weeks_ago:
                    return 2
                return 3
            return 3
        except (ValueError, TypeError):
            return 3

    df['_category'] = df.apply(get_category, axis=1)
    df['_points'] = pd.to_numeric(df['points'], errors='coerce').fillna(0)
    df = df.sort_values(
        by=['_category', '_points'],
        ascending=[True, False],
    )

    category_labels = {
        0: "Postings last 7 days - SCROLL FOR OLDER!!!",
        1: "Last 2 weeks postings:",
        2: "Last 4 weeks postings",
        3: "Older postings",
    }
    current_category = None
    separators = []
    
    for idx, (_, row) in enumerate(df.iterrows()):
        cat = row['_category']
        if cat != current_category:
            separators.append((idx, category_labels[cat]))
            current_category = cat

    df['_separator'] = ""
    for idx, label in separators:
        df.iloc[idx, df.columns.get_loc('_separator')] = label

    return df


def generate_outputs(
    results: dict,
    added: dict | None = None,
    keywords: dict | None = None,
    excel_cols: dict | None = None,
    excel_prefix: str = "postings",
    path_excel: str = RELATIVE_EXCELS_PATH,
    verbose: bool = False,
    highlight_first_collected_days: int | None = None,
) -> dict:
    """Generate outputs and return the Excel file path if created."""
    if not path_excel or results is None:
        return {"excel_file_path": None}

    if excel_cols is None:
        excel_cols = EXCEL_COLUMNS

    df = pd.DataFrame.from_dict(results, orient='index')
    for col, vals in excel_cols.items():
        if col not in df.columns:
            df[col] = ""

    cols_ids = [vals['column'] for _, vals in excel_cols.items()]
    cols_ids_sorted = sorted(cols_ids, key=lambda x: (len(x), x))
    cols_sorted = [
        key for col_id in cols_ids_sorted
        for key, vals in excel_cols.items() if vals['column'] == col_id
    ]
    if 'first_collected_on' not in cols_sorted and 'first_collected_on' in df.columns:
        cols_sorted.append('first_collected_on')

    highlight_titles = None
    if highlight_first_collected_days is not None:
        cutoff = datetime.datetime.now() - datetime.timedelta(days=highlight_first_collected_days)
        highlight_titles = []
        for _, row in df.iterrows():
            date_str = row.get("first_collected_on")
            if not date_str:
                continue
            try:
                date_value = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                continue
            if date_value >= cutoff:
                title = row.get("title")
                if title:
                    highlight_titles.append(title)

    excel_df = df[cols_sorted].copy()
    excel_df = categorize_postings_by_date(excel_df)

    if 'url' in excel_df.columns:
        excel_df.loc[:, "url"] = excel_df["url"].apply(reduce_url)

    excel_df = excel_df.rename(columns={col: vals['as'] for col, vals in excel_cols.items()})
    excel_file_path = create_excel_report(
        excel_df,
        path_excel=path_excel, prefix=excel_prefix,
        added=added, keywords=keywords, throw_error=True,
        widths={vals['column']: vals.get('width', 20) for _, vals in excel_cols.items()},
        highlight_titles=highlight_titles,
    )
    if verbose:
        print(f"Excel report created at {excel_file_path}")

    return {"excel_file_path": excel_file_path}


def log_to_markdown(postings: dict, log_file_path: str = "newly_added_history.md") -> None:
    """
    Prepend (add to top) postings (typically newly added ones) to a markdown log file.
    Newest entries appear at the top.
    
    Parameters:
    added (dict): Dictionary of newly added postings
    log_file_path (str): Path to the markdown log file
    """
    if not postings:
        return
    log_dir = os.path.dirname(log_file_path)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    existing_content = ""
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as file_obj:
            existing_content = file_obj.read()
    with open(log_file_path, 'w', encoding='utf-8') as file_obj:
        file_obj.write(f"### {timestamp}\n")
        for _key, posting in postings.items():
            if "title" in posting and "company" in posting:
                file_obj.write(f"{posting['title']} - at - {posting['company']}\n")
        file_obj.write("\n")
        if existing_content:
            file_obj.write(existing_content)

def send_email(
    results: dict,
    to_email: str,
    file_path: str | None = None,
    subject: str = "Daily report",
    from_email: str | None = None,
) -> None:
    """Send a report email with the Excel file attached."""
    import smtplib  # pylint: disable=import-outside-toplevel
    #from email import encoders
    from email.mime.base import MIMEBase  # pylint: disable=import-outside-toplevel
    from email.mime.text import MIMEText  # pylint: disable=import-outside-toplevel
    from email.mime.multipart import MIMEMultipart  # pylint: disable=import-outside-toplevel

    new_postings = "\n".join(
        result['title'] + "\n\t at " + result['company']
        for posting_id, result in results['added'].items()
    )
    companies_list = "\n".join(results['companies'])

    body = (
        "Dear User, here is your report of the current relevant job postings.\n\n"
        f"New posting not seen before:\n{new_postings}\n\n"
        f"Currently relevant companies:\n{companies_list}\n\n"
        "Best regards,\n\tHanicsBot"
    )
    msg = MIMEMultipart()
    msg.attach(MIMEText(body, 'plain'))

    with open("config.txt", "r", encoding="utf-8") as file_obj:
        password = file_obj.readline().split("\n")[0]
        if not from_email:
            from_email = file_obj.readline()

    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    #msg['Bcc'] = from_email+"2"
    with open(file_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={os.path.basename(file_path)}',
        )
        msg.attach(part)

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(from_email, password)
        smtp.send_message(msg)
