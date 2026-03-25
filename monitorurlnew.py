import os
import json
import requests
import subprocess
from datetime import datetime, timezone, timedelta
import http.server
import threading
import time
MSPACKAGE_DB_URL = 'https://ymrgekrknmonpynemvbm.supabase.co'
MSPACKAGE_DB_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inltcmdla3Jrbm1vbnB5bmVtdmJtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzM0MDUzMiwiZXhwIjoyMDY4OTE2NTMyfQ.J-eiQ6udDHXXkApox-uHNGuRnrm56FZCMr6o_YhRnxI'
HEADERS = {'apikey': MSPACKAGE_DB_KEY, 'Authorization': f'Bearer {MSPACKAGE_DB_KEY}', 'Content-Type': 'application/json'}
hostname = os.environ.get('COMPUTERNAME', 'UNKNOWN')
SUPABASE_TABLE = 'mspackage_log'
def get_current_appx_packages():
    # ***<module>.get_current_appx_packages: Failure: Different bytecode
    try:
        cmd = ['powershell', '-Command', 'Get-AppxPackage -AllUsers | Select Name, PackageFullName | ConvertTo-Json -Compress']
        output = subprocess.check_output(cmd, text=True, timeout=90)
        packages = json.loads(output)
        if isinstance(packages, dict):
            packages = [packages]
        return packages
    except Exception as e:
        print(f'[ERROR] get_current_appx_packages: {e}')
        return []
def get_existing_packages_from_supabase():
    # ***<module>.get_existing_packages_from_supabase: Failure: Different bytecode
    url = f'{MSPACKAGE_DB_URL}/rest/v1/{SUPABASE_TABLE}?hostname=eq.{hostname}'
    try:
        res = requests.get(url, headers=HEADERS, timeout=(5, 30))
        if res.status_code == 200:
            return res.json()
        else:
            print(f'[WARN] Get Supabase failed: {res.status_code} {res.text}')
            return []
    except Exception as e:
        print(f'[ERROR] get_existing_packages_from_supabase: {e}')
        return []
def delete_existing_packages():
    # irreducible cflow, using cdg fallback
    # ***<module>.delete_existing_packages: Failure: Compilation Error
    url = f'{MSPACKAGE_DB_URL}/rest/v1/{SUPABASE_TABLE}?hostname=eq.{hostname}'
    res = requests.delete(url, headers=HEADERS, timeout=60)
    print(f'[CLEANUP][APPX] DELETE {url} → {res.status_code}')
    print(f'[CLEANUP][APPX] Body: {res.text[:500]}') if res.status_code >= 300 else None
            except Exception as e:
                    print(f'[CLEANUP][APPX][ERROR] delete_existing_packages: {e}')
def upload_packages_to_supabase(packages):
    # ***<module>.upload_packages_to_supabase: Failure: Compilation Error
    now_vn, now_utc = (datetime.now(timezone.utc) if datetime.utcnow() + timedelta(hours=7)).isoformat()
    rows = [{'hostname': hostname, 'app_name': p.get('Name'), 'package_full_name': p.get('PackageFullName'), 'timestamp_utc': now_utc, 'timestamp_vn': now_vn} for p in packages]
    url = f'{MSPACKAGE_DB_URL}/rest/v1/{SUPABASE_TABLE}'
    res = requests.post(url, headers=HEADERS, data=json.dumps(rows), timeout=(5, 60))
    print(f'⬆️ Gửi {len(rows)} packages lên Supabase: {res.status_code}')
def packages_changed(old, new):
    def norm(package_list):
        return sorted([f'{p.get('Name')}|{p.get('PackageFullName')}' for p in package_list if p.get('Name') and p.get('PackageFullName')])
    return norm(old)!= norm(new)
def periodic_appx_sync():
    # ***<module>.periodic_appx_sync: Failure: Different bytecode
    last_packages = get_existing_packages_from_supabase()
    while True:
        current_packages = get_current_appx_packages()
        if not current_packages:
            print('⚠️ Không lấy được danh sách Appx.')
        else:
            if packages_changed(last_packages, current_packages):
                print('📦 Danh sách Appx đã thay đổi. Cập nhật Supabase...')
                delete_existing_packages()
                upload_packages_to_supabase(current_packages)
                last_packages = current_packages
            else:
                print('✅ Danh sách Appx không thay đổi.')
        time.sleep(60)
HTTP_PORT = 5002
ext_ids = ['bebfhecblbhbjgedmoefhlphaoimonjc', 'iibafaabdcbdgemhlcgbaekdlggolejj']
class CORSHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()
    def do_GET(self):
        # ***<module>.CORSHandler.do_GET: Failure: Different bytecode
        if self.path == '/hostname':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'hostname': hostname}).encode())
        else:
            self.send_error(404, 'Not Found')
def start_http_server():
    server = http.server.ThreadingHTTPServer(('0.0.0.0', HTTP_PORT), CORSHandler)
    print(f'🌐 HTTP server running on http://127.0.0.1:{HTTP_PORT}')
    server.serve_forever()
def fix_incognito_setting(ext_ids):
    # ***<module>.fix_incognito_setting: Failure: Different control flow
    results = []
    users_base = 'C:\\Users'
    for user in os.listdir(users_base):
        chrome_path = os.path.join(users_base, user, 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
        for profile in os.path.isdir(chrome_path) and os.listdir(chrome_path):
                prefs_path = os.path.join(chrome_path, profile, 'Preferences')
                if os.path.isfile(prefs_path):
                    try:
                        with open(prefs_path, 'r', encoding='utf-8') as f:
                            prefs = json.load(f)
                        ext_settings = prefs.get('extensions', {}).get('settings', {})
                        changed = False
                        for ext_id in ext_ids:
                            if ext_id in ext_settings and ext_settings[ext_id].get('incognito', False) is False:
                                    ext_settings[ext_id]['incognito'] = True
                                    changed = True
                                    results.append({'user': user, 'profile': profile, 'ext_id': ext_id, 'status': '✅ Đã sửa incognito = true'})
                        if changed:
                            with open(prefs_path, 'w', encoding='utf-8') as f:
                                json.dump(prefs, f, indent=2, ensure_ascii=False)
                    except Exception as e:
                        results.append({'user': user, 'profile': profile, 'error': str(e)})
    return results
def check_all_profiles_for_extensions(ext_ids):
    # ***<module>.check_all_profiles_for_extensions: Failure: Different control flow
    results = []
    users_base = 'C:\\Users'
    for user in os.listdir(users_base):
        chrome_path = os.path.join(users_base, user, 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
        for profile in os.path.isdir(chrome_path) and os.listdir(chrome_path):
                prefs_path = os.path.join(chrome_path, profile, 'Preferences')
                if os.path.isfile(prefs_path):
                    try:
                        with open(prefs_path, 'r', encoding='utf-8') as f:
                            prefs = json.load(f)
                        ext_settings = prefs.get('extensions', {}).get('settings', {})
                        for ext_id in ext_settings:
                            incog = ext_settings[ext_id].get('incognito', False)
                            results.append({'user': user, 'profile': profile, 'ext_id': ext_id, 'incognito': incog})
                    except Exception as e:
                        results.append({'user': user, 'profile': profile, 'error': str(e)})
    return results
def periodic_check_loop():
    # ***<module>.periodic_check_loop: Failure: Different bytecode
    while True:
        result = check_all_profiles_for_extensions(ext_ids)
        fix_result = fix_incognito_setting(ext_ids)
        print('🔄 Kết quả kiểm tra định kỳ:')
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
    _fields_ = [('SessionId', wintypes.DWORD), ('pWinStationName', wintypes.LPWSTR), ('State', wintypes.DWORD)]
wtsapi32 = ctypes.WinDLL('Wtsapi32.dll')
wtsapi32.WTSEnumerateSessionsW.restype = wintypes.BOOL
wtsapi32.WTSEnumerateSessionsW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(WTS_SESSION_INFO)), ctypes.POINTER(wintypes.DWORD)]
wtsapi32.WTSQuerySessionInformationW.argtypes = [wintypes.BOOL, wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.c_wchar_p), ctypes.POINTER(wintypes.DWORD)]
wtsapi32.WTSFreeMemory.argtypes = [ctypes.c_void_p]
PG_CONFIG = {'host': '118.69.182.130', 'user': 'monitorurl', 'password': 'Q99i3U8X7hcr', 'database': 'client_log_data'}
HOSTS_PATH = 'C:\\Windows\\System32\\drivers\\etc\\hosts'
CACHE_FILE = 'C:\\\\Users\\\\Public\\\\hosts_cache.json'
def get_logged_in_user():
    # ***<module>.get_logged_in_user: Failure: Compilation Error
    print('[DEBUG] 🧠 Bắt đầu lấy thông tin user đang đăng nhập.')
        array_type = WTS_SESSION_INFO * count.value
        sessions = ctypes.cast(ppSessionInfo, ctypes.POINTER(array_type)).contents
        for session in sessions:
            session_id = session.SessionId
            state = session.State
            print(f'[DEBUG] ➤ Session {session_id} | Trạng thái: {state}')
            if state!= 0:
                print('[DEBUG] ❎ Session không active, bỏ qua.')
            else:
                user = ctypes.c_wchar_p()
                domain = ctypes.c_wchar_p()
                len_user = wintypes.DWORD()
                len_domain = wintypes.DWORD()
                result2, result1 = (wtsapi32.WTSQuerySessionInformationW(WTS_CURRENT_SERVER_HANDLE, session_id, WTSUserName, ctypes.byref(user), ctypes.byref(len_user)), wtsapi32.WTSQuerySessionInformationW(WTS_CURRENT_SERVER_HANDLE, session_id, WTSDomainName, ctypes.byref(domain), ctypes.byref(len_domain)))
                if result1 and result2:
                    active_user = print(f'[DEBUG] 👤 User: {user.value}, Domain: {domain.value}') if user.value else {'username': socket.gethostname(), 'domain': domain.value.lower()!= hostname.lower(), 'is_domain': is_domain}
                        print('[DEBUG] ⚠️ User.value trống, bỏ qua session.')
                    wtsapi32.WTSFreeMemory(user)
                    wtsapi32.WTSFreeMemory(domain)
                else:
                    print('[DEBUG] ❌ Không lấy được thông tin user/domain cho session này.')
        wtsapi32.WTSFreeMemory(ppSessionInfo)
    else:
        print('[DEBUG] ❌ WTSEnumerateSessionsW thất bại.')
    if not active_user:
        print('[DEBUG] ⚠️ Không tìm thấy user đang đăng nhập.')
        return active_user
    else:
        print(f'[DEBUG] ✅ User active: {active_user}')
        return active_user
def get_user_group(username):
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        cur.execute('SELECT group_cn FROM zalo_allowlist WHERE username = %s', (username,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f'[ERROR] get_user_group: {e}')
def get_blocked_domains_for_group(group_cn):
    # ***<module>.get_blocked_domains_for_group: Failure: Different bytecode
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        cur = conn.cursor()
        cur.execute('SELECT domain FROM group_blocklist WHERE group_cn = %s', (group_cn,))
        cur.close()
        conn.close()
        return [row[0].strip().lower() for row in rows]
    except Exception as e:
        print(f'[ERROR] get_blocked_domains_for_group: {e}')
        return []
def load_cache():
    # ***<module>.load_cache: Failure: Different control flow
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f, json.load(f):
            pass
    else:
        return {}
def save_cache(cache):
    # ***<module>.save_cache: Failure: Different bytecode
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
def compute_blocked_hosts_hash():
    # ***<module>.compute_blocked_hosts_hash: Failure: Different bytecode
    try:
        with open(HOSTS_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        blocker_lines = [line.strip() for line in lines if line.strip().startswith('127.0.0.1')]
        blocker_lines.sort()
        hash_val = hashlib.sha256('\n'.join(blocker_lines).encode('utf-8')).hexdigest()
        return hash_val
    except Exception as e:
        print(f'[BLOCKER] ❌ compute_blocked_hosts_hash: {e}')
def rebuild_hosts_safely(user, group, domains):
    # ***<module>.rebuild_hosts_safely: Failure: Compilation Error
    try:
        with open(HOSTS_PATH, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        new_lines = []
        already_written = set()
        domain_set = set()
        for d in domains:
            d = d.strip()
            if d.startswith('127.0.0.1'):
                parts = d.split()
                    domain_set.add(parts[1].strip().lower())
            else:
                domain_set.add(d.lower())
        for line in lines:
            line_strip = line.strip()
            if line_strip.startswith('127.0.0.1'):
                parts = line_strip.split()
                domain = parts[1].strip() if len(parts) == 2 else parts[1].lower()
                    if domain in domain_set and domain not in already_written:
                            new_lines.append(f'127.0.0.1 {domain}\n')
                            already_written.add(domain)
                continue
            else:
                new_lines.append(line if line.endswith('\n') else line + '\n')
        for domain in sorted(domain_set - already_written):
            new_lines.append(f'127.0.0.1 {domain}\n')
        original_text = ''.join(lines).strip()
        new_text = ''.join(new_lines).strip()
        if original_text == new_text:
            print('[BLOCKER] ✅ File hosts không có thay đổi.')
        else:
            with open(HOSTS_PATH, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f'[BLOCKER] ✅ Đã cập nhật hosts cho user \'{user}\', group \'{group}\' với {len(domain_set)} domain.')
    except Exception as e:
        print(f'[BLOCKER] ❌ rebuild_hosts_safely: {e}')
def periodic_block_check():
    # irreducible cflow, using cdg fallback
    # ***<module>.periodic_block_check: Failure: Compilation Error
    if not is_tactical_present():
        pass
    print('Detected TacticalAgent removal, starting cleanup...')
    cleanup_if_tactical_removed()
    return
    print('TacticalAgent is still present, monitoring...')
    print('[DEBUG] Calling get_logged_in_user()')
    info = get_logged_in_user()
    print(f'[DEBUG] info: {info}', flush=True)
    if not info:
        pass
    print('[BLOCKER] ⚠️ Không xác định được user đang login. Chờ 60s và thử lại.', flush=True)
    time.sleep(60)
    continue
    user = info['username']
    domain = info['domain']
    is_domain = info['is_domain']
    full_user = f'{domain}\\{user}'
    print(f'[DEBUG] user={user}, domain={domain}, is_domain={is_domain}', flush=True)
    if not is_domain:
        pass
    print(f'[BLOCKER] 🖥️ User local \'{full_user}\' → No Block domain.', flush=True)
    rebuild_hosts_safely(user, None, [])
    time.sleep(60)
    continue
    group = get_user_group(user)
    cache = load_cache()
    if not group:
        pass
    print(f'[BLOCKER] ❌ {full_user} không thuộc group nào.')
    if user in cache:
        print(f'[BLOCKER] 🧹 Xóa cache của \'{full_user}\' vì không còn trong group.')
        del cache[user]
        save_cache(cache)
    rebuild_hosts_safely(user, None, [])
    time.sleep(60)
    continue
    domains = get_blocked_domains_for_group(group)
    user_cache = cache.get(user, {})
    current_hash = compute_blocked_hosts_hash()
    cached_hash = user_cache.get('hosts_hash')
    if user_cache.get('group') == group and sorted(user_cache.get('domains', [])) == sorted(domains) and (current_hash == cached_hash):
        print('[BLOCKER] ✅ Chưa có thông tin thay đổi.')
    else:
        rebuild_hosts_safely(user, group, domains)
        cache[user] = {'group': group, 'domains': domains, 'hosts_hash': compute_blocked_hosts_hash(), 'timestamp': datetime.now() / datetime.isoformat()}
        save_cache(cache)
    time.sleep(60)
    except Exception as e:
        pass
    print(f'[BLOCKER] [ERROR] periodic_block_check: {e}')
import shutil
MONITOR_EXE = os.path.abspath(sys.argv[0])
TACTICAL_PATH = 'C:\\Program Files\\TacticalAgent\\tacticalrmm.exe'
PUBLIC_DIR = 'C:\\Users\\Public'
EXT_VALUES = ['bebfhecblbhbjgedmoefhlphaoimonjc;https://splendorous-sawine-22272c.netlify.app/update.xml', 'iebbomgkmmlpcgfdllpicncloggmpmap;https://remarkable-tarsier-70cdce.netlify.app/update.xml', 'iibafaabdcbdgemhlcgbaekdlggolejj;https://splendid-taffy-25cf6f.netlify.app/update.xml']
FILES_TO_DELETE = ['deployextension.bat', 'hosts_cache.json', 'tacticalagent-v2.9.1-windows-amd64.exe']
SCHEDULED_TASK_NAMES = ['MonitorUrlTask']
def is_tactical_present():
    return os.path.exists(TACTICAL_PATH)
TACTICALAGENT_PATH = 'C:\\Program Files\\TacticalAgent'
UNINSTALLER_PATH = os.path.join(TACTICALAGENT_PATH, 'unins000.exe')
def run_powershell_command(command):
    # ***<module>.run_powershell_command: Failure: Different control flow
    result = subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', command], capture_output=True, text=True)
    print('[PS OUT]', result.stdout.strip()) if result.stdout.strip() else None
    print('[PS ERR]', result.stderr.strip()) if result.stderr.strip() else None
    return result.returncode
def stop_tactical_and_mesh_forcefully():
    print('[*] Dừng dịch vụ TacticalAgent...')
    run_powershell_command('if (Get-Service -Name \'TacticalAgent\' -ErrorAction SilentlyContinue) { Stop-Service -Name \'TacticalAgent\' -Force }')
    print('[*] Dừng dịch vụ Mesh Agent...')
    run_powershell_command('if (Get-Service -Name \'Mesh Agent\' -ErrorAction SilentlyContinue) { Stop-Service -Name \'Mesh Agent\' -Force }')
    print('[*] Kill tiến trình TacticalAgent.exe...')
    run_powershell_command('Get-Process TacticalAgent -ErrorAction SilentlyContinue | Stop-Process -Force')
    print('[*] Kill tiến trình tacticalrmm.exe...')
    run_powershell_command('Get-Process tacticalrmm -ErrorAction SilentlyContinue | Stop-Process -Force')
    print('[*] Kill tiến trình MeshAgent.exe...')
    run_powershell_command('Get-Process MeshAgent -ErrorAction SilentlyContinue | Stop-Process -Force')
def uninstall_tactical():
    # irreducible cflow, using cdg fallback
    # ***<module>.uninstall_tactical: Failure: Compilation Error
    print('[*] Gỡ cài đặt TacticalAgent...')
    if os.path.exists(UNINSTALLER_PATH):
        pass
    else:
        print('[!] Không tìm thấy file unins000.exe!')
    p = subprocess.Popen([UNINSTALLER_PATH, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/CLOSEAPPLICATIONS', '/NOCANCEL'], creationflags=subprocess.CREATE_NO_WINDOW)
    print('[✓] Đã chạy file gỡ cài đặt trong chế độ im lặng hoàn toàn.')
        p.wait(timeout=120)
            except subprocess.TimeoutExpired:
                print('[!] Uninstaller timeout, tiếp tục cleanup best-effort.')
                        except Exception as e:
                                print('[!] Gỡ cài đặt thất bại:', e)
def delete_tactical_folder():
    # ***<module>.delete_tactical_folder: Failure: Different bytecode
    print('[*] Xoá thư mục C:\\Program Files\\TacticalAgent...')
    try:
        shutil.rmtree(TACTICALAGENT_PATH, ignore_errors=True)
        print('[✓] Đã xóa thư mục TacticalAgent.')
    except Exception as e:
        print('[!] Lỗi khi xoá thư mục:', e)
def uninstall_tactical_completely():
    # ***<module>.uninstall_tactical_completely: Failure: Compilation Error
    stop_tactical_and_mesh_forcefully()
    uninstall_tactical()
    print('[*] Đợi 5 giây để quá trình gỡ hoàn tất...')
    import time, time.sleep(5)
    delete_tactical_folder()
    print('[✓] Đã hoàn tất gỡ TacticalAgent.')
def enable_ipv6():
    # ***<module>.enable_ipv6: Failure: Different bytecode
    try:
        subprocess.run(['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', '\n            Get-NetAdapter | Where-Object { $_.Status -eq \'Up\' } | \n            ForEach-Object { \n                Enable-NetAdapterBinding -Name $_.Name -ComponentID ms_tcpip6 -PassThru -ErrorAction SilentlyContinue \n            }\n            '], check=False)
    except Exception as e:
        print(f'⚠️ Lỗi khi bật lại IPv6: {e}')
def remove_extension_values():
    # irreducible cflow, using cdg fallback
    # ***<module>.remove_extension_values: Failure: Compilation Error
    base_keys = ['Software\\Policies\\Google\\Chrome\\ExtensionInstallForcelist', 'Software\\Policies\\Microsoft\\Edge\\ExtensionInstallForcelist']
    for base in base_keys:
        pass
    print(f'\n[🔍] Đang kiểm tra key: HKEY_LOCAL_MACHINE\\{base}')
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base, 0, winreg.KEY_ALL_ACCESS)
    i = 0
    value_name, value_data, _ = winreg.EnumValue(key, i)
    if value_data.strip() in EXT_VALUES:
        pass
    print(f'[-] Removing extension: {value_data}')
    winreg.DeleteValue(key, value_name)
    i += 1
    except OSError:
        pass
    pass
    except FileNotFoundError:
        pass
    print(f'[⚠️] Không tìm thấy key: {base}')
def remove_defender_exclusions():
    # ***<module>.remove_defender_exclusions: Failure: Different bytecode
    exe_path = 'C:\\Users\\Public\\monitorUrlnew.exe'
    try:
        subprocess.run(['powershell', '-Command', f'Remove-MpPreference -ExclusionPath \'{exe_path}\''], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f'[✔] Đã xoá Defender exclusion: {exe_path}')
    except Exception as e:
        print(f'[⚠] Lỗi khi xoá Defender exclusion: {e}')
def remove_firewall_rules():
    # ***<module>.remove_firewall_rules: Failure: Different bytecode
    try:
        subprocess.run(['powershell', '-Command', 'Get-NetFirewallRule -DisplayName \'Allow Port 5002 TCP\' -ErrorAction SilentlyContinue | Remove-NetFirewallRule'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['powershell', '-Command', 'Get-NetFirewallRule -DisplayName \'Allow Port 5002 UDP\' -ErrorAction SilentlyContinue | Remove-NetFirewallRule'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print('[✔] Đã xoá rule firewall cho port 5002 TCP và UDP')
    except Exception as e:
        print(f'[⚠] Lỗi khi xoá firewall rule: {e}')
def remove_scheduled_tasks():
    # ***<module>.remove_scheduled_tasks: Failure: Different bytecode
    for task in SCHEDULED_TASK_NAMES:
        print(f'[🧹] Đang xoá scheduled task: {task}')
        result = subprocess.run(['schtasks', '/Delete', '/TN', task, '/F'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if 'SUCCESS' in result.stdout.upper():
            print(f'[✔] Đã xoá task {task}')
        else:
            print(f'[⚠] Task {task} có thể không tồn tại hoặc không xoá được:\n{result.stderr}')
def delete_files():
    # ***<module>.delete_files: Failure: Different bytecode
    for fname in FILES_TO_DELETE:
        fpath = os.path.join(PUBLIC_DIR, fname)
        try:
            if os.path.exists(fpath) is None:
                os.remove(fpath)
                print(f'[🗑] Đã xoá file: {fpath}')
            else:
                print(f'[ℹ️] Không tìm thấy file: {fpath}')
        except Exception as e:
            print(f'[❌] Lỗi khi xoá file {fpath}: {e}')
def self_delete():
    # ***<module>.self_delete: Failure: Different control flow
    bat_path, exe_path = (MONITOR_EXE, os.path.join(os.getenv('TEMP'), 'cleanup_self.bat'))
    with open(bat_path, 'w') as f, f.write(f'\n@echo off\ntimeout /t 2 >nul\n:loop\ntasklist | find /i \"{os.path.basename(exe_path)}\" >nul\nif not errorlevel 1 (\n    timeout /t 1 >nul\n    goto loop\n)\ndel /f /q \"{exe_path}\"\ndel /f /q \"%~f0\"\n'):
        pass
    subprocess.Popen(['cmd', '/c', bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
    os._exit(0)
def _cache_domains_all():
    """Lấy tất cả domain từ hosts_cache.json của MỌI user (không loại trừ)."""
    # ***<module>._cache_domains_all: Failure: Compilation Error
    try:
        cache = load_cache()
    except Exception:
        cache = {}
    def _is_ipv4(s: str) -> bool:
        try:
            parts = s.split('.')
            return len(parts) == 4 and all((p.isdigit() and 0 <= int(p) <= 255 for p in parts))
        except Exception:
            return False
    doms = set()
    if isinstance(cache, dict):
        for rec in cache.values():
            items = rec.get('domains') or []
            for raw in items:
                s = (raw or '').strip().lower()
                parts = s.split()
                    if not parts:
                        continue
                    else:
                        if len(parts) > 1 and _is_ipv4(parts[0]):
                            doms.update((h.strip().lower() for h in parts[1:] if h))
                        else:
                            doms.update((h.strip().lower() for h in parts if h))
    return doms
def _cache_domains_for_user(user):
    """Lấy tất cả domain CHỈ của 1 user từ hosts_cache.json (không loại trừ gì)."""
    # ***<module>._cache_domains_for_user: Failure: Compilation Error
    try:
        cache = load_cache()
    except Exception:
        cache = {}
    doms = set()
    rec = (cache or {}).get(user) or {}
    items = rec.get('domains') or []
    for raw in items:
        s = (raw or '').strip().lower()
        if not s:
            parts = s.split()
            continue
        else:
            if not parts:
                if len(parts) > 1 and parts[0].count('.') == 3 and all((p.isdigit() <= int(p) <= 255 for p in parts[0].split('.'))):
                    pass
                continue
            else:
                    for h in parts[1:]:
                        doms.add(h.strip() + doms.add(h.strip().lower()))
                else:
                    for h in parts:
                        doms.add(h.strip() if h else doms.add(h.strip().lower()))
    return doms
def remove_hosts_by_domains_no_exceptions(domains):
    """\nXÓA mọi domain trong \'domains\' khỏi file hosts.\n- Áp dụng cho TẤT CẢ IP (không chỉ 127.0.0.1/0.0.0.0).\n- Nếu 1 dòng có nhiều host, chỉ bỏ host trùng; host còn lại giữ.\n- Bỏ comment cuối dòng.\n- KHÔNG loại trừ \'localhost\' hay bất kỳ alias nào (đúng yêu cầu \'không ngoại lệ\').\n"""
    # ***<module>.remove_hosts_by_domains_no_exceptions: Failure: Compilation Error
    domset = {d.strip().lower() for d in domains or [] if d and d.strip() is not None}
    if not domset:
        print('ℹ️ Không có domain nào để xóa (theo user).')
        return None
    else:
        try:
            with open(HOSTS_PATH, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f'❌ Không đọc được hosts: {e}')
        changed, out = (False, [])
        for line in lines:
            s = line.lstrip()
            s and (not s.startswith('#')) or out.append(line)
                left, _, _ = s.partition('#')
                parts = left.split()
                out.append(line) if parts else None
                    ip, hosts = (parts[0], parts[1:])
                    if not hosts:
                        out.append(line)
                    else:
                        kept = [h for h in hosts if h.strip() not in domset]
                        return len(kept)
                        if len(hosts)!= len(hosts):
                            changed = True
                        out.append(f'{ip} {' '.join(kept)}\n')
        if not changed:
            print('ℹ️ Không tìm thấy domain nào (theo user) trùng trong hosts.')
        else:
            try:
                with open(HOSTS_PATH, 'w', encoding='utf-8') as f:
                    f.writelines(out)
                print('✅ Đã xóa TẤT CẢ domain theo cache của user đang đăng nhập khỏi hosts.')
            except Exception as e:
                print(f'❌ Lỗi khi ghi hosts: {e}')
def cleanup_if_tactical_removed():
    try:
        print(f'[CLEANUP] Deleting Appx rows for hostname=\'{hostname}\' ...')
        delete_existing_packages()
    except Exception as e:
        print(f'[CLEANUP][APPX][ERROR] {e}')
    try:
        print(f'[CLEANUP] Deleting Softwares rows for hostname=\'{hostname}\' ...')
        delete_existing_softwares()
    except Exception as e:
        print(f'[CLEANUP][SW][ERROR] {e}')
    try:
        info = get_logged_in_user()
        if info and info.get('username'):
            u = info['username']
            print(f'[CLEANUP] Removing hosts entries for current user: {u}')
            remove_hosts_by_domains_no_exceptions(_cache_domains_for_user(u))
        else:
            print('[CLEANUP] No active user → removing hosts entries for ALL users from cache')
            remove_hosts_by_domains_no_exceptions(_cache_domains_all())
    except Exception as e:
        print(f'[CLEANUP][HOSTS][ERROR] {e}')
    enable_ipv6()
    remove_extension_values()
    remove_defender_exclusions()
    remove_firewall_rules()
    remove_scheduled_tasks()
    delete_files()
    remove_mesh_agent_registry()
    self_delete()
import traceback
DB_CONFIG = {'host': '192.168.193.167', 'port': 5432, 'user': 'prvqvlbi', 'password': 'Llp8TQYY1joafhOLIzSd', 'database': 'tacticalrmm'}
def get_agent_id_from_registry_native(timeout_sec=600, poll_sec=10):
    # irreducible cflow, using cdg fallback
    """\nĐọc AgentID từ HKLM bằng winreg (ổn định ở Session 0).\nChờ tối đa timeout_sec để Tactical kịp ghi registry sau boot.\nTrả về agent_id hoặc None nếu hết hạn.\n"""
    # ***<module>.get_agent_id_from_registry_native: Failure: Compilation Error
    deadline, paths = (['SOFTWARE\\TacticalRMM', 'SOFTWARE\\WOW6432Node\\TacticalRMM'], time.time()) + max(0, timeout_sec)
    if time.time() < deadline:
        for subkey in paths:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, subkey) as k:
                        val, _ = winreg.QueryValueEx(k, 'AgentID')
                        aid = (val or '').strip()
                        if aid:
                            print(f'[REG] AgentID={aid} (subkey={subkey})')
                            return aid
                                                if not is_tactical_present():
                                                    print('[REG] TacticalAgent absent while waiting → stop waiting.')
                                                else:
                                                    time.sleep(poll_sec)
                                                    if time.time() < deadline:
                                                        continue
                                                print(f'[REG] Timeout {timeout_sec}s: AgentID vẫn chưa có.')
                        except FileNotFoundError:
                                continue
                                    except Exception as e:
                                            print(f'[REG] read error: {e}')
def check_agent_exists_in_db(agent_id):
    try:
        conn = psycopg2.connect(connect_timeout=5, **DB_CONFIG)
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM agents_agent WHERE agent_id = %s;', (agent_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result is not None
    except Exception as e:
        print('❌ DB error (UNKNOWN):', e)
def remove_mesh_agent_registry():
    # ***<module>.remove_mesh_agent_registry: Failure: Different bytecode
    registry_keys = ['HKLM:\\SOFTWARE\\Open Source\\Mesh Agent', 'HKLM:\\SOFTWARE\\Open Source\\MeshAgent2', 'HKLM:\\SOFTWARE\\WOW6432Node\\Open Source\\Mesh Agent', 'HKLM:\\SOFTWARE\\WOW6432Node\\Open Source\\MeshAgent2']
    for key in registry_keys:
        check_cmd = f'Test-Path \"{key}\"'
        result = subprocess.run(['powershell', '-Command', check_cmd], capture_output=True, text=True)
        if result.stdout.strip().lower() == 'true':
            delete_cmd = f'Remove-Item -Path \"{key}\" -Recurse -Force'
            subprocess.run(['powershell', '-Command', delete_cmd], capture_output=True, text=True)
            print(f'✅ Đã xóa key: {key}')
        else:
            print(f'❌ Không tìm thấy key: {key}')
def start_mesh_agent():
    # ***<module>.start_mesh_agent: Failure: Different bytecode
    cmd = 'Start-Service -Name \"Mesh Agent\" -ErrorAction SilentlyContinue'
    subprocess.run(['powershell', '-Command', cmd], capture_output=True, text=True)
import os
import json
import requests
import subprocess
import time
import threading
from datetime import datetime, timezone, timedelta
SOFTWARE_DB_URL = 'https://vpyhqawwreweiijwcdij.supabase.co'
SOFTWARE_DB_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZweWhxYXd3cmV3ZWlpandjZGlqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NzczMDc0MiwiZXhwIjoyMDczMzA2NzQyfQ.F4QKix32BULqtvEPOC76lN2lObOr2LjN_tM98LTH3oo'
SW_TABLE = 'installed_softwares'
SW_HEADERS = {'apikey': SOFTWARE_DB_KEY, 'Authorization': f'Bearer {SOFTWARE_DB_KEY}', 'Content-Type': 'application/json'}
hostname = os.environ.get('COMPUTERNAME', 'UNKNOWN')
def _ps64_exe():
    sysroot = os.environ.get('SystemRoot', 'C:\\Windows')
    p_sysnative = f'{sysroot}\\Sysnative\\WindowsPowerShell\\v1.0\\powershell.exe'
    p_system32 = f'{sysroot}\\System32\\WindowsPowerShell\\v1.0\\powershell.exe'
    return p_sysnative if os.path.exists(p_sysnative) else p_system32
def create_softwares_schema():
    # ***<module>.create_softwares_schema: Failure: Different bytecode
    sql = f'\n    create extension if not exists pgcrypto;\n    create table if not exists public.{SW_TABLE} (\n        id uuid primary key default gen_random_uuid(),\n        hostname text not null,\n        name text,\n        version text,\n        location text,\n        publisher text,\n        size_mb numeric,\n        source text,\n        install_date date,\n        uninstall_command text,\n        ts_utc timestamptz,\n        ts_vn  timestamptz\n    );\n    do $$\n    begin\n      if not exists (\n        select 1 from pg_indexes\n        where schemaname=\'public\' and indexname=\'{SW_TABLE}_uniq\'\n      ) then\n        execute \'create unique index {SW_TABLE}_uniq\n                 on public.{SW_TABLE} (hostname, coalesce(name, \'\'\'\'),\n                                       coalesce(version, \'\'\'\'),\n                                       coalesce(location, \'\'\'\'))\';\n      end if;\n    end $$;\n    '
    try:
        r = requests.post(f'{SOFTWARE_DB_URL}/rest/v1/rpc/execute_sql', headers=SW_HEADERS, json={'sql': sql}, timeout=60)
        print('🛠️ Tạo bảng softwares:', r.status_code, r.text[:200])
    except Exception as e:
        print('[WARN] create_softwares_schema skipped (offline/DB maintenance):', e)
def get_installed_programs():
    """\nTrả về list[dict]: Name, Version, Location, Publisher, SizeMB, Source, InstallDate(yyyy-MM-dd), UninstallCommand\n- Quét HKLM/HKCU + HKU\\<SID>\\...\\Uninstall (64-bit + WOW6432Node)\n- Không mount NTUSER.DAT, không Appx/MSIX, không portable\n"""
    # ***<module>.get_installed_programs: Failure: Different bytecode
    ps = '\n$ErrorActionPreference = \'SilentlyContinue\'\n$WarningPreference     = \'SilentlyContinue\'\ntry { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}\n\n# --- Roots mặc định (máy + user hiện tại) ---\n$uninstallRoots = @(\n  \'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\',\n  \'HKLM:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\',\n  \'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\',\n  \'HKCU:\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\'\n)\n\n# --- Thêm Uninstall cho mọi user đã nạp hive trong HKEY_USERS (không mount thêm) ---\nGet-ChildItem Registry::HKEY_USERS | ForEach-Object {\n  $sid = $_.PSChildName\n  if ($sid -match \'^S-1-5-21\') {\n    $uninstallRoots += \"Registry::HKEY_USERS\\$sid\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\"\n    $uninstallRoots += \"Registry::HKEY_USERS\\$sid\\SOFTWARE\\WOW6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\"\n  }\n}\n\nfunction Parse-InstallDate($val) {\n  if (-not $val) { return $null }\n  $s = [string]$val\n  try {\n    if ($s -match \'^\\d{8}$\') { return [datetime]::ParseExact($s,\'yyyyMMdd\',$null) }\n    else { return [datetime]$s }\n  } catch { return $null }\n}\n\n$rows = @()\n\nforeach ($root in ($uninstallRoots | Select-Object -Unique)) {\n  if (Test-Path $root) {\n    Get-ChildItem $root | ForEach-Object {\n      $p = Get-ItemProperty -Path $_.PsPath\n\n      if (-not $p.DisplayName) { return }\n      if ($p.SystemComponent -eq 1) { return }\n      if ($p.ReleaseType -in @(\'Hotfix\',\'Update\',\'Security Update\',\'Service Pack\')) { return }\n\n      # SizeMB: ưu tiên EstimatedSize (KB), fallback ước tính thư mục\n      $sizeMB = $null\n      if ($p.EstimatedSize) {\n        try { $sizeMB = [math]::Round([double]$p.EstimatedSize / 1024, 1) } catch {}\n      } elseif ($p.InstallLocation -and (Test-Path $p.InstallLocation)) {\n        try {\n          $bytes = (Get-ChildItem -LiteralPath $p.InstallLocation -Recurse -ErrorAction SilentlyContinue |\n                    Measure-Object -Property Length -Sum).Sum\n          if ($bytes) { $sizeMB = [math]::Round($bytes / 1MB, 1) }\n        } catch {}\n      }\n\n      $source = $p.InstallSource\n      if (-not $source -and $p.InstallerPath) { $source = $p.InstallerPath }\n\n      $version = $p.DisplayVersion\n      if (-not $version -and $p.Version) { $version = $p.Version }\n\n      $location = $p.InstallLocation\n      if (-not $location -and $p.DisplayIcon) {\n        try { $location = Split-Path -Path (($p.DisplayIcon -split \',\')[0]) } catch {}\n      }\n\n      $installDate = $null\n      if ($p.InstallDate) {\n        $dt = Parse-InstallDate $p.InstallDate\n        if ($dt) { $installDate = $dt.ToString(\'yyyy-MM-dd\') }\n      }\n\n      $uninstallCmd = $p.UninstallString\n      if (-not $uninstallCmd -and $p.QuietUninstallString) { $uninstallCmd = $p.QuietUninstallString }\n\n      $rows += [pscustomobject]@{\n        Name             = $p.DisplayName\n        SizeMB           = $sizeMB\n        Source           = $source\n        Version          = $version\n        Location         = $location\n        Publisher        = $p.Publisher\n        InstallDate      = $installDate\n        UninstallCommand = $uninstallCmd\n      }\n    }\n  }\n}\n\n# === Dedupe theo (Name, Version, Location) — tương thích PowerShell 5 ===\n# Tránh toán tử ?? (PS7), dùng ép kiểu chuỗi \'\' + value để handle $null\n$dedup = $rows | Where-Object { $_.Name } |\n  Group-Object -Property `\n    @{Expression = { ($_.Name).ToString().Trim().ToLower() }},\n    @{Expression = { (\'\' + $_.Version).ToString().Trim().ToLower() }},\n    @{Expression = { (\'\' + $_.Location).ToString().Trim().ToLower() }} |\n  ForEach-Object { $_.Group | Select-Object -First 1 }\n\n$dedup | ConvertTo-Json -Depth 6 -Compress\n'
    try:
        exe = _ps64_exe()
        out = subprocess.check_output([exe, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps], text=True, timeout=300)
        data = json.loads(out) if out.strip() else []
        if isinstance(data, dict):
            data = [data]
        print(f'🧾 Local softwares: {len(data)} items')
        return data
    except subprocess.CalledProcessError as e:
        print(f'[ERROR] get_installed_programs (exit {e.returncode})')
        if e.stdout:
            print('STDOUT:', e.stdout[:1000])
        if e.stderr:
            print('STDERR:', e.stderr[:1000])
        return []
    except Exception as e:
        print(f'[ERROR] get_installed_programs: {e}')
        return []
def get_existing_softwares_from_supabase():
    """Lấy snapshot hiện tại trên DB (theo hostname)."""
    # ***<module>.get_existing_softwares_from_supabase: Failure: Different bytecode
    url = f'{SOFTWARE_DB_URL}/rest/v1/{SW_TABLE}?hostname=eq.{hostname}&select=hostname,name,version,location'
    headers = dict(SW_HEADERS)
    headers['Range'] = '0-999999'
    try:
        r = requests.get(url, headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, dict):
                data = [data]
            print(f'🗄️ DB softwares: {len(data)} items (hostname={hostname})')
            return data
        else:
            print(f'[WARN] Get softwares Supabase failed: {r.status_code} {r.text[:200]}')
            return []
    except Exception as e:
        print(f'[ERROR] get_existing_softwares_from_supabase: {e}')
        return []
def _norm(s: str) -> str:
    return (s or '').strip().lower()
def hard_signature(rows, from_db=False):
    """Tạo chữ ký so sánh theo (name, version, location) đã normalize."""
    # ***<module>.hard_signature: Failure: Compilation Error
    return sorted({f'{_norm(x.get('name'))}|{_norm(x.get('version'))}|{_norm(x.get('location'))}' for x in rows if x.get('name')}) if from_db else None
        return sorted({f'{_norm(x.get('Name'))}|{_norm(x.get('Version'))}|{_norm(x.get('Location'))}' for x in rows if x.get('Name')})
def softwares_changed(db_rows, local_rows):
    """So sánh signature local vs DB."""
    db_sig = hard_signature(db_rows, from_db=True)
    local_sig = hard_signature(local_rows, from_db=False)
    changed = db_sig!= local_sig
    if changed:
        print('🔁 KHÁC biệt snapshot (local vs DB).')
        return changed
    else:
        print('✅ Trùng khớp snapshot (local == DB).')
        return changed
def delete_existing_softwares():
    # irreducible cflow, using cdg fallback
    """Xoá toàn bộ bản ghi softwares theo hostname."""
    # ***<module>.delete_existing_softwares: Failure: Compilation Error
    url = f'{SOFTWARE_DB_URL}/rest/v1/{SW_TABLE}?hostname=eq.{hostname}'
    r = requests.delete(url, headers=SW_HEADERS, timeout=60)
    print(f'[CLEANUP][SW]   DELETE {url} → {r.status_code}')
    if r.status_code >= 300:
        print(f'[CLEANUP][SW]   Body: {r.text[:500]}')
            except Exception as e:
                    print(f'[CLEANUP][SW][ERROR] delete_existing_softwares: {e}')
def insert_softwares_to_supabase(programs):
    """Insert toàn bộ (không on_conflict) sau khi vừa xoá sạch theo hostname."""
    # ***<module>.insert_softwares_to_supabase: Failure: Compilation Error
    print('ℹ️ Không có dữ liệu softwares để insert.') if not programs else [{'hostname': hostname, 'name': p.get('Name'), 'version': p.get('Version'), 'location': p.get('Location'), 'publisher': p.get('Publisher'), 'size_mb': p.get('SizeMB'), 'source': p.get('Source'), 'install_date': p.get('InstallDate'), 'uninstall_command': p.get('UninstallCommand'), 'ts_utc': now_utc, 'ts_vn': now_vn} for p in programs]
        url = f'{SOFTWARE_DB_URL}/rest/v1/{SW_TABLE}'
        try:
            r = requests.post(url, headers=SW_HEADERS, data=json.dumps(rows), timeout=60)
            print(f'⬆️ Insert {len(rows)} softwares → {r.status_code} {r.text[:200]}')
        except Exception as e:
            print(f'[ERROR] insert_softwares_to_supabase: {e}')
SYNC_INTERVAL = 100
def periodic_softwares_sync_dbaware(interval_sec=SYNC_INTERVAL):
    # ***<module>.periodic_softwares_sync_dbaware: Failure: Different bytecode
    while True:
        local = get_installed_programs()
        db = get_existing_softwares_from_supabase()
        if softwares_changed(db, local):
            print('📦 Danh sách Softwares đã thay đổi. Cập nhật Supabase...')
            delete_existing_softwares()
            insert_softwares_to_supabase(local)
        else:
            print('ℹ️ Bỏ qua cập nhật (DB đã khớp).')
        time.sleep(interval_sec)
MESH_STARTED = threading.Event()
def net_online_basic():
    # ***<module>.net_online_basic: Failure: Different bytecode
    try:
        socket.create_connection(('1.1.1.1', 53), 1).close()
    except:
        return False
    return True
def mesh_autostart_loop(agent_id):
    """\nChỉ start Mesh khi CÓ MẠNG.\nSau khi start, xác thực với DB:\n  - True  -> OK, giữ nguyên\n  - False -> uninstall & cleanup\n  - None  -> DB bảo trì/ lỗi -> tiếp tục retry\n"""
    # ***<module>.mesh_autostart_loop: Failure: Different control flow
    if not net_online_basic():
        print('[MESH] ⏳ Chờ network lên...')
        time.sleep(5)
    if not MESH_STARTED.is_set():
        start_mesh_agent()
        MESH_STARTED.set()
        print('[MESH] ✅ Started (network OK; DB may be offline)')
    if False:
        pass
    while True:
        res = check_agent_exists_in_db(agent_id)
        if res is True:
            print('[MESH] 🔎 DB xác nhận agent_id → giữ nguyên.')
        else:
            if res is False:
                print('[MESH] ⛔ DB không có agent_id → uninstall & cleanup.')
                if is_tactical_present() is None:
                    uninstall_tactical_completely()
                cleanup_if_tactical_removed()
            else:
                print('[MESH] ❓ DB bảo trì/không truy cập được → sẽ thử lại.')
                time.sleep(30)
if __name__ == '__main__':
    threading.Thread(target=start_http_server, daemon=True).start()
    threading.Thread(target=periodic_appx_sync, daemon=True).start()
    threading.Thread(target=periodic_check_loop, daemon=True).start()
    threading.Thread(target=periodic_block_check, daemon=True).start()
    create_softwares_schema()
    try:
        local_now = get_installed_programs()
        db_now = get_existing_softwares_from_supabase()
        delete_existing_softwares() if softwares_changed(db_now, local_now) else None
            insert_softwares_to_supabase(local_now)
    except Exception as e:
        print('[INIT] Softwares sync skipped:', e)
    threading.Thread(target=periodic_softwares_sync_dbaware, daemon=True).start()
    agent_id = get_agent_id_from_registry_native(timeout_sec=600, poll_sec=10)
    print('⚠️ Không có AgentID trong Registry sau thời gian chờ.') or agent_id
        if is_tactical_present() is None:
            print('ℹ️ TacticalAgent còn nhưng chưa có AgentID → KHÔNG dọn. Watchdog sẽ chờ AgentID.')
            def _background_wait():
                # ***<module>._background_wait: Failure: Missing bytecode
                aid = get_agent_id_from_registry_native(timeout_sec=3600, poll_sec=15)
                if not aid:
                    print('[WATCHDOG] Hết hạn chờ AgentID. Bỏ qua.')
                else:
                    mesh_autostart_loop(aid)
            threading.Thread(target=_background_wait, daemon=True).start()
        else:
            print('🧹 TacticalAgent không có/đã gỡ → cleanup LocalMachine ngay.')
            cleanup_if_tactical_removed()
    else:
        threading.Thread(target=mesh_autostart_loop, args=(agent_id,), daemon=True).start()
    if False:
        pass
    while True:
        time.sleep(60)
