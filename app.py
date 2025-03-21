import os
import shutil
import subprocess
import threading
import requests
import json
import time
import base64
from flask import Flask

app = Flask(__name__)

# 设置环境变量
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # 脚本所在目录
FILE_PATH = '/tmp'  # 使用/tmp目录进行写入操作
PROJECT_URL = os.environ.get('URL', '') # 填写项目分配的url可实现自动访问
INTERVAL_SECONDS = int(os.environ.get("TIME", 120))                   # 访问间隔时间
UUID = os.environ.get('UUID', 'abe2f2de-13ae-4f1f-bea5-d6c881ca3888')
NEZHA_SERVER = os.environ.get('NEZHA_SERVER', '')
NEZHA_PORT = os.environ.get('NEZHA_PORT', '')
NEZHA_KEY = os.environ.get('NEZHA_KEY', '')
# 使用Leapcell分配的域名
DOMAIN = os.environ.get('DOMAIN', 'lpcl-gyxzhao9316-r79shlmi.leapcell.dev')
NAME = os.environ.get('NAME', 'Vls')
PORT = int(os.environ.get('PORT', 8080))            # http服务端口
VPORT = int(os.environ.get('VPORT', 8080))          # 节点端口与HTTP端口相同

print(f"Script directory: {SCRIPT_DIR}")
print(f"Using writable directory: {FILE_PATH}")
print(f"Using domain: {DOMAIN}")
print(f"HTTP port: {PORT}, Node port: {VPORT}")

# 清理旧文件
paths_to_delete = ['list.txt','sub.txt']
for file in paths_to_delete:
    file_path = os.path.join(FILE_PATH, file)
    try:
        os.unlink(file_path)
        print(f"{file_path} has been deleted")
    except Exception as e:
        print(f"Skip Delete {file_path}")

# 生成xray配置文件
def generate_config():
    config = {
        "log": {"access": "/dev/null", "error": "/dev/null", "loglevel": "none"},
        "inbounds": [
            {
                "port": VPORT,
                "protocol": "vless",
                "settings": {
                    "clients": [{"id": UUID}],
                    "decryption": "none"
                },
                "streamSettings": {
                    "network": "ws",
                    "wsSettings": {
                        "path": "/vless"
                    }
                }
            }
        ],
        "outbounds": [
            {"protocol": "freedom"}
        ]
    }

    with open(os.path.join(FILE_PATH, 'config.json'), 'w', encoding='utf-8') as config_file:
        json.dump(config, config_file, ensure_ascii=False, indent=2)
    print("Config file generated successfully")

# 复制可执行文件到可写目录
def copy_executables():
    for file in ['swith', 'web']:
        source_path = os.path.join(SCRIPT_DIR, file)
        dest_path = os.path.join(FILE_PATH, file)
        
        if os.path.exists(source_path):
            try:
                shutil.copy2(source_path, dest_path)
                print(f"Copied {file} to {dest_path}")
            except Exception as e:
                print(f"Error copying {file}: {e}")
        else:
            print(f"Source file {source_path} not found")

# 授予文件权限
def authorize_files(file_paths):
    new_permissions = 0o775

    for file_path in file_paths:
        absolute_file_path = os.path.join(FILE_PATH, file_path)
        try:
            os.chmod(absolute_file_path, new_permissions)
            print(f"Empowerment success for {absolute_file_path}: {oct(new_permissions)}")
        except Exception as e:
            print(f"Empowerment failed for {absolute_file_path}: {e}")

# 生成订阅链接
def generate_links():
    try:
        ISP = "Unknown"
    except Exception as e:
        print(f"Error getting meta info: {e}")
        ISP = "Unknown"
    
    list_txt = f"""vless://{UUID}@{DOMAIN}:{VPORT}?encryption=none&security=&type=ws&host={DOMAIN}&path=%2Fvless#{NAME}-{ISP}"""
    
    with open(os.path.join(FILE_PATH, 'list.txt'), 'w', encoding='utf-8') as list_file:
        list_file.write(list_txt)

    sub_txt = base64.b64encode(list_txt.encode('utf-8')).decode('utf-8')
    with open(os.path.join(FILE_PATH, 'sub.txt'), 'w', encoding='utf-8') as sub_file:
        sub_file.write(sub_txt)
        
    try:
        with open(os.path.join(FILE_PATH, 'sub.txt'), 'rb') as file:
            sub_content = file.read()
        print(f"\nSubscription content: {sub_content.decode('utf-8')}")
    except FileNotFoundError:
        print(f"sub.txt not found")
    
    print(f'{FILE_PATH}/sub.txt saved successfully')

# 运行服务
def run_services():
    # 复制可执行文件到可写目录
    copy_executables()
    
    # 授权可执行文件
    files_to_authorize = ['swith', 'web']
    authorize_files(files_to_authorize)

    # 运行哪吒监控
    if NEZHA_SERVER and NEZHA_PORT and NEZHA_KEY:
        NEZHA_TLS = '--tls' if NEZHA_PORT == '443' else ''
        command = f"nohup {os.path.join(FILE_PATH, 'swith')} -s {NEZHA_SERVER}:{NEZHA_PORT} -p {NEZHA_KEY} {NEZHA_TLS} >/dev/null 2>&1 &"
        try:
            subprocess.run(command, shell=True, check=True)
            print('swith is running')
        except subprocess.CalledProcessError as e:
            print(f'swith running error: {e}')
    else:
        print('NEZHA variable is empty, skip running')

    # 运行xray服务
    try:
        # 直接运行web服务，不使用pkill（因为它可能不存在）
        command = f"nohup {os.path.join(FILE_PATH, 'web')} -c {os.path.join(FILE_PATH, 'config.json')} >/dev/null 2>&1 &"
        subprocess.run(command, shell=True)
        time.sleep(1)  # 给服务启动一点时间
        print('web is running')
    except Exception as e:
        print(f'web running error: {e}')

# 启动服务器
def start_server():
    generate_config()  # 先生成配置文件
    generate_links()   # 然后生成链接文件
    run_services()     # 最后运行服务
    print('App is running')
    print('Thank you for using this script, enjoy!')

# 先执行初始化
start_server()

# Flask路由
@app.route('/')
def home():
    return 'Hello, world! Server is running.'

@app.route('/sub')
def sub():
    try:
        with open(os.path.join(FILE_PATH, 'sub.txt'), 'r') as file:
            content = file.read()
        return content, 200, {'Content-Type': 'text/plain; charset=utf-8'}
    except FileNotFoundError:
        return 'Error reading file', 500

@app.route('/kaithheathcheck')
@app.route('/kaithhealthcheck')
def healthcheck():
    return 'OK', 200

@app.route('/status')
def status():
    # 检查web进程是否运行
    web_running = subprocess.run("ps -ef | grep web | grep -v grep", shell=True, capture_output=True).returncode == 0
    # 检查swith进程是否运行
    swith_running = subprocess.run("ps -ef | grep swith | grep -v grep", shell=True, capture_output=True).returncode == 0
    
    status_info = {
        "web_running": web_running,
        "swith_running": swith_running,
        "domain": DOMAIN,
        "port": VPORT,
        "uuid": UUID
    }
    
    return f"""
    <html>
    <head><title>Status</title></head>
    <body>
        <h1>Status</h1>
        <pre>{json.dumps(status_info, indent=2)}</pre>
        <h2>Environment</h2>
        <pre>{json.dumps(dict(os.environ), indent=2)}</pre>
    </body>
    </html>
    """

# 自动访问项目页面
has_logged_empty_message = False

def visit_project_page():
    try:
        if not PROJECT_URL or not INTERVAL_SECONDS:
            global has_logged_empty_message
            if not has_logged_empty_message:
                print("URL or TIME variable is empty, Skipping visit web")
                has_logged_empty_message = True
            return

        response = requests.get(PROJECT_URL)
        response.raise_for_status() 
        print("Page visited successfully")
    except requests.exceptions.RequestException as error:
        print(f"Error visiting project page: {error}")

# 启动Flask应用
if __name__ == "__main__":
    # 启动一个线程定期访问项目页面
    def periodic_visit():
        while True:
            visit_project_page()
            time.sleep(INTERVAL_SECONDS)
    
    visit_thread = threading.Thread(target=periodic_visit)
    visit_thread.daemon = True
    visit_thread.start()
    
    # 启动Flask应用
    app.run(host='0.0.0.0', port=PORT, debug=False)
