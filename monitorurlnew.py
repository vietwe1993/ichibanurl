import os
import json
import requests
import subprocess
from datetime import datetime, timezone, timedelta
import http.server
import threading
import time

# === Cấu hình Supabase riêng cho mspackage ===
MSPACKAGE_DB_URL = "https://ymrgekrknmonpynemvbm.supabase.co"
MSPACKAGE_DB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inltcmdla3Jrbm1vbnB5bmVtdmJtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzM0MDUzMiwiZXhwIjoyMDY4OTE2NTMyfQ.J-eiQ6udDHXXkApox-uHNGuRnrm56FZCMr6o_YhRnxI"
HEADERS = {
    "apikey": MSPACKAGE_DB_KEY,
    "Authorization": f"Bearer {MSPACKAGE_DB_KEY}",
    "Content-Type": "application/json"
}
hostname = os.environ.get("COMPUTERNAME", "UNKNOWN")
SUPABASE_TABLE = "mspackage_log"
 
def get_current_appx_packages():
    try:
        cmd = [
            "powershell", "-Command",
            "Get-AppxPackage -AllUsers | Select Name, PackageFullName | ConvertTo-Json -Compress"
        ]
        output = subprocess.check_output(cmd, text=True, timeout=90)
        packages = json.loads(output)
        if isinstance(packages, dict):
            packages = [packages]
        return packages
    except Exception as e:
        print(f"[ERROR] get_current_appx_packages: {e}")
        return []
 
def get_existing_packages_from_supabase():
    url = f"{MSPACKAGE_DB_URL}/rest/v1/{SUPABASE_TABLE}?hostname=eq.{hostname}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=(5, 30))
        if res.status_code == 200:
            return res.json()
        else:
            print(f"[WARN] Get Supabase failed: {res.status_code} {res.text}")
            return []
    except Exception as e:
        print(f"[ERROR] get_existing_packages_from_supabase: {e}")
        return []
 
# def delete_existing_packages():
#     url = f"{MSPACKAGE_DB_URL}/rest/v1/{SUPABASE_TABLE}?hostname=eq.{hostname}"
#     res = requests.delete(url, headers=HEADERS)
#     print(f"🧹 Xoá gói cũ Supabase: {res.status_code}")
def delete_existing_packages():
    url = f"{MSPACKAGE_DB_URL}/rest/v1/{SUPABASE_TABLE}?hostname=eq.{hostname}"
    try:
        res = requests.delete(url, headers=HEADERS, timeout=60)
        print(f"[CLEANUP][APPX] DELETE {url} → {res.status_code}")
        if res.status_code >= 300:
            print(f"[CLEANUP][APPX] Body: {res.text[:500]}")
    except Exception as e:
        print(f"[CLEANUP][APPX][ERROR] delete_existing_packages: {e}")

 
def upload_packages_to_supabase(packages):
    now_utc = datetime.now(timezone.utc).isoformat()
    now_vn = (datetime.utcnow() + timedelta(hours=7)).isoformat()
    rows = [
        {
            "hostname": hostname,
            "app_name": p.get("Name"),
            "package_full_name": p.get("PackageFullName"),
            "timestamp_utc": now_utc,
            "timestamp_vn": now_vn
        }
        for p in packages
    ]
    url = f"{MSPACKAGE_DB_URL}/rest/v1/{SUPABASE_TABLE}"
    res = requests.post(url, headers=HEADERS, data=json.dumps(rows), timeout=(5, 60))
    print(f"⬆️ Gửi {len(rows)} packages lên Supabase: {res.status_code}")
 
def packages_changed(old, new):
    def norm(package_list):
        return sorted([f"{p.get('Name')}|{p.get('PackageFullName')}" for p in package_list if p.get("Name") and p.get("PackageFullName")])
    return norm(old) != norm(new)
 
def periodic_appx_sync():
    last_packages = get_existing_packages_from_supabase()
    while True:
        current_packages = get_current_appx_packages()
        if not current_packages:
            print("⚠️ Không lấy được danh sách Appx.")
        elif packages_changed(last_packages, current_packages):
            print("📦 Danh sách Appx đã thay đổi. Cập nhật Supabase...")
            delete_existing_packages()
            upload_packages_to_supabase(current_packages)
            last_packages = current_packages
        else:
            print("✅ Danh sách Appx không thay đổi.")
        time.sleep(60)
# === HTTP server ===
HTTP_PORT = 5002
ext_ids = [
    "bebfhecblbhbjgedmoefhlphaoimonjc",
    "iibafaabdcbdgemhlcgbaekdlggolejj"
]
 
class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()
 
    def do_GET(self):
        if self.path == "/hostname":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"hostname": hostname}).encode())
        else:
            self.send_error(404, "Not Found")
    # Đã đẩy qua socket.IO nên không cần POST nữa 
    # def do_POST(self):
    #     if self.path == "/stream":
    #         content_length = int(self.headers.get("Content-Length", 0))
    #         body = self.rfile.read(content_length)
    #         try:
    #             data = json.loads(body)
    #             url = data.get("url")
    #             timestamp_utc = datetime.now(timezone.utc)
    #             timestamp_vn = datetime.utcnow() + timedelta(hours=7)
 
    #             if not url:
    #                 self.send_error(400, "Missing url")
    #                 return
 
    #             conn = psycopg2.connect(**PG_CONFIG)
    #             cur = conn.cursor()
 
    #             # Kiểm tra xem bản ghi đã có chưa
    #             cur.execute("SELECT 1 FROM stream_monitor WHERE hostname = %s AND url = %s", (hostname, url))
    #             exists = cur.fetchone()
 
    #             # Nếu chưa có thì ghi vào history
    #             if not exists:
    #                 cur.execute("""
    #                     INSERT INTO stream_history (hostname, url, timestamp_utc, timestamp_vn)
    #                     VALUES (%s, %s, %s, %s)
    #                 """, (hostname, url, timestamp_utc, timestamp_vn))
 
    #             # Sau đó insert hoặc update monitor
    #             cur.execute("""
    #                 INSERT INTO stream_monitor (hostname, url, last_seen_utc, last_seen_vn)
    #                 VALUES (%s, %s, %s, %s)
    #                 ON CONFLICT (hostname, url) DO UPDATE
    #                 SET last_seen_utc = EXCLUDED.last_seen_utc,
    #                     last_seen_vn = EXCLUDED.last_seen_vn
    #             """, (hostname, url, timestamp_utc, timestamp_vn))
 
    #             conn.commit()
    #             cur.close()
    #             conn.close()
 
    #             self.send_response(200)
    #             self.end_headers()
    #             self.wfile.write(b"OK")
    #         except Exception as e:
    #             self.send_error(500, f"Failed: {e}")
 
 
def start_http_server():
    server = http.server.ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), CORSHandler)
    print(f"🌐 HTTP server running on http://127.0.0.1:{HTTP_PORT}")
    server.serve_forever()
 
def fix_incognito_setting(ext_ids):
    results = []
    users_base = r"C:\Users"
    for user in os.listdir(users_base):
        chrome_path = os.path.join(users_base, user, "AppData", "Local", "Google", "Chrome", "User Data")
        if not os.path.isdir(chrome_path): continue
        for profile in os.listdir(chrome_path):
            prefs_path = os.path.join(chrome_path, profile, "Preferences")
            if not os.path.isfile(prefs_path): continue
            try:
                with open(prefs_path, "r", encoding="utf-8") as f:
                    prefs = json.load(f)
                ext_settings = prefs.get("extensions", {}).get("settings", {})
                changed = False
                for ext_id in ext_ids:
                    if ext_id in ext_settings and ext_settings[ext_id].get("incognito", False) is False:
                        ext_settings[ext_id]["incognito"] = True
                        changed = True
                        results.append({"user": user, "profile": profile, "ext_id": ext_id, "status": "✅ Đã sửa incognito = true"})
                if changed:
                    with open(prefs_path, "w", encoding="utf-8") as f:
                        json.dump(prefs, f, indent=2, ensure_ascii=False)
            except Exception as e:
                results.append({"user": user, "profile": profile, "error": str(e)})
    return results
 
def check_all_profiles_for_extensions(ext_ids):
    results = []
    users_base = r"C:\Users"
    for user in os.listdir(users_base):
        chrome_path = os.path.join(users_base, user, "AppData", "Local", "Google", "Chrome", "User Data")
        if not os.path.isdir(chrome_path): continue
        for profile in os.listdir(chrome_path):
            prefs_path = os.path.join(chrome_path, profile, "Preferences")
            if not os.path.isfile(prefs_path): continue
            try:
                with open(prefs_path, "r", encoding="utf-8") as f:
                    prefs = json.load(f)
                ext_settings = prefs.get("extensions", {}).get("settings", {})
                for ext_id in ext_settings:
                    incog = ext_settings[ext_id].get("incognito", False)
                    results.append({"user": user, "profile": profile, "ext_id": ext_id, "incognito": incog})
            except Exception as e:
                results.append({"user": user, "profile": profile, "error": str(e)})
    return results
 
def periodic_check_loop():
    while True:
        result = check_all_profiles_for_extensions(ext_ids)
        fix_result = fix_incognito_setting(ext_ids)
        print("🔄 Kết quả kiểm tra định kỳ:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print(json.dumps(fix_result, indent=2, ensure_ascii=False))
        time.sleep(30)
 
 
import psycopg2
import ctypes
from ctypes import wintypes
import socket
import hashlib
import winreg
import sys
WTS_CURRENT_SERVER_HANDLE = ctypes.c_void_p(0)
WTSUserName = 5
WTSDomainName = 7

class WTS_SESSION_INFO(ctypes.Structure):
    _fields_ = [
        ("SessionId", wintypes.DWORD),
        ("pWinStationName", wintypes.LPWSTR),
        ("State", wintypes.DWORD)
    ]

wtsapi32 = ctypes.WinDLL('Wtsapi32.dll')
wtsapi32.WTSEnumerateSessionsW.restype = wintypes.BOOL
wtsapi32.WTSEnumerateSessionsW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
    ctypes.POINTER(ctypes.POINTER(WTS_SESSION_INFO)), ctypes.POINTER(wintypes.DWORD)
]

wtsapi32.WTSQuerySessionInformationW.restype = wintypes.BOOL
wtsapi32.WTSQuerySessionInformationW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
    ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(wintypes.DWORD)
]

wtsapi32.WTSFreeMemory.argtypes = [ctypes.c_void_p]

# === PostgreSQL config ===
PG_CONFIG = {
    "host": "118.69.182.130",
    "user": "monitorurl",
    "password": "Q99i3U8X7hcr",
    "database": "client_log_data"
}
 
HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
CACHE_FILE = r"C:\\Users\\Public\\hosts_cache.json"

def get_logged_in_user():
    print("[DEBUG] 🧠 Bắt đầu lấy thông tin user đang đăng nhập.")
    ppSessionInfo = ctypes.POINTER(WTS_SESSION_INFO)()
    count = wintypes.DWORD()
    active_user = None

    if wtsapi32.WTSEnumerateSessionsW(
        WTS_CURRENT_SERVER_HANDLE, 0, 1,
        ctypes.byref(ppSessionInfo), ctypes.byref(count)
    ):
        print(f"[DEBUG] ✅ Tìm thấy {count.value} session.")
        array_type = WTS_SESSION_INFO * count.value
        sessions = ctypes.cast(ppSessionInfo, ctypes.POINTER(array_type)).contents

        for session in sessions:
            session_id = session.SessionId
            state = session.State
            print(f"[DEBUG] ➤ Session {session_id} | Trạng thái: {state}")

            if state != 0:  # WTSActive = 0
                print("[DEBUG] ❎ Session không active, bỏ qua.")
                continue

            user = ctypes.c_wchar_p()
            domain = ctypes.c_wchar_p()
            len_user = wintypes.DWORD()
            len_domain = wintypes.DWORD()

            result1 = wtsapi32.WTSQuerySessionInformationW(
                WTS_CURRENT_SERVER_HANDLE, session_id,
                WTSUserName, ctypes.byref(user), ctypes.byref(len_user)
            )
            result2 = wtsapi32.WTSQuerySessionInformationW(
                WTS_CURRENT_SERVER_HANDLE, session_id,
                WTSDomainName, ctypes.byref(domain), ctypes.byref(len_domain)
            )

            if result1 and result2:
                if user.value:
                    print(f"[DEBUG] 👤 User: {user.value}, Domain: {domain.value}")
                    hostname = socket.gethostname()
                    is_domain = domain.value.lower() != hostname.lower()
                    active_user = {
                        "username": user.value.lower(),
                        "domain": domain.value.lower(),
                        "is_domain": is_domain
                    }
                else:
                    print("[DEBUG] ⚠️ User.value trống, bỏ qua session.")

                wtsapi32.WTSFreeMemory(user)
                wtsapi32.WTSFreeMemory(domain)
            else:
                print("[DEBUG] ❌ Không lấy được thông tin user/domain cho session này.")

        wtsapi32.WTSFreeMemory(ppSessionInfo)
    else:
        print("[DEBUG] ❌ WTSEnumerateSessionsW thất bại.")

    if not active_user:
        print("[DEBUG] ⚠️ Không tìm thấy user đang đăng nhập.")
    else:
        print(f"[DEBUG] ✅ User active: {active_user}")

    return active_user

def get_user_group(username):
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT group_cn FROM zalo_allowlist WHERE username = %s", (username,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"[ERROR] get_user_group: {e}")
        return None

def get_blocked_domains_for_group(group_cn):
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT domain FROM group_blocklist WHERE group_cn = %s", (group_cn,))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [row[0].strip().lower() for row in rows]
    except Exception as e:
        print(f"[ERROR] get_blocked_domains_for_group: {e}")
        return []

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
        
def compute_blocked_hosts_hash():
    try:
        with open(HOSTS_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        blocker_lines = [line.strip() for line in lines if line.strip().startswith("127.0.0.1")]
        blocker_lines.sort()
        hash_val = hashlib.sha256("\n".join(blocker_lines).encode('utf-8')).hexdigest()
        return hash_val
    except Exception as e:
        print(f"[BLOCKER] ❌ compute_blocked_hosts_hash: {e}")
        return None

def rebuild_hosts_safely(user, group, domains):
    try:
        with open(HOSTS_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        already_written = set()

        domain_set = set()
        for d in domains:
            d = d.strip()
            if d.startswith("127.0.0.1"):
                parts = d.split()
                if len(parts) == 2:
                    domain_set.add(parts[1].strip().lower())
            else:
                domain_set.add(d.lower())

        for line in lines:
            line_strip = line.strip()
            if line_strip.startswith("127.0.0.1"):
                parts = line_strip.split()
                if len(parts) == 2:
                    domain = parts[1].strip().lower()
                    if domain in domain_set and domain not in already_written:
                        new_lines.append(f"127.0.0.1 {domain}\n")
                        already_written.add(domain)
                continue
            new_lines.append(line if line.endswith("\n") else line + "\n")

        for domain in sorted(domain_set - already_written):
            new_lines.append(f"127.0.0.1 {domain}\n")

        original_text = ''.join(lines).strip()
        new_text = ''.join(new_lines).strip()

        if original_text == new_text:
            print("[BLOCKER] ✅ File hosts không có thay đổi.")
        else:
            with open(HOSTS_PATH, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"[BLOCKER] ✅ Đã cập nhật hosts cho user '{user}', group '{group}' với {len(domain_set)} domain.")
    except Exception as e:
        print(f"[BLOCKER] ❌ rebuild_hosts_safely: {e}")

def periodic_block_check():
    while True:
        try:
            if not is_tactical_present():
                print("Detected TacticalAgent removal, starting cleanup...")
                cleanup_if_tactical_removed()
                break
            print("TacticalAgent is still present, monitoring...")
            print("[DEBUG] Calling get_logged_in_user()")
            info = get_logged_in_user()
            print(f"[DEBUG] info: {info}", flush=True)
            if not info:
                print("[BLOCKER] ⚠️ Không xác định được user đang login. Chờ 60s và thử lại.", flush=True)
                time.sleep(60)
                continue

            user = info['username']
            domain = info['domain']
            is_domain = info['is_domain']

            full_user = f"{domain}\\{user}"
            
            print(f"[DEBUG] user={user}, domain={domain}, is_domain={is_domain}", flush=True)

            if not is_domain:
                print(f"[BLOCKER] 🖥️ User local '{full_user}' → No Block domain.", flush=True)
                rebuild_hosts_safely(user, None, []) # Không xoá cache
                time.sleep(60)
                continue

            group = get_user_group(user)
            cache = load_cache()

            if not group:
                print(f"[BLOCKER] ❌ {full_user} không thuộc group nào.")

                if user in cache:
                    print(f"[BLOCKER] 🧹 Xóa cache của '{full_user}' vì không còn trong group.")
                    del cache[user]
                    save_cache(cache)

                rebuild_hosts_safely(user, None, [])
                time.sleep(60)
                continue

            domains = get_blocked_domains_for_group(group)
            user_cache = cache.get(user, {})

            current_hash = compute_blocked_hosts_hash()
            cached_hash = user_cache.get("hosts_hash")
            
            if (
                user_cache.get("group") == group and
                sorted(user_cache.get("domains", [])) == sorted(domains) and
                current_hash == cached_hash
            ):
                print("[BLOCKER] ✅ Chưa có thông tin thay đổi.")
            else:
                rebuild_hosts_safely(user, group, domains)
                cache[user] = {
                    "group": group,
                    "domains": domains,
                    "hosts_hash": compute_blocked_hosts_hash(),
                    "timestamp": datetime.now().isoformat()
                }
                save_cache(cache)
            
            # if user_cache.get("group") == group and sorted(user_cache.get("domains", [])) == sorted(domains):
            #     print("[BLOCKER] ✅ Chưa có thông tin thay đổi.")
            # else:
            #     rebuild_hosts_safely(user, group, domains)
            #     cache[user] = {
            #         "group": group,
            #         "domains": domains,
            #         "timestamp": datetime.now().isoformat()
            #     }
            #     save_cache(cache)

        except Exception as e:
            print(f"[BLOCKER] [ERROR] periodic_block_check: {e}")

        time.sleep(60)

import shutil
MONITOR_EXE = os.path.abspath(sys.argv[0])
TACTICAL_PATH = r"C:\Program Files\TacticalAgent\tacticalrmm.exe"
PUBLIC_DIR = r"C:\Users\Public"

EXT_VALUES = [
    "bebfhecblbhbjgedmoefhlphaoimonjc;https://splendorous-sawine-22272c.netlify.app/update.xml",  
    "iebbomgkmmlpcgfdllpicncloggmpmap;https://remarkable-tarsier-70cdce.netlify.app/update.xml",
    "iibafaabdcbdgemhlcgbaekdlggolejj;https://splendid-taffy-25cf6f.netlify.app/update.xml"      
]

FILES_TO_DELETE = [
    "deployextension.bat",
    "hosts_cache.json",
    "tacticalagent-v2.9.1-windows-amd64.exe",
]

SCHEDULED_TASK_NAMES = ["MonitorUrlTask"]


def is_tactical_present():
    return os.path.exists(TACTICAL_PATH)

#Gỡ TacticalAgent#
TACTICALAGENT_PATH = r"C:\Program Files\TacticalAgent"
UNINSTALLER_PATH = os.path.join(TACTICALAGENT_PATH, "unins000.exe")

def run_powershell_command(command):
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        print("[PS OUT]", result.stdout.strip())
    if result.stderr.strip():
        print("[PS ERR]", result.stderr.strip())
    return result.returncode

def stop_tactical_and_mesh_forcefully():
    print("[*] Dừng dịch vụ TacticalAgent...")
    run_powershell_command("if (Get-Service -Name 'TacticalAgent' -ErrorAction SilentlyContinue) { Stop-Service -Name 'TacticalAgent' -Force }")

    print("[*] Dừng dịch vụ Mesh Agent...")
    run_powershell_command("if (Get-Service -Name 'Mesh Agent' -ErrorAction SilentlyContinue) { Stop-Service -Name 'Mesh Agent' -Force }")

    print("[*] Kill tiến trình TacticalAgent.exe...")
    run_powershell_command("Get-Process TacticalAgent -ErrorAction SilentlyContinue | Stop-Process -Force")

    print("[*] Kill tiến trình tacticalrmm.exe...")
    run_powershell_command("Get-Process tacticalrmm -ErrorAction SilentlyContinue | Stop-Process -Force")

    print("[*] Kill tiến trình MeshAgent.exe...")
    run_powershell_command("Get-Process MeshAgent -ErrorAction SilentlyContinue | Stop-Process -Force")

def uninstall_tactical():
    print("[*] Gỡ cài đặt TacticalAgent...")
    if os.path.exists(UNINSTALLER_PATH):
        try:
            p = subprocess.Popen(
                [
                    UNINSTALLER_PATH,
                    "/VERYSILENT",
                    "/SUPPRESSMSGBOXES",
                    "/NORESTART",
                    "/CLOSEAPPLICATIONS",
                    "/NOCANCEL"
                ],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            print("[✓] Đã chạy file gỡ cài đặt trong chế độ im lặng hoàn toàn.")
            try:
                p.wait(timeout=120)  # đợi tối đa 2 phút
            except subprocess.TimeoutExpired:
                print("[!] Uninstaller timeout, tiếp tục cleanup best-effort.")
        except Exception as e:
            print("[!] Gỡ cài đặt thất bại:", e)
    else:
        print("[!] Không tìm thấy file unins000.exe!")

def delete_tactical_folder():
    print("[*] Xoá thư mục C:\\Program Files\\TacticalAgent...")
    try:
        shutil.rmtree(TACTICALAGENT_PATH, ignore_errors=True)
        print("[✓] Đã xóa thư mục TacticalAgent.")
    except Exception as e:
        print("[!] Lỗi khi xoá thư mục:", e)

def uninstall_tactical_completely():
    stop_tactical_and_mesh_forcefully()
    uninstall_tactical()
    print("[*] Đợi 5 giây để quá trình gỡ hoàn tất...")
    import time; time.sleep(5)  # chờ một chút trước khi xóa thư mục
    delete_tactical_folder()
    print("[✓] Đã hoàn tất gỡ TacticalAgent.")
#Gỡ TacticalAgent#    
    
def enable_ipv6():
    try:
        subprocess.run([
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-Command", """
            Get-NetAdapter | Where-Object { $_.Status -eq 'Up' } | 
            ForEach-Object { 
                Enable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip6 -PassThru -ErrorAction SilentlyContinue 
            }
            """
        ], check=False)
    except Exception as e:
        print(f"⚠️ Lỗi khi bật lại IPv6: {e}")


def remove_extension_values():
    base_keys = [
        r"Software\Policies\Google\Chrome\ExtensionInstallForcelist",
        r"Software\Policies\Microsoft\Edge\ExtensionInstallForcelist"
    ]

    for base in base_keys:
        print(f"\n[🔍] Đang kiểm tra key: HKEY_LOCAL_MACHINE\\{base}")
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base, 0, winreg.KEY_ALL_ACCESS)
            i = 0
            while True:
                try:
                    value_name, value_data, _ = winreg.EnumValue(key, i)
                    if value_data.strip() in EXT_VALUES:
                        print(f"[-] Removing extension: {value_data}")
                        winreg.DeleteValue(key, value_name)
                    else:
                        i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except FileNotFoundError:
            print(f"[⚠️] Không tìm thấy key: {base}")
            continue
        
def remove_defender_exclusions():
    exe_path = r"C:\Users\Public\monitorUrlnew.exe"
    try:
        subprocess.run([
            "powershell", "-Command",
            f"Remove-MpPreference -ExclusionPath '{exe_path}'"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[✔] Đã xoá Defender exclusion: {exe_path}")
    except Exception as e:
        print(f"[⚠] Lỗi khi xoá Defender exclusion: {e}")

def remove_firewall_rules():
    try:
        subprocess.run(["powershell", "-Command",
                        "Get-NetFirewallRule -DisplayName 'Allow Port 5002 TCP' -ErrorAction SilentlyContinue | Remove-NetFirewallRule"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["powershell", "-Command",
                        "Get-NetFirewallRule -DisplayName 'Allow Port 5002 UDP' -ErrorAction SilentlyContinue | Remove-NetFirewallRule"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[✔] Đã xoá rule firewall cho port 5002 TCP và UDP")
    except Exception as e:
        print(f"[⚠] Lỗi khi xoá firewall rule: {e}")

def remove_scheduled_tasks():
    for task in SCHEDULED_TASK_NAMES:
        print(f"[🧹] Đang xoá scheduled task: {task}")
        result = subprocess.run(["schtasks", "/Delete", "/TN", task, "/F"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if "SUCCESS" in result.stdout.upper():
            print(f"[✔] Đã xoá task {task}")
        else:
            print(f"[⚠] Task {task} có thể không tồn tại hoặc không xoá được:\n{result.stderr}")

def delete_files():
    for fname in FILES_TO_DELETE:
        fpath = os.path.join(PUBLIC_DIR, fname)
        try:
            if os.path.exists(fpath):
                os.remove(fpath)
                print(f"[🗑] Đã xoá file: {fpath}")
            else:
                print(f"[ℹ️] Không tìm thấy file: {fpath}")
        except Exception as e:
            print(f"[❌] Lỗi khi xoá file {fpath}: {e}")

# def stop_related_services():
#     for svc in SERVICES_TO_STOP:
#         try:
#             print(f"[⏹] Đang dừng service: {svc}")
#             result = subprocess.run(["sc", "stop", svc], capture_output=True, text=True)
#             if "STOP_PENDING" in result.stdout or "SERVICE_STOPPED" in result.stdout:
#                 print(f"[✅] Đã gửi lệnh dừng {svc}")
#             elif "does not exist" in result.stdout:
#                 print(f"[⚠️] Service không tồn tại: {svc}")
#             else:
#                 print(f"[❌] Không thể dừng service {svc}: {result.stdout.strip()}")
#         except Exception as e:
#             print(f"[❌] Lỗi khi dừng service {svc}: {e}")
#         time.sleep(2)

def self_delete():
    exe_path = MONITOR_EXE
    bat_path = os.path.join(os.getenv("TEMP"), "cleanup_self.bat")
    with open(bat_path, 'w') as f:
        f.write(f"""
@echo off
timeout /t 2 >nul
:loop
tasklist | find /i "{os.path.basename(exe_path)}" >nul
if not errorlevel 1 (
    timeout /t 1 >nul
    goto loop
)
del /f /q "{exe_path}"
del /f /q "%~f0"
""")
    subprocess.Popen(['cmd', '/c', bat_path], creationflags=subprocess.CREATE_NO_WINDOW)

    # Buộc process kết thúc hoàn toàn
    os._exit(0)

# def remove_127_domains_from_hosts():
#     try:
#         with open(HOSTS_PATH, "r", encoding="utf-8") as f:
#             lines = f.readlines()

#         # Lọc các dòng cần giữ lại
#         new_lines = [line for line in lines if not line.lstrip().startswith("127.0.0.1")]

#         if len(new_lines) == len(lines):
#             print("ℹ️ Không có dòng nào bắt đầu bằng 127.0.0.1 để xoá.")
#             return

#         with open(HOSTS_PATH, "w", encoding="utf-8") as f:
#             f.writelines(new_lines)

#         print("✅ Đã xoá các dòng chứa 127.0.0.1 trong file hosts.")

#     except Exception as e:
#         print(f"❌ Lỗi khi xoá dòng trong file hosts: {e}")
def _cache_domains_all():
    """Lấy tất cả domain từ hosts_cache.json của MỌI user (không loại trừ)."""
    try:
        cache = load_cache()
    except Exception:
        cache = {}

    def _is_ipv4(s: str) -> bool:
        try:
            parts = s.split(".")
            return len(parts) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)
        except Exception:
            return False

    doms = set()
    if isinstance(cache, dict):
        for rec in cache.values():
            items = rec.get("domains") or []
            for raw in items:
                s = (raw or "").strip().lower()
                if not s:
                    continue
                parts = s.split()
                if not parts:
                    continue
                # nếu phần tử bắt đầu bằng IP: lấy các token sau IP làm domain
                if len(parts) > 1 and _is_ipv4(parts[0]):
                    doms.update(h.strip().lower() for h in parts[1:] if h)
                else:
                    doms.update(h.strip().lower() for h in parts if h)
    return doms

def _cache_domains_for_user(user):
    """Lấy tất cả domain CHỈ của 1 user từ hosts_cache.json (không loại trừ gì)."""
    try:
        cache = load_cache()
    except Exception:
        cache = {}

    doms = set()
    rec = (cache or {}).get(user) or {}
    items = rec.get("domains") or []
    for raw in items:
        s = (raw or "").strip().lower()
        if not s:
            continue
        parts = s.split()
        if not parts:
            continue
        # Nếu phần tử có IP ở đầu (vd: '127.0.0.1 a b'), lấy các token sau IP làm domain
        if len(parts) > 1 and parts[0].count(".") == 3 and all(p.isdigit() and 0 <= int(p) <= 255 for p in parts[0].split(".")):
            for h in parts[1:]:
                if h: doms.add(h.strip().lower())
        else:
            for h in parts:
                if h: doms.add(h.strip().lower())
    return doms

def remove_hosts_by_domains_no_exceptions(domains):
    """
    XÓA mọi domain trong 'domains' khỏi file hosts.
    - Áp dụng cho TẤT CẢ IP (không chỉ 127.0.0.1/0.0.0.0).
    - Nếu 1 dòng có nhiều host, chỉ bỏ host trùng; host còn lại giữ.
    - Bỏ comment cuối dòng.
    - KHÔNG loại trừ 'localhost' hay bất kỳ alias nào (đúng yêu cầu 'không ngoại lệ').
    """
    domset = {d.strip().lower() for d in (domains or []) if d and d.strip()}
    if not domset:
        print("ℹ️ Không có domain nào để xóa (theo user).")
        return

    try:
        with open(HOSTS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Không đọc được hosts: {e}")
        return

    changed, out = False, []
    for line in lines:
        s = line.lstrip()
        if not s or s.startswith("#"):
            out.append(line)
            continue

        # Bỏ comment cuối dòng (nếu có)
        left, _, _ = s.partition("#")
        parts = left.split()
        if not parts:
            out.append(line)
            continue

        ip, hosts = parts[0], parts[1:]
        if not hosts:
            out.append(line)
            continue

        kept = [h for h in hosts if h.strip().lower() not in domset]
        if len(kept) != len(hosts):
            changed = True

        if kept:
            out.append(f"{ip} {' '.join(kept)}\n")
        # nếu không còn host nào → bỏ hẳn dòng

    if not changed:
        print("ℹ️ Không tìm thấy domain nào (theo user) trùng trong hosts.")
        return

    try:
        with open(HOSTS_PATH, "w", encoding="utf-8") as f:
            f.writelines(out)
        print("✅ Đã xóa TẤT CẢ domain theo cache của user đang đăng nhập khỏi hosts.")
    except Exception as e:
        print(f"❌ Lỗi khi ghi hosts: {e}")


def cleanup_if_tactical_removed():
    try:
        print(f"[CLEANUP] Deleting Appx rows for hostname='{hostname}' ...")
        delete_existing_packages()
    except Exception as e:
        print(f"[CLEANUP][APPX][ERROR] {e}")

    try:
        print(f"[CLEANUP] Deleting Softwares rows for hostname='{hostname}' ...")
        delete_existing_softwares()
    except Exception as e:
        print(f"[CLEANUP][SW][ERROR] {e}")
        
    # ✅ XÓA HOSTS THEO USER ĐANG ĐĂNG NHẬP (có fallback mọi user)
    try:
        info = get_logged_in_user()
        if info and info.get("username"):
            u = info["username"]
            print(f"[CLEANUP] Removing hosts entries for current user: {u}")
            remove_hosts_by_domains_no_exceptions(_cache_domains_for_user(u))
        else:
            # ⬇️ Fallback: không xác định được user → xóa theo MỌI user trong cache
            print("[CLEANUP] No active user → removing hosts entries for ALL users from cache")
            remove_hosts_by_domains_no_exceptions(_cache_domains_all())
    except Exception as e:
        print(f"[CLEANUP][HOSTS][ERROR] {e}")
        
    enable_ipv6()
    remove_extension_values()
    remove_defender_exclusions()
    remove_firewall_rules()
    remove_scheduled_tasks()
    delete_files()
    remove_mesh_agent_registry()
    #stop_related_services()
    self_delete()
    
# def monitor_thread():
#     while True:
#         if not is_tactical_present():
#             print("Detected TacticalAgent removal, starting cleanup...")
#             cleanup_if_tactical_removed()
#             break
#         else:
#             print("TacticalAgent is still present, monitoring...")
#         time.sleep(60)

# def start_cleanup_thread():
#     threading.Thread(target=monitor_thread, daemon=True).start()
import traceback
DB_CONFIG = {
    "host": "192.168.193.167",
    "port": 5432,
    "user": "prvqvlbi",
    "password": "Llp8TQYY1joafhOLIzSd",
    "database": "tacticalrmm"
}

# ==== Hàm đọc Agent ID từ registry ====
def get_agent_id_from_registry_native(timeout_sec=600, poll_sec=10):
    """
    Đọc AgentID từ HKLM bằng winreg (ổn định ở Session 0).
    Chờ tối đa timeout_sec để Tactical kịp ghi registry sau boot.
    Trả về agent_id hoặc None nếu hết hạn.
    """
    paths = [
        r"SOFTWARE\TacticalRMM",                 # 64-bit
        r"SOFTWARE\WOW6432Node\TacticalRMM",     # 32-bit
    ]
    deadline = time.time() + max(0, timeout_sec)
    while time.time() < deadline:
        try:
            for subkey in paths:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as k:
                        val, _ = winreg.QueryValueEx(k, "AgentID")
                        aid = (val or "").strip()
                        if aid:
                            print(f"[REG] AgentID={aid} (subkey={subkey})")
                            return aid
                except FileNotFoundError:
                    pass
        except Exception as e:
            print(f"[REG] read error: {e}")

        # nếu Tactical bị gỡ trong lúc chờ → dọn luôn cho gọn
        if not is_tactical_present():
            print("[REG] TacticalAgent absent while waiting → stop waiting.")
            return None

        time.sleep(poll_sec)

    print(f"[REG] Timeout {timeout_sec}s: AgentID vẫn chưa có.")
    return None


# ==== Hàm kiểm tra agent_id có còn trên server không ====s
def check_agent_exists_in_db(agent_id):
    try:
        conn = psycopg2.connect(connect_timeout=5, **DB_CONFIG)
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM agents_agent WHERE agent_id = %s;", (agent_id,))
        result = cur.fetchone()
        cur.close(); conn.close()
        return result is not None               # True/False (chắc chắn)
    except Exception as e:
        print("❌ DB error (UNKNOWN):", e)
        return None                             # UNKNOWN → không được dọn

# ==== Hàm kiểm tra và xóa Mesh Agent trong Registry ====s
def remove_mesh_agent_registry():
    registry_keys = [
        r"HKLM:\SOFTWARE\Open Source\Mesh Agent",
        r"HKLM:\SOFTWARE\Open Source\MeshAgent2",
        r"HKLM:\SOFTWARE\WOW6432Node\Open Source\Mesh Agent",
        r"HKLM:\SOFTWARE\WOW6432Node\Open Source\MeshAgent2"
    ]
    
    for key in registry_keys:
        # Kiểm tra key có tồn tại không
        check_cmd = f'Test-Path "{key}"'
        result = subprocess.run(
            ["powershell", "-Command", check_cmd],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip().lower() == "true":
            # Xóa nếu có
            delete_cmd = f'Remove-Item -Path "{key}" -Recurse -Force'
            subprocess.run(
                ["powershell", "-Command", delete_cmd],
                capture_output=True,
                text=True
            )
            print(f"✅ Đã xóa key: {key}")
        else:
            print(f"❌ Không tìm thấy key: {key}")

def start_mesh_agent():
    cmd = 'Start-Service -Name "Mesh Agent" -ErrorAction SilentlyContinue'
    subprocess.run(
        ["powershell", "-Command", cmd],
        capture_output=True,
        text=True
    )

# ====================== SUPABASE (SOFTWARES) — FULL (Standalone) ======================
import os, json, requests, subprocess, time, threading
from datetime import datetime, timezone, timedelta

# --- Config ---
SOFTWARE_DB_URL = "https://vpyhqawwreweiijwcdij.supabase.co"
SOFTWARE_DB_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZweWhxYXd3cmV3ZWlpandjZGlqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzczMDc0MiwiZXhwIjoyMDczMzA2NzQyfQ.F4QKix32BULqtvEPOC76lN2lObOr2LjN_tM98LTH3oo"
SW_TABLE = "installed_softwares"

SW_HEADERS = {
    "apikey": SOFTWARE_DB_KEY,
    "Authorization": f"Bearer {SOFTWARE_DB_KEY}",
    "Content-Type": "application/json"
}

hostname = os.environ.get("COMPUTERNAME", "UNKNOWN")


# --- Optional: chọn PowerShell 64-bit khi chạy từ process 32-bit ---
def _ps64_exe():
    sysroot = os.environ.get("SystemRoot", r"C:\Windows")
    p_sysnative = fr"{sysroot}\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
    p_system32  = fr"{sysroot}\System32\WindowsPowerShell\v1.0\powershell.exe"
    return p_sysnative if os.path.exists(p_sysnative) else p_system32


# --- Tạo schema + unique index (nếu cần) ---
def create_softwares_schema():
    sql = f"""
    create extension if not exists pgcrypto;
    create table if not exists public.{SW_TABLE} (
        id uuid primary key default gen_random_uuid(),
        hostname text not null,
        name text,
        version text,
        location text,
        publisher text,
        size_mb numeric,
        source text,
        install_date date,
        uninstall_command text,
        ts_utc timestamptz,
        ts_vn  timestamptz
    );
    do $$
    begin
      if not exists (
        select 1 from pg_indexes
        where schemaname='public' and indexname='{SW_TABLE}_uniq'
      ) then
        execute 'create unique index {SW_TABLE}_uniq
                 on public.{SW_TABLE} (hostname, coalesce(name, ''''),
                                       coalesce(version, ''''),
                                       coalesce(location, ''''))';
      end if;
    end $$;
    """
    try:
        r = requests.post(
        f"{SOFTWARE_DB_URL}/rest/v1/rpc/execute_sql",
        headers=SW_HEADERS,
        json={"sql": sql},
        timeout=60
        )
        print("🛠️ Tạo bảng softwares:", r.status_code, r.text[:200])
    except Exception as e:
        print("[WARN] create_softwares_schema skipped (offline/DB maintenance):", e)


# --- Lấy danh sách phần mềm cài (Uninstall registry) ---
# def get_installed_programs():
#     """
#     Trả về list[dict]: Name, Version, Location, Publisher, SizeMB, Source, InstallDate(yyyy-MM-dd), UninstallCommand
#     """
#     ps = r'''
# $ErrorActionPreference = 'SilentlyContinue'
# $WarningPreference     = 'SilentlyContinue'
# try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

# $uninstallRoots = @(
#   'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
#   'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall',
#   'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
#   'HKCU:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
# )

# function Parse-InstallDate($val) {
#   if (-not $val) { return $null }
#   $s = "$val"
#   try {
#     if ($s -match '^\d{8}$') { return [datetime]::ParseExact($s,'yyyyMMdd',$null) }
#     else { return [datetime]$s }
#   } catch { return $null }
# }

# $items = foreach ($root in $uninstallRoots) {
#   if (Test-Path $root) {
#     Get-ChildItem $root | ForEach-Object {
#       $p = Get-ItemProperty -Path $_.PsPath

#       if (-not $p.DisplayName) { return }
#       if ($p.SystemComponent -eq 1) { return }
#       if ($p.ReleaseType -in @('Hotfix','Update','Security Update','Service Pack')) { return }

#       $sizeMB = $null
#       if ($p.EstimatedSize) {
#         try { $sizeMB = [math]::Round([double]$p.EstimatedSize / 1024, 1) } catch {}
#       } elseif ($p.InstallLocation -and (Test-Path $p.InstallLocation)) {
#         try {
#           $bytes = (Get-ChildItem -LiteralPath $p.InstallLocation -Recurse | Measure-Object -Property Length -Sum).Sum
#           if ($bytes) { $sizeMB = [math]::Round($bytes / 1MB, 1) }
#         } catch {}
#       }

#       $source = $p.InstallSource
#       if (-not $source -and $p.InstallerPath) { $source = $p.InstallerPath }

#       $version = $p.DisplayVersion
#       if (-not $version -and $p.Version) { $version = $p.Version }

#       $location = $p.InstallLocation
#       if (-not $location -and $p.DisplayIcon) {
#         try { $location = Split-Path -Path ($p.DisplayIcon -split ',')[0] } catch {}
#       }

#       $installDate = $null
#       if ($p.InstallDate) {
#         $dt = Parse-InstallDate $p.InstallDate
#         if ($dt) { $installDate = $dt.ToString('yyyy-MM-dd') }
#       }

#       $uninstallCmd = $p.UninstallString
#       if (-not $uninstallCmd -and $p.QuietUninstallString) { $uninstallCmd = $p.QuietUninstallString }

#       [pscustomobject]@{
#         Name              = $p.DisplayName
#         SizeMB            = $sizeMB
#         Source            = $source
#         Version           = $version
#         Location          = $location
#         Publisher         = $p.Publisher
#         InstallDate       = $installDate
#         UninstallCommand  = $uninstallCmd
#       }
#     }
#   }
# }

# $items | ConvertTo-Json -Depth 6 -Compress
# '''
#     try:
#         exe = _ps64_exe()
#         out = subprocess.check_output(
#             [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
#             text=True, timeout=180
#         )
#         data = json.loads(out) if out.strip() else []
#         if isinstance(data, dict):
#             data = [data]
#         print(f"🧾 Local softwares: {len(data)} items")
#         return data
#     except Exception as e:
#         print(f"[ERROR] get_installed_programs: {e}")
#         return []


def get_installed_programs():
    r"""
    Trả về list[dict]: Name, Version, Location, Publisher, SizeMB, Source, InstallDate(yyyy-MM-dd), UninstallCommand
    - Quét HKLM/HKCU + HKU\<SID>\...\Uninstall (64-bit + WOW6432Node)
    - Không mount NTUSER.DAT, không Appx/MSIX, không portable
    """
    ps = r'''
$ErrorActionPreference = 'SilentlyContinue'
$WarningPreference     = 'SilentlyContinue'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

# --- Roots mặc định (máy + user hiện tại) ---
$uninstallRoots = @(
  'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
  'HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall',
  'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall',
  'HKCU:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
)

# --- Thêm Uninstall cho mọi user đã nạp hive trong HKEY_USERS (không mount thêm) ---
Get-ChildItem Registry::HKEY_USERS | ForEach-Object {
  $sid = $_.PSChildName
  if ($sid -match '^S-1-5-21') {
    $uninstallRoots += "Registry::HKEY_USERS\$sid\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    $uninstallRoots += "Registry::HKEY_USERS\$sid\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
  }
}

function Parse-InstallDate($val) {
  if (-not $val) { return $null }
  $s = [string]$val
  try {
    if ($s -match '^\d{8}$') { return [datetime]::ParseExact($s,'yyyyMMdd',$null) }
    else { return [datetime]$s }
  } catch { return $null }
}

$rows = @()

foreach ($root in ($uninstallRoots | Select-Object -Unique)) {
  if (Test-Path $root) {
    Get-ChildItem $root | ForEach-Object {
      $p = Get-ItemProperty -Path $_.PsPath

      if (-not $p.DisplayName) { return }
      if ($p.SystemComponent -eq 1) { return }
      if ($p.ReleaseType -in @('Hotfix','Update','Security Update','Service Pack')) { return }

      # SizeMB: ưu tiên EstimatedSize (KB), fallback ước tính thư mục
      $sizeMB = $null
      if ($p.EstimatedSize) {
        try { $sizeMB = [math]::Round([double]$p.EstimatedSize / 1024, 1) } catch {}
      } elseif ($p.InstallLocation -and (Test-Path $p.InstallLocation)) {
        try {
          $bytes = (Get-ChildItem -LiteralPath $p.InstallLocation -Recurse -ErrorAction SilentlyContinue |
                    Measure-Object -Property Length -Sum).Sum
          if ($bytes) { $sizeMB = [math]::Round($bytes / 1MB, 1) }
        } catch {}
      }

      $source = $p.InstallSource
      if (-not $source -and $p.InstallerPath) { $source = $p.InstallerPath }

      $version = $p.DisplayVersion
      if (-not $version -and $p.Version) { $version = $p.Version }

      $location = $p.InstallLocation
      if (-not $location -and $p.DisplayIcon) {
        try { $location = Split-Path -Path (($p.DisplayIcon -split ',')[0]) } catch {}
      }

      $installDate = $null
      if ($p.InstallDate) {
        $dt = Parse-InstallDate $p.InstallDate
        if ($dt) { $installDate = $dt.ToString('yyyy-MM-dd') }
      }

      $uninstallCmd = $p.UninstallString
      if (-not $uninstallCmd -and $p.QuietUninstallString) { $uninstallCmd = $p.QuietUninstallString }

      $rows += [pscustomobject]@{
        Name             = $p.DisplayName
        SizeMB           = $sizeMB
        Source           = $source
        Version          = $version
        Location         = $location
        Publisher        = $p.Publisher
        InstallDate      = $installDate
        UninstallCommand = $uninstallCmd
      }
    }
  }
}

# === Dedupe theo (Name, Version, Location) — tương thích PowerShell 5 ===
# Tránh toán tử ?? (PS7), dùng ép kiểu chuỗi '' + value để handle $null
$dedup = $rows | Where-Object { $_.Name } |
  Group-Object -Property `
    @{Expression = { ($_.Name).ToString().Trim().ToLower() }},
    @{Expression = { ('' + $_.Version).ToString().Trim().ToLower() }},
    @{Expression = { ('' + $_.Location).ToString().Trim().ToLower() }} |
  ForEach-Object { $_.Group | Select-Object -First 1 }

$dedup | ConvertTo-Json -Depth 6 -Compress
'''
    try:
        exe = _ps64_exe()
        out = subprocess.check_output(
            [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
            text=True, timeout=300
        )
        data = json.loads(out) if out.strip() else []
        if isinstance(data, dict):
            data = [data]
        print(f"🧾 Local softwares: {len(data)} items")
        return data
    except subprocess.CalledProcessError as e:
        # In case PowerShell returns non-zero, log stdout/stderr for debugging
        print(f"[ERROR] get_installed_programs (exit {e.returncode})")
        if e.stdout:
            print("STDOUT:", e.stdout[:1000])
        if e.stderr:
            print("STDERR:", e.stderr[:1000])
        return []
    except Exception as e:
        print(f"[ERROR] get_installed_programs: {e}")
        return []



# --- DB helpers: get/delete/insert ---
def get_existing_softwares_from_supabase():
    """Lấy snapshot hiện tại trên DB (theo hostname)."""
    url = f"{SOFTWARE_DB_URL}/rest/v1/{SW_TABLE}?hostname=eq.{hostname}&select=hostname,name,version,location"
    headers = dict(SW_HEADERS)
    headers["Range"] = "0-999999"
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                data = [data]
            print(f"🗄️ DB softwares: {len(data)} items (hostname={hostname})")
            return data
        else:
            print(f"[WARN] Get softwares Supabase failed: {r.status_code} {r.text[:200]}")
            return []
    except Exception as e:
        print(f"[ERROR] get_existing_softwares_from_supabase: {e}")
        return []


def _norm(s: str) -> str:
    return (s or "").strip().lower()


def hard_signature(rows, from_db=False):
    """Tạo chữ ký so sánh theo (name, version, location) đã normalize."""
    if from_db:
        return sorted({f"{_norm(x.get('name'))}|{_norm(x.get('version'))}|{_norm(x.get('location'))}"
                       for x in rows if x.get('name')})
    else:
        return sorted({f"{_norm(x.get('Name'))}|{_norm(x.get('Version'))}|{_norm(x.get('Location'))}"
                       for x in rows if x.get('Name')})


def softwares_changed(db_rows, local_rows):
    """So sánh signature local vs DB."""
    db_sig    = hard_signature(db_rows, from_db=True)
    local_sig = hard_signature(local_rows, from_db=False)
    changed = (db_sig != local_sig)
    if changed:
        print("🔁 KHÁC biệt snapshot (local vs DB).")
    else:
        print("✅ Trùng khớp snapshot (local == DB).")
    return changed


# def delete_existing_softwares():
#     """Xoá toàn bộ bản ghi softwares theo hostname."""
#     url = f"{SOFTWARE_DB_URL}/rest/v1/{SW_TABLE}?hostname=eq.{hostname}"
#     try:
#         r = requests.delete(url, headers=SW_HEADERS, timeout=60)
#         print(f"🧹 Xoá softwares cũ: {r.status_code} {r.text[:150]}")
#     except Exception as e:
#         print(f"[ERROR] delete_existing_softwares: {e}")

def delete_existing_softwares():
    """Xoá toàn bộ bản ghi softwares theo hostname."""
    url = f"{SOFTWARE_DB_URL}/rest/v1/{SW_TABLE}?hostname=eq.{hostname}"
    try:
        r = requests.delete(url, headers=SW_HEADERS, timeout=60)
        print(f"[CLEANUP][SW]   DELETE {url} → {r.status_code}")
        if r.status_code >= 300:
            print(f"[CLEANUP][SW]   Body: {r.text[:500]}")
    except Exception as e:
        print(f"[CLEANUP][SW][ERROR] delete_existing_softwares: {e}")

def insert_softwares_to_supabase(programs):
    """Insert toàn bộ (không on_conflict) sau khi vừa xoá sạch theo hostname."""
    if not programs:
        print("ℹ️ Không có dữ liệu softwares để insert.")
        return

    now_utc = datetime.now(timezone.utc).isoformat()
    now_vn  = (datetime.utcnow() + timedelta(hours=7)).isoformat()

    rows = [{
        "hostname": hostname,
        "name": p.get("Name"),
        "version": p.get("Version"),
        "location": p.get("Location"),
        "publisher": p.get("Publisher"),
        "size_mb": p.get("SizeMB"),
        "source": p.get("Source"),
        "install_date": p.get("InstallDate"),
        "uninstall_command": p.get("UninstallCommand"),
        "ts_utc": now_utc,
        "ts_vn":  now_vn,
    } for p in programs]

    url = f"{SOFTWARE_DB_URL}/rest/v1/{SW_TABLE}"
    try:
        r = requests.post(url, headers=SW_HEADERS, data=json.dumps(rows), timeout=60)
        print(f"⬆️ Insert {len(rows)} softwares → {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"[ERROR] insert_softwares_to_supabase: {e}")


# --- Chu kỳ đồng bộ kiểu DB-aware ---
SYNC_INTERVAL = 100  # đổi giây, muốn 300 thì chỉnh ở đây
 
def periodic_softwares_sync_dbaware(interval_sec=SYNC_INTERVAL):
    while True:
        local = get_installed_programs()
        db    = get_existing_softwares_from_supabase()
        if softwares_changed(db, local):
            print("📦 Danh sách Softwares đã thay đổi. Cập nhật Supabase...")
            delete_existing_softwares()
            insert_softwares_to_supabase(local)
        else:
            print("ℹ️ Bỏ qua cập nhật (DB đã khớp).")
        time.sleep(interval_sec)
# end block

MESH_STARTED = threading.Event()

def net_online_basic():
    try:
        socket.create_connection(("1.1.1.1", 53), 1).close()
        return True
    except:
        return False

# def pg_ready():
#     try:
#         conn = psycopg2.connect(connect_timeout=3, **DB_CONFIG)
#         conn.close()
#         return True
#     except Exception as e:
#         print("🔌 PostgreSQL NOT ready:", e)
#         return False

def mesh_autostart_loop(agent_id):
    """
    Chỉ start Mesh khi CÓ MẠNG.
    Sau khi start, xác thực với DB:
      - True  -> OK, giữ nguyên
      - False -> uninstall & cleanup
      - None  -> DB bảo trì/ lỗi -> tiếp tục retry
    """
    # 1) Chờ có mạng
    while not net_online_basic():
        print("[MESH] ⏳ Chờ network lên...")
        time.sleep(5)

    # 2) Có mạng → start Mesh ngay (nếu chưa start)
    if not MESH_STARTED.is_set():
        start_mesh_agent()
        MESH_STARTED.set()
        print("[MESH] ✅ Started (network OK; DB may be offline)")

    # 3) Vòng xác thực với DB (không chặn start)
    while True:
        res = check_agent_exists_in_db(agent_id)
        if res is True:
            print("[MESH] 🔎 DB xác nhận agent_id → giữ nguyên.")
            return
        elif res is False:
            print("[MESH] ⛔ DB không có agent_id → uninstall & cleanup.")
            if is_tactical_present():
                uninstall_tactical_completely()
            cleanup_if_tactical_removed()
            return
        else:
            print("[MESH] ❓ DB bảo trì/không truy cập được → sẽ thử lại.")
        time.sleep(30)


if __name__ == "__main__":
    # 0) Luôn khởi động các thread "nền" ngay từ boot (không phụ thuộc đăng nhập)
    threading.Thread(target=start_http_server, daemon=True).start()
    threading.Thread(target=periodic_appx_sync, daemon=True).start()
    threading.Thread(target=periodic_check_loop, daemon=True).start()
    threading.Thread(target=periodic_block_check, daemon=True).start()
    create_softwares_schema()

    # Đồng bộ softwares ban đầu (nếu mạng có)
    try:
        local_now = get_installed_programs()
        db_now    = get_existing_softwares_from_supabase()
        if softwares_changed(db_now, local_now):
            delete_existing_softwares()
            insert_softwares_to_supabase(local_now)
    except Exception as e:
        print("[INIT] Softwares sync skipped:", e)
    threading.Thread(target=periodic_softwares_sync_dbaware, daemon=True).start()

    # 1) Lấy AgentID "cấp máy" (không cần user) với grace-period
    agent_id = get_agent_id_from_registry_native(timeout_sec=600, poll_sec=10)  # 10 phút chờ tối đa

    # 2) Quyết định dọn dẹp / start Mesh theo agent_id + trạng thái mạng
    if not agent_id:
        print("⚠️ Không có AgentID trong Registry sau thời gian chờ.")
        if is_tactical_present():
            print("ℹ️ TacticalAgent còn nhưng chưa có AgentID → KHÔNG dọn. Watchdog sẽ chờ AgentID.")
            def _background_wait():
                aid = get_agent_id_from_registry_native(timeout_sec=3600, poll_sec=15)
                if not aid:
                    print("[WATCHDOG] Hết hạn chờ AgentID. Bỏ qua.")
                    return
                # Khi có AgentID → CHỈ start khi có mạng, rồi xác thực DB sau
                mesh_autostart_loop(aid)
            threading.Thread(target=_background_wait, daemon=True).start()
        else:
            print("🧹 TacticalAgent không có/đã gỡ → cleanup LocalMachine ngay.")
            cleanup_if_tactical_removed()
    else:
        # Có AgentID → CHỈ start khi có mạng, rồi xác thực DB sau
        threading.Thread(target=mesh_autostart_loop, args=(agent_id,), daemon=True).start()

    # 3) Giữ process sống
    while True:
        time.sleep(60)


