import os
import sys
import time
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = "1x2tcR4WyHXj_cvHjpPFWNsrtelkimUXJXNTw9hPbVeo"
SERVICE_ACCOUNT_FILE = "/media/vpsg16gb/HaRiDisk/Youtube/historysnoozevox/00.System/01.Docker/service_account.json"

def get_sheets_service():
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"[Error] Service account file {SERVICE_ACCOUNT_FILE} not found.")
        sys.exit(1)
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return build("sheets", "v4", credentials=creds)

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    return {
        "red": int(hex_str[0:2], 16) / 255.0,
        "green": int(hex_str[2:4], 16) / 255.0,
        "blue": int(hex_str[4:6], 16) / 255.0
    }

def format_pipeline_and_remove_control_center():
    service = get_sheets_service()
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    sheets = {s["properties"]["title"]: s["properties"]["sheetId"] for s in spreadsheet.get("sheets", [])}

    print("Existing Sheets:", sheets)

    # Delete Control_Center sheet if it exists
    if "Control_Center" in sheets:
        control_sheet_id = sheets["Control_Center"]
        try:
            service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={"requests": [{"deleteSheet": {"sheetId": control_sheet_id}}]}
            ).execute()
            print("✅ Successfully deleted redundant 'Control_Center' tab from Google Sheet!")
        except Exception as e:
            print(f"⚠️ Notice deleting Control_Center sheet: {e}")

    # Format Pipeline Sheet (A:K)
    pipeline_sheet_id = sheets.get("Pipeline")
    if not pipeline_sheet_id:
        print("[Error] Pipeline sheet not found.")
        return

    res = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range="Pipeline!A:Z").execute()
    rows = res.get("values", [])
    
    headers_11 = [
        "Idea_ID", "Historical_Figure", "YouTube_Title", "Status",
        "GDrive", "Outline", "Script", "Voiceover",
        "Image", "Video", "Updated_At"
    ]

    updated_rows = [headers_11]
    if len(rows) > 1:
        for idx, row in enumerate(rows[1:], 1):
            if not row or not any(row):
                continue
            idea_id = row[0] if len(row) > 0 else ""
            char_name = row[1] if len(row) > 1 else ""
            yt_title = row[2] if len(row) > 2 else ""
            status = row[3] if len(row) > 3 else "Proposed"
            gdrive_url = row[4] if len(row) > 4 else ""
            outline_link = row[5] if len(row) > 5 else ""
            script_link = row[6] if len(row) > 6 else ""
            voice_link = row[7] if len(row) > 7 else ""
            image_link = row[8] if len(row) > 8 else ""
            video_link = row[9] if len(row) > 9 else ""
            updated_at = row[10] if len(row) > 10 else time.strftime("%Y-%m-%d %H:%M:%S")

            new_row = [
                idea_id, char_name, yt_title, status,
                gdrive_url, outline_link, script_link, voice_link,
                image_link, video_link, updated_at
            ]
            updated_rows.append(new_row)

    # Write 11 columns
    service.spreadsheets().values().clear(spreadsheetId=SPREADSHEET_ID, range="Pipeline!A1:Z500").execute()
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range="Pipeline!A1:K" + str(len(updated_rows)),
        valueInputOption="USER_ENTERED",
        body={"values": updated_rows}
    ).execute()
    print(f"✅ Updated Pipeline sheet to 11-column schema ({len(updated_rows)} rows).")

    # Apply Pipeline Styling
    reqs = []
    # Header Formatting
    reqs.append({
        "repeatCell": {
            "range": {"sheetId": pipeline_sheet_id, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 0, "endColumnIndex": 11},
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": hex_to_rgb("#1B365D"),
                    "textFormat": {"foregroundColor": hex_to_rgb("#FFFFFF"), "bold": True, "fontSize": 11},
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE"
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment)"
        }
    })

    # Freeze Header Row
    reqs.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": pipeline_sheet_id,
                "gridProperties": {"frozenRowCount": 1}
            },
            "fields": "gridProperties.frozenRowCount"
        }
    })

    # Column Widths (A:K)
    col_widths = [110, 180, 320, 150, 200, 200, 200, 200, 200, 250, 160]
    for c_idx, width in enumerate(col_widths):
        reqs.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": pipeline_sheet_id,
                    "dimension": "COLUMNS",
                    "startIndex": c_idx,
                    "endIndex": c_idx + 1
                },
                "properties": {"pixelSize": width},
                "fields": "pixelSize"
            }
        })

    # Data Validation Dropdown for Status
    status_values = [
        "Proposed", "Pending", "GDrive", "Outline",
        "Scripting", "Script", "Beats", "Voicing",
        "Voiceover", "Ready", "Producing", "Done"
    ]
    reqs.append({
        "setDataValidation": {
            "range": {"sheetId": pipeline_sheet_id, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 3, "endColumnIndex": 4},
            "rule": {
                "condition": {"type": "ONE_OF_LIST", "values": [{"userEnteredValue": v} for v in status_values]},
                "showCustomUi": True
            }
        }
    })

    # Conditional Formatting Rules for Status & Image Column
    styles_map = [
        (["Done", "Voiceover", "Script", "Beats", "Outline", "GDrive"], "#D4EDDA", "#155724"),
        (["Failed", "Rejected"], "#F8D7DA", "#721C24"),
        (["Producing", "Voicing", "Imaging", "Scripting", "Pending"], "#FFF3CD", "#856404"),
        (["Proposed", "Ready"], "#E2E3E5", "#383D41")
    ]

    for val_list, bg_color, text_color in styles_map:
        for val in val_list:
            reqs.append({
                "addConditionalFormatRule": {
                    "rule": {
                        "ranges": [
                            {"sheetId": pipeline_sheet_id, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 3, "endColumnIndex": 4},
                            {"sheetId": pipeline_sheet_id, "startRowIndex": 1, "endRowIndex": 500, "startColumnIndex": 8, "endColumnIndex": 9}
                        ],
                        "booleanRule": {
                            "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": val}]},
                            "format": {
                                "backgroundColor": hex_to_rgb(bg_color),
                                "textFormat": {"foregroundColor": hex_to_rgb(text_color), "bold": True}
                            }
                        }
                    },
                    "index": 0
                }
            })

    service.spreadsheets().batchUpdate(
        spreadsheetId=SPREADSHEET_ID,
        body={"requests": reqs}
    ).execute()

    print("🎉 Successfully formatted Pipeline schema (A:K)!")

if __name__ == "__main__":
    format_pipeline_and_remove_control_center()
