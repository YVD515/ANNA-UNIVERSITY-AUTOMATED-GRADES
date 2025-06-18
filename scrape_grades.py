from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import time

# --- Setup Google Sheets API ---
def connect_to_sheet(sheet_name="Anna University Grades"):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name)

# --- Setup Selenium ---
driver = webdriver.Chrome()
driver.get("https://acoe.annauniv.edu/sems/student/login")

print("🔐 Please log in manually in the browser (solve CAPTCHA).")
input("➡️ Press Enter here after you've logged in...")

# Navigate to grades page
driver.get("https://acoe.annauniv.edu/sems/student/mark")

# Wait for the dropdown to load
WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "sessions")))
session_dropdown = Select(driver.find_element(By.ID, "sessions"))

# Connect to the Google Sheet
sheet = connect_to_sheet()
sheet_counter = 1  # For naming tabs session1, session2, ...

# Loop through each session
for i in range(len(session_dropdown.options)):
    option = session_dropdown.options[i]
    session_dropdown.select_by_index(i)
    time.sleep(3)  # Allow time for page to load

    # Extract session tab name
    session_tab_name = f"session{sheet_counter}"
    print(f"\n📄 Working on: {session_tab_name}")

    # Scrape grades
    try:
        table = driver.find_element(By.ID, "student_subject")
        rows = table.find_elements(By.TAG_NAME, "tr")
        gpa_row = rows[-1]
        gpa_text = gpa_row.find_element(By.TAG_NAME, "td").text.strip()

        # Prepare headers
        headers = ["S.No.", "Course Code", "Course Name", "Att. 1", "Att. 2", "Att. 3", "Att.(%)",
                   "Assess. 1", "Assess. 2", "Assess. 3", "I. Assess", "Grade"]

        # Try to access or create the worksheet
        try:
            worksheet = sheet.worksheet(session_tab_name)
            worksheet.clear()
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sheet.add_worksheet(title=session_tab_name, rows="100", cols="20")

        # Write headers
        worksheet.append_row(headers)

        # Write each row of grades
        for row in rows[1:-1]:  # Skip header and GPA row
            cols = row.find_elements(By.TAG_NAME, "td")
            data = [col.text.strip() for col in cols]
            worksheet.append_row(data)

        # Add GPA at the bottom
        worksheet.append_row(["", "", "", "", "", "", "", "", "", "", "", gpa_text])
        print(f"✅ {session_tab_name} updated successfully.")

    except Exception as e:
        print(f"❌ Failed to scrape session {sheet_counter}: {str(e)}")

    sheet_counter += 1

print("\n🎉 All sessions scraped and uploaded to Google Sheets!")
# driver.quit()  # Uncomment this if you want to close the browser after execution
