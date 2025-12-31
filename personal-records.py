from datetime import date, datetime
from garminconnect import Garmin
from notion_client import Client
import os

def get_icon_for_record(activity_name):
    icon_map = {
        "1K": "🥇",
        "1mi": "⚡",
        "5K": "👟",
        "10K": "⭐",
        "Half Marathon": "🥈",
        "Marathon": "🏆",
        "Longest Run": "🏃",
        "Longest Ride": "🚴",
        "Total Ascent": "🚵",
        "Max Avg Power (20 min)": "🔋",
        "Most Steps in a Day": "👣",
        "Most Steps in a Week": "🚶",
        "Most Steps in a Month": "📅",
        "Longest Goal Streak": "✔️",
        "Other": "🏅"
    }
    return icon_map.get(activity_name, "🏅")

def get_cover_for_record(activity_name):
    cover_map = {
        "1K": "https://images.unsplash.com/photo-1526676537331-7747bf8278fc?q=80&w=2000",
        "1mi": "https://images.unsplash.com/photo-1638183395699-2c0db5b6afbb?q=80&w=2000",
        "5K": "https://images.unsplash.com/photo-1571008887538-b36bb32f4571?q=80&w=2000",
        "10K": "https://images.unsplash.com/photo-1529339944280-1a37d3d6fa8c?q=80&w=2000",
        "Half Marathon": "https://images.unsplash.com/photo-1452626038306-9aae5e071dd3?q=80&w=2000",
        "Marathon": "https://images.unsplash.com/photo-1459313191173-ef21677ed9b7?q=80&w=2000",
        "Longest Run": "https://images.unsplash.com/photo-1532383282788-19b341e3c422?q=80&w=2000",
        "Longest Ride": "https://images.unsplash.com/photo-1471506480208-91b3a4cc78be?q=80&w=2000",
        "Max Avg Power (20 min)": "https://images.unsplash.com/photo-1591741535018-d042766c62eb?q=80&w=2000",
        "Most Steps in a Day": "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?q=80&w=2000",
        "Most Steps in a Week": "https://images.unsplash.com/photo-1602174865963-9159ed37e8f1?q=80&w=2000",
        "Most Steps in a Month": "https://images.unsplash.com/photo-1580058572462-98e2c0e0e2f0?q=80&w=2000",
        "Longest Goal Streak": "https://images.unsplash.com/photo-1477332552946-cfb384aeaf1c?q=80&w=2000"
    }
    # Fallback to a default running image if name not found
    return cover_map.get(activity_name, "https://images.unsplash.com/photo-1471506480208-91b3a4cc78be?q=80&w=2000") 

def format_activity_type(activity_type):
    if activity_type is None:
        return "Walking"
    return activity_type.replace('_', ' ').title()

def format_garmin_value(value, activity_type, typeId):
    # 1K (TypeId 1)
    if typeId == 1:
        total_seconds = round(value)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted_value = f"{minutes}:{seconds:02d}"
        return formatted_value, f"{formatted_value} /km"

    # 1 Mile (TypeId 2)
    if typeId == 2:
        total_seconds = round(value)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted_value = f"{minutes}:{seconds:02d}"
        total_pseconds = total_seconds / 1.60934
        pminutes = int(total_pseconds // 60)
        pseconds = int(total_pseconds % 60)
        return formatted_value, f"{pminutes}:{pseconds:02d} /km"

    # 5K (TypeId 3)
    if typeId == 3:
        total_seconds = round(value)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted_value = f"{minutes}:{seconds:02d}"
        pminutes = (total_seconds // 5) // 60
        pseconds = (total_seconds // 5) % 60
        return formatted_value, f"{pminutes}:{pseconds:02d} /km"

    # 10K, Half Marathon, Marathon (TypeIds 4, 5, 6)
    if typeId in [4, 5, 6]:
        total_seconds = round(value)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        formatted_value = f"{hours}:{minutes:02d}:{seconds:02d}"
        dist_map = {4: 10, 5: 21.0975, 6: 42.195}
        dist = dist_map.get(typeId)
        total_pseconds = total_seconds / dist
        pminutes = int(total_pseconds // 60)
        pseconds = int(total_pseconds % 60)
        return formatted_value, f"{pminutes}:{pseconds:02d} /km"

    # Longest Run, Ride (TypeIds 7, 8)
    if typeId in [7, 8]:
        return f"{value / 1000:.2f} km", ""

    # Total Ascent (TypeId 9)
    if typeId == 9:
        return f"{int(value):,} m", ""

    # Max Avg Power (TypeId 10)
    if typeId == 10:
        return f"{round(value)} W", ""

    # Steps (TypeIds 12, 13, 14)
    if typeId in [12, 13, 14]:
        return f"{round(value):,}", ""

    # Streak (TypeId 15)
    if typeId == 15:
        return f"{round(value)} days", ""

    return str(value), ""

def replace_activity_name_by_typeId(typeId):
    typeId_name_map = {
        1: "1K", 2: "1mi", 3: "5K", 4: "10K",
        5: "Half Marathon", 6: "Marathon",
        7: "Longest Run", 8: "Longest Ride", 9: "Total Ascent",
        10: "Max Avg Power (20 min)", 12: "Most Steps in a Day",
        13: "Most Steps in a Week", 14: "Most Steps in a Month",
        15: "Longest Goal Streak"
    }
    return typeId_name_map.get(typeId, "Unnamed Activity")

def get_existing_record(client, database_id, activity_name):
    query = client.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Record", "title": {"equals": activity_name}},
                {"property": "PR", "checkbox": {"equals": True}}
            ]
        }
    )
    return query['results'][0] if query['results'] else None

def get_record_by_date_and_name(client, database_id, activity_date, activity_name):
    if not activity_date:
        return None
    query = client.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Record", "title": {"equals": activity_name}},
                {"property": "Date", "date": {"equals": activity_date}}
            ]
        }
    )
    return query['results'][0] if query['results'] else None

def update_record(client, page_id, activity_date, value, pace, activity_name, is_pr=True):
    properties = {
        "Date": {"date": {"start": activity_date}},
        "PR": {"checkbox": is_pr}
    }
    if value: properties["Value"] = {"rich_text": [{"text": {"content": value}}]}
    if pace: properties["Pace"] = {"rich_text": [{"text": {"content": pace}}]}
    try:
        client.pages.update(
            page_id=page_id,
            properties=properties,
            icon={"emoji": get_icon_for_record(activity_name)},
            cover={"type": "external", "external": {"url": get_cover_for_record(activity_name)}}
        )
    except Exception as e:
        print(f"Error updating record: {e}")

def write_new_record(client, database_id, activity_date, activity_type, activity_name, typeId, value, pace):
    properties = {
        "Date": {"date": {"start": activity_date}},
        "Activity Type": {"select": {"name": activity_type}},
        "Record": {"title": [{"text": {"content": activity_name}}]},
        "typeId": {"number": typeId},
        "PR": {"checkbox": True}
    }
    if value: properties["Value"] = {"rich_text": [{"text": {"content": value}}]}
    if pace: properties["Pace"] = {"rich_text": [{"text": {"content": pace}}]}
    try:
        client.pages.create(
            parent={"database_id": database_id},
            properties=properties,
            icon={"emoji": get_icon_for_record(activity_name)},
            cover={"type": "external", "external": {"url": get_cover_for_record(activity_name)}}
        )
    except Exception as e:
        print(f"Error writing new record: {e}")

def main():
    garmin_email = os.getenv("GARMIN_EMAIL")
    garmin_password = os.getenv("GARMIN_PASSWORD")
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_PR_DB_ID")

    garmin = Garmin(garmin_email, garmin_password)
    garmin.login()
    client = Client(auth=notion_token)

    records = garmin.get_personal_record()
    filtered_records = [record for record in records if record.get('typeId') != 16]

    for record in filtered_records:
        activity_date = record.get('prStartTimeGmtFormatted')
        
        # FIX: Skip records with no date to prevent 400 error
        if not activity_date:
            print(f"Skipping record ID {record.get('typeId')} - Missing Date")
            continue

        activity_type = format_activity_type(record.get('activityType'))
        activity_name = replace_activity_name_by_typeId(record.get('typeId'))
        typeId = record.get('typeId', 0)
        value, pace = format_garmin_value(record.get('value', 0), activity_type, typeId)

        existing_pr_record = get_existing_record(client, database_id, activity_name)
        existing_date_record = get_record_by_date_and_name(client, database_id, activity_date, activity_name)

        if existing_date_record:
            update_record(client, existing_date_record['id'], activity_date, value, pace, activity_name, True)
            print(f"No update needed/Updated: {activity_type} - {activity_name}")
        elif existing_pr_record:
            try:
                date_prop = existing_pr_record['properties']['Date']
                if date_prop and date_prop.get('date') and date_prop['date'].get('start'):
                    existing_date = date_prop['date']['start']
                    if activity_date > existing_date:
                        update_record(client, existing_pr_record['id'], existing_date, None, None, activity_name, False)
                        write_new_record(client, database_id, activity_date, activity_type, activity_name, typeId, value, pace)
                        print(f"Created new PR: {activity_type} - {activity_name}")
                    else:
                        print(f"No update needed: {activity_type} - {activity_name}")
                else:
                    update_record(client, existing_pr_record['id'], activity_date, value, pace, activity_name, True)
            except:
                write_new_record(client, database_id, activity_date, activity_type, activity_name, typeId, value, pace)
        else:
            write_new_record(client, database_id, activity_date, activity_type, activity_name, typeId, value, pace)
            print(f"Written new record: {activity_type} - {activity_name}")

if __name__ == '__main__':
    main()
