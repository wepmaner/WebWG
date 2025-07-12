import json
import os
import subprocess
from base64 import b64encode
import ipaddress
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
import re
import qrcode
import uuid
from logger import get_logger
from dotenv import load_dotenv
load_dotenv()
log = get_logger("wg")
IP = os.getenv("IP")
PORT = os.getenv("PORT")
endpoint = f"{IP}:{PORT}"
log.debug(IP)
TEMPLATE = """[Interface]
PrivateKey = {priv}
Address = {addr}
ListenPort = {port}
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -t nat -A POSTROUTING -o enp0s3 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -t nat -D POSTROUTING -o enp0s3 -j MASQUERADE

{peers}
"""

PEER_BLOCK = """[Peer]
PublicKey = {pub}
AllowedIPs = {allowed}

"""

def generate_wg_qr(username: str) -> str:
    """
    Генерирует QR‑код из текста WireGuard‑конфига и сохраняет его в PNG.
    :param config_text: строка с содержимым .conf
    :param png_path: куда сохранить изображение
    """
    config_text = createUserConfig(username)
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(config_text)
    qr.make(fit=True)

    img = qr.make_image()
    png_path = f'static/img/{uuid.uuid4()}.png'
    img.save(png_path)
    return png_path


def run_command(cmd, capture_output=True, text=True, check=True):
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture_output,
            text=text,
            check=check
        )
        if result.stdout:
            print("Вывод команды:")
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении команды: {' '.join(cmd)}")
        if e.stdout:
            print("stdout:")
            print(e.stdout)
        if e.stderr:
            print("stderr:")
            print(e.stderr)
    except Exception as e:
        print(f"Произошла неожиданная ошибка: {e}")

def load_config(path="peers.json") -> dict:
    '''Загрузка данных пиров'''
    with open(path) as f:
        return json.load(f)

def render(config):
    # сгенерить текст для всех пиров
    peers_txt = []
    for p in config["peers"]:
        if p['enable']:
            peers_txt.append(PEER_BLOCK.format(
                pub=p["public_key"],
                allowed=p["allowed_ips"]
            ))
    return TEMPLATE.format(
        priv=config["interface"]["private_key"],
        addr=config["interface"]["address"],
        port=config["interface"]["listen_port"],
        peers="\n".join(peers_txt)
    )


def save_config(state, dest="/etc/wireguard/wg0.conf"):
    txt = render(state)
    with open(dest,"w") as f:
        f.write(txt)
    run_command(["sudo", "bash", "-c", "wg syncconf wg0 <(wg-quick strip wg0)"])
    with open('peers.json', 'w') as f:
        return json.dump(state,f)

# def create_backup():
#     with open('peers.json') as file:
#         server_info = json.load(file)
#     backup_json = {"server_info":server_info}
#     for peer in server_info['peers']:
#         username = peer['username']

#     with open('backup.json','w',encoding='utf8') as file:
#         json.dump(backup_json,file)
    


def restore_server(server_config):
    with open('peers.json','w',encoding='utf8') as file:
        json.dump(server_config,file)



def keygen():
    private = X25519PrivateKey.generate()

    return (
        b64encode(
            private.private_bytes(
                serialization.Encoding.Raw,
                serialization.PrivateFormat.Raw,
                serialization.NoEncryption(),
            ),
        ).decode(),
        b64encode(
            private.public_key().public_bytes(
                serialization.Encoding.Raw,
                serialization.PublicFormat.Raw,
            ),
        ).decode(),
    )

def getAllowedIp(network = '10.0.0.0/24'):
    '''Поиск свободного ip для пира'''
    existing_ips = {"10.0.0.1"}
    try:
        config = load_config()
        peers = config['peers']
    except FileNotFoundError:
        return "10.0.0.2"
    for peer in peers:
        allowed_ips = peer['allowed_ips']
        existing_ips.add(allowed_ips)

    # Ищем следующий свободный IP
    net = ipaddress.ip_network(network)
    for ip in net.hosts():
        ip_str = str(ip)
        if ip_str not in existing_ips:  # не использовать адрес сервера
            return ip_str

    raise Exception("Свободных IP-адресов больше нет!")

def parse_wireguard_peers(text):
    users = {}
    peers = []
    config = load_config() 
    peers_info = {peer['public_key']:[peer['username'],peer['enable'],peer['allowed_ips']] for peer in config['peers'] if peer }

    # Разбиваем на куски по каждому peer
    peer_blocks = text.split('peer: ')
    peer_blocks = [block.strip() for block in peer_blocks if block.strip()][1:]

    for block in peer_blocks:
        lines = block.splitlines()
        peer_public_key = lines[0].strip()
        peer_info = peers_info.get(peer_public_key,["Unknown",False])
        data = {
            "name": peer_info[0],
            "allowedIPs": peer_info[2],
            "isOnline": False,
            "isEnable": peer_info[1],
            "latestHandshake": "",
            "received": "",
            "send": "",
        }
        

        for line in lines[1:]:
            if "latest handshake:" in line:
                handshake = line.split(":", 1)[1].strip()
                data["latestHandshake"] = handshake
                data["isOnline"] = handshake.lower() != "never"
            if "transfer:" in line:
                parts = re.findall(r'(\d+\s\w+)', line)
                if len(parts) == 2:
                    data["received"] = parts[0]
                    data["send"] = parts[1]

        users[peer_public_key] = data

    for peer in config['peers']:
        if peer['public_key'] in users:
            peers.append(users[peer['public_key']])
        else:
            peers.append({
            "name": peer["username"],
            "allowedIPs": peer["allowed_ips"],
            "isOnline": False,
            "isEnable": False,
            "latestHandshake": "",
            "received": "",
            "send": "",
        })

    return peers


def createUserConfig(username:str,network = '10.0.0.0/24')->str:
    server_config = load_config()
    log.debug(f'createUserConfig - username:{username}')
    for peer in server_config['peers']:
        log.debug(f"createUserConfig - peer:{peer} - {peer['username'] == username}")
    peer = next((peer for peer in server_config['peers'] if peer['username'] == username), None)
    log.debug(f'createUserConfig - peer:{peer}')
    server_public_key = getServerPublicKey()
    config = f"""
[Interface]
PrivateKey = {peer['private_key']}
Address = {peer['allowed_ips']}/32
DNS = 8.8.8.8

[Peer]
PublicKey = {server_public_key}
Endpoint = {endpoint}
AllowedIPs = {network}
PersistentKeepalive = 25""".strip()
    return config

def isActive():
    result = subprocess.run(
        ["sudo", "systemctl", "is-active", "wg-quick@wg0"],
        capture_output=True,
        text=True
    )
    if result.stdout == 'active\n':
        return True
    return False
def toggle():
    '''Включение отключение VPN сервера'''
    if isActive():
        commands = ["sudo", "systemctl", "stop", "wg-quick@wg0"]
        action = 'stop'
    else:
        commands = ["sudo", "systemctl", "start", "wg-quick@wg0"]
        action = 'start'
    subprocess.run(
       commands,
        capture_output=True,
        text=True
    )
    return action

def getServerPublicKey() -> str:
    '''Получение публичного ключа сервера'''
    result = subprocess.run(
        ["sudo", "wg", "show", "wg0", "public-key"],
        capture_output=True,
        text=True
    )
    return result.stdout

def peer_add(username):
    """Добавление пользователя"""
    config = load_config()
    peer = next((peer for peer in config['peers'] if peer['username'] == username), None)
    if peer is not None:
        return False, ''
    private_key, public_key = keygen()
    allowed_ips = getAllowedIp()
    
    config["peers"].append({"username":username,"private_key":private_key,"public_key":public_key,"allowed_ips":allowed_ips,'enable':True})
    save_config(config)
    return True, allowed_ips

def peer_del(username):
    """Удаление пользователя"""

    config = load_config()
    peers = [peer for peer in config['peers'] if peer['username'] != username]
    config["peers"] = peers
    save_config(config)


def changeUserStatus(username):
    """Включение/отключение пользователя"""
    config = load_config()
    peer = next((peer for peer in config['peers'] if peer['username'] == username))
    if peer['enable']:
        isEnable = False
    else:
        isEnable = True
    peer['enable'] = isEnable
    save_config(config)
    return isEnable


def getInfo():
    """Информация о сервере и пользователях"""
    result = subprocess.run(
        ["sudo", "wg", "show"],
        capture_output=True, 
        text=True
    )
    print(result.stdout)
    users = parse_wireguard_peers(result.stdout)
    serverenable = isActive()

    return {
            "status": "success",
            "serverenable": serverenable,
            "users": users
        }

def editUser(username, user):
    """Отредактировать пользователя"""
    config = load_config()
    peer = next((peer for peer in config['peers'] if peer['username'] == username))
    if user.new_username:
        peer['username'] = user.new_username
    if  user.allowedIps:
        peer['allowed_ips'] = user.allowedIps
    save_config(config)

# args = sys.argv
# if args[1] == 'create':
#     peer_add(args[2])
# elif args[1] == 'delete':
#     peer_del(args[2])
