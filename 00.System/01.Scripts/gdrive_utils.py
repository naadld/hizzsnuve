import io
import json
import os
import time
import mimetypes
from google.oauth2.service_account import Credentials as SACredentials
from google.oauth2.credentials import Credentials as UserCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

DEFAULT_PARENT_FOLDER_ID = "1UGkrUFQ62ghj1Lquy1HVsKIYR9nO60zf"

def get_gdrive_service():
    """
    1. Prefer User OAuth Refresh Token (Bypasses Service Account 0MB Storage Quota).
    2. Fallback to Service Account JSON.
    """
    refresh_token = os.environ.get("GDRIVE_REFRESH_TOKEN")
    client_id = os.environ.get("GDRIVE_CLIENT_ID")
    client_secret = os.environ.get("GDRIVE_CLIENT_SECRET")
    quota_proj = os.environ.get("GDRIVE_QUOTA_PROJECT_ID")

    if refresh_token and client_id and client_secret:
        try:
            from google.auth.transport.requests import Request
            creds = UserCredentials(
                None,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret,
                quota_project_id=quota_proj
            )
            creds.refresh(Request())
            print("🔑 Authenticated GDrive using User OAuth Credentials")
            return build("drive", "v3", credentials=creds)
        except Exception as e:
            print(f"⚠️ User OAuth Refresh Failed: {e}")

    # Fallback to Service Account
    raw_env = os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON")
    sa_path = os.environ.get("GDRIVE_SERVICE_ACCOUNT_PATH", "/media/vpsg16gb/HaRiDisk/Youtube/historysnoozevox/00.System/01.Docker/service_account.json")
    if not os.path.exists(sa_path):
        sa_path = "/tmp/service_account.json"

    info = None
    if raw_env and len(raw_env.strip()) > 50:
        try:
            info = json.loads(raw_env)
        except Exception:
            pass

    if not info and os.path.exists(sa_path):
        try:
            with open(sa_path, "r", encoding="utf-8") as f:
                info = json.load(f)
        except Exception:
            pass

    if not info:
        print("⚠️ No valid Google Drive credentials found.")
        return None

    try:
        creds = SACredentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        print(f"⚠️ Service Account Auth Error: {e}")
        return None

def get_parent_id(provided_id=None):
    if provided_id:
        return provided_id
    env_id = os.environ.get("GDRIVE_PARENT_FOLDER_ID")
    if env_id and len(env_id.strip()) > 5:
        return env_id.strip()
    return DEFAULT_PARENT_FOLDER_ID

def find_file_or_folder(service, name, parent_id=None, mime_type=None):
    if not service:
        return None
    parent_id = get_parent_id(parent_id)
    query = f"name = '{name}' and trashed = false"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    if mime_type:
        query += f" and mimeType = '{mime_type}'"
    try:
        res = service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = res.get("files", [])
        return files[0]["id"] if files else None
    except Exception as e:
        print(f"⚠️ GDrive list error: {e}")
        return None

def find_or_create_folder(service, folder_name, parent_id=None):
    if not service:
        return None
    parent_id = get_parent_id(parent_id)
    folder_id = find_file_or_folder(service, folder_name, parent_id=parent_id, mime_type="application/vnd.google-apps.folder")
    if folder_id:
        return folder_id

    metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    if parent_id:
        metadata["parents"] = [parent_id]
    try:
        f = service.files().create(body=metadata, fields="id", supportsAllDrives=True).execute()
        fid = f.get("id")
        try:
            service.permissions().create(
                fileId=fid,
                body={"type": "anyone", "role": "writer"},
                supportsAllDrives=True
            ).execute()
        except Exception:
            pass
        return fid
    except Exception as e:
        print(f"⚠️ GDrive create folder error: {e}")
        return None

def ensure_project_tree(service, project_name):
    """
    Pre-initializes the standardized GDrive project tree:
    <Root> / <project_name> /
      ├── 01.Preproduction
      ├── 02.Media Generation / (audio, keyframes)
      └── 03.Final Production
    """
    if not service:
        return {}
    parent_env_id = get_parent_id()
    proj_id = find_or_create_folder(service, project_name, parent_id=parent_env_id)
    
    pre_id = find_or_create_folder(service, "01.Preproduction", parent_id=proj_id)
    
    media_id = find_or_create_folder(service, "02.Media Generation", parent_id=proj_id)
    audio_id = find_or_create_folder(service, "audio", parent_id=media_id)
    keyframes_id = find_or_create_folder(service, "keyframes", parent_id=media_id)
    combined_id = find_or_create_folder(service, "combined", parent_id=media_id)
    
    post_id = find_or_create_folder(service, "03.Final Production", parent_id=proj_id)
    
    return {
        "project_id": proj_id,
        "preproduction_id": pre_id,
        "media_generation_id": media_id,
        "audio_id": audio_id,
        "keyframes_id": keyframes_id,
        "combined_id": combined_id,
        "final_production_id": post_id,
        "final_id": post_id
    }

def upload_file(service, local_path, parent_id=None, file_name=None, mime_type=None):
    if not service or not os.path.exists(local_path):
        return None
    parent_id = get_parent_id(parent_id)
    if not file_name:
        file_name = os.path.basename(local_path)
    if not mime_type:
        ext = os.path.splitext(local_path)[1].lower()
        mapping = {
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
            ".json": "application/json",
            ".txt": "text/plain",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".mp4": "video/mp4"
        }
        mime_type = mapping.get(ext, "application/octet-stream")

    existing_id = find_file_or_folder(service, file_name, parent_id=parent_id)
    file_size = os.path.getsize(local_path)
    is_resumable = file_size > 5 * 1024 * 1024

    for attempt in range(1, 4):
        try:
            media = MediaFileUpload(local_path, mimetype=mime_type, resumable=is_resumable)
            if existing_id:
                f = service.files().update(
                    fileId=existing_id,
                    media_body=media,
                    fields="id",
                    supportsAllDrives=True
                ).execute()
                print(f"  ☁️ [GDrive Updated] {file_name} -> ID: {existing_id}")
                return existing_id
            else:
                metadata = {"name": file_name}
                if parent_id:
                    metadata["parents"] = [parent_id]
                f = service.files().create(
                    body=metadata,
                    media_body=media,
                    fields="id",
                    supportsAllDrives=True
                ).execute()
                fid = f.get("id")
                print(f"  ☁️ [GDrive Uploaded] {file_name} -> ID: {fid}")
                return fid
        except Exception as e:
            if attempt == 3:
                print(f"⚠️ GDrive Upload Warning ({file_name}): {e}")
                return None
            time.sleep(2)

def download_file(service, file_id, dest_path):
    if not service or not file_id:
        return False
    try:
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
        fh = io.FileIO(dest_path, "wb")
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        print(f"  ⬇️ [GDrive Downloaded] File ID {file_id} -> {dest_path}")
        return True
    except Exception as e:
        print(f"⚠️ GDrive Download Error for {file_id}: {e}")
        return False

def download_folder_files(service, folder_id, dest_dir):
    if not service or not folder_id:
        return
    os.makedirs(dest_dir, exist_ok=True)
    try:
        res = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="files(id, name, mimeType)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        files = res.get("files", [])
        for f in files:
            if f["mimeType"] == "application/vnd.google-apps.folder":
                sub_dir = os.path.join(dest_dir, f["name"])
                download_folder_files(service, f["id"], sub_dir)
            else:
                local_path = os.path.join(dest_dir, f["name"])
                if not os.path.exists(local_path):
                    download_file(service, f["id"], local_path)
    except Exception as e:
        print(f"⚠️ GDrive download folder error: {e}")

def sync_project_to_gdrive(character_name, project_dir):
    """
    Uploads all local project files to GDrive storage.
    """
    service = get_gdrive_service()
    if not service:
        print("⚠️ Skipped GDrive upload: No GDrive service available.")
        return False

    print(f"\n☁️ Syncing local project '{character_name}' to Google Drive Storage...")
    tree = ensure_project_tree(service, character_name)

    # 1. Sync 01.Preproduction
    preprod_dir = os.path.join(project_dir, "01.Preproduction")
    if os.path.exists(preprod_dir):
        for f in os.listdir(preprod_dir):
            upload_file(service, os.path.join(preprod_dir, f), parent_id=tree["preproduction_id"])

    # 2. Sync 02.Media Generation / audio
    audio_dir = os.path.join(project_dir, "02.Media Generation", "audio")
    if os.path.exists(audio_dir):
        for f in os.listdir(audio_dir):
            upload_file(service, os.path.join(audio_dir, f), parent_id=tree["audio_id"])

    # 3. Sync 02.Media Generation / keyframes
    keyframes_dir = os.path.join(project_dir, "02.Media Generation", "keyframes")
    if os.path.exists(keyframes_dir):
        for f in os.listdir(keyframes_dir):
            upload_file(service, os.path.join(keyframes_dir, f), parent_id=tree["keyframes_id"])

    # 4. Sync 03.Final Production
    final_dir = os.path.join(project_dir, "03.Final Production")
    if os.path.exists(final_dir):
        for f in os.listdir(final_dir):
            if f.endswith(".mp4"):
                upload_file(service, os.path.join(final_dir, f), parent_id=tree["final_production_id"])

    print(f"🎉 Google Drive Sync Completed for '{character_name}'!")
    return True

def sync_project_from_gdrive(character_name, project_dir):
    """
    Downloads project assets from GDrive storage to local working directory.
    """
    service = get_gdrive_service()
    if not service:
        print("⚠️ Skipped GDrive download: No GDrive service available.")
        return False

    print(f"\n⬇️ Pulling project '{character_name}' from Google Drive Storage...")
    tree = ensure_project_tree(service, character_name)

    # Download Preproduction
    download_folder_files(service, tree["preproduction_id"], os.path.join(project_dir, "01.Preproduction"))
    # Download Audio
    download_folder_files(service, tree["audio_id"], os.path.join(project_dir, "02.Media Generation", "audio"))
    # Download Keyframes
    download_folder_files(service, tree["keyframes_id"], os.path.join(project_dir, "02.Media Generation", "keyframes"))

    print(f"🎉 Project '{character_name}' pulled from GDrive successfully!")
    return True
