'''
Auto Email Program
By: Andy Duong
//Description\\
y -> sends email
n -> regenerates email
skip -> skips entry
hw -> sets status to handwrite (indicates the email must be handwritten)
'''
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import os
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

sheet = client.open("Email Test").sheet1

data = sheet.get_all_records()
df = pd.DataFrame(data)

your_email = os.getenv("EMAIL")
your_password = os.getenv("PASS")

smtp_server = "smtp.gmail.com"
smtp_port = 587

server = smtplib.SMTP(smtp_server, smtp_port)
server.starttls()
server.login(your_email, your_password)

def generate_text(company, model="gpt-4o-mini", max_tokens=300):
    messages = [{"role": "system", "content": "You are a member of a tech startup called the Neo Developer League and are explaining to a company why your company's values align with theirs and be specific. The general idea of Neo Dev is : Neo Developer League is a student-led organization that hosts competitive events created to inspire high school students to pursue engineering and build connections in a fun and competitive way. Also limit answer to ONE paragraph and say it like you just finished explaining the company"}]
    messages.append({"role": "user", "content": f'Tell me why your company aligns with the values at {company}'})

    response = openai.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
        n=1,
        stop=None,
        stream=False,
        frequency_penalty=2.0
    )
    return response.choices[0].message.content

def generate_email(company_name, first_name):
    body = f"""
{first_name},

Hello! I'm Andy Duong, a founder at the NeoDev League, and we're reaching out to collaborate! We’re excited to connect with you as we prepare to launch our first competitive engineering event for high school students this October. We’re expecting 150-200 participants for this one-day event, where teams of students will collaborate on projects to present to a panel of judges. Our organization is focused on sparking collaboration and innovation in high schoolers. Events will allow teams of 8-10 students from various schools in the region to collaborate over an 8 hour work period to create a project and present it to a panel of judges.  

{generate_text(company=company_name)}

We’d love to discuss this further and explore how we can collaborate. Please feel free to reach out with any questions.

Thank you for your time and consideration.

Best regards,
Andy Duong
Finance Lead
neodevleague@gmail.com
    """
    return body

for index, row in df.iterrows():
    status = row['Status']
    if status != "Selected":
        continue
    company_name = row['Company Name']
    first_name = row['First Name']

    if not (isinstance(first_name, str)):
        first_name = "To Whom It May Concern"
    elif first_name.strip()=='':
        first_name = "To Whom It May Concern"
    else:
        first_name = "Dear, " + first_name

    recipient_email = row['Email']
    subject = f"Why {company_name} Should Sponsor Us"
    body = generate_email(company_name=company_name, first_name=first_name)

    while True:
        print(f"\nSubject: {subject}")
        print(f"To: {recipient_email}")
        print(f"Body:\n{body}")

        send_email = input("Do you want to send this email? (y/n/skip/hw): ").strip().lower()
        
        if send_email == 'y':
            send_email = input("Are you sure? (y/n): ").strip().lower()
            if send_email =='y':
                msg = MIMEMultipart()
                msg['From'] = your_email
                msg['To'] = recipient_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                
                file_path = 'NeoDev_Sponsorship_Package.pdf'

                try:
                    with open(file_path, 'rb') as file:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(file.read())
                        encoders.encode_base64(part)
                        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(file_path)}')
                        msg.attach(part)
                except FileNotFoundError:
                    print(f"File {file_path} not found. Skipping attachment.")

                server.sendmail(your_email, recipient_email, msg.as_string())
                df.at[index, 'Status'] = 'Review'
                print(f"Email sent to {first_name} at {company_name}")

                cell = sheet.find(row['Company Name'])
                sheet.update_cell(cell.row, df.columns.get_loc('Status') + 1, 'Review')
                break
            else:
                pass
        elif send_email == 'n':
            print("Here's Another")
            body=generate_email(company_name=company_name, first_name=first_name)
        elif send_email == 'skip':
            break
        elif send_email =='hw':
            df.at[index, 'Status'] = 'Handwrite'
            cell = sheet.find(row['Company Name'])
            sheet.update_cell(cell.row, df.columns.get_loc('Status') + 1, 'Handwrite')
            break
        else:
            print("Invalid input. Please enter 'y' to send or 'n' to create another email.")

df.to_csv('sponsors.csv', index=False)
server.quit()
