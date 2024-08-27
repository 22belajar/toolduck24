import requests
import json
import os
import time
import gzip
import zlib
import io
import brotli
import zstandard as zstd
import websocket

ws_game_url = 'wss://game-ws-api.duckcoop.xyz/'
get_balance_url = "https://api.duckcoop.xyz/reward/get"
claim_checkin_url = "https://api.duckcoop.xyz/checkin/claim"
partner_mission_list_url = "https://api.duckcoop.xyz/partner-mission/list"
claim_mission_url = "https://api.duckcoop.xyz/user-partner-mission/claim"
create_order_url = "https://game-api.duckcoop.xyz/dump-game/create-order"

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

def read_token_ids_from_file(filename):
    with open(filename, 'r') as file:
        token_ids = [line.strip() for line in file.readlines()]
    return token_ids

def get_game_id(ws_game_url, token):
    class GameWebSocketClient:
        def __init__(self, ws_game_url, token):
            self.ws_game_url = ws_game_url
            self.token = token
            self.ws = None
            self.authenticated = False
            self.game_id = None
        def on_message(self, ws, message):
            try:
                parsed_message = json.loads(message)
                if 'channel' in parsed_message and parsed_message['channel'] == 'game_update':
                    game_data = parsed_message.get('data', {})
                    self.game_id = game_data.get('id')
                    ws.close()
                elif 'type' in parsed_message:
                    msg_type = parsed_message['type']
                    if msg_type == 'login':
                        self.handle_login_response(parsed_message)
                    elif msg_type == 'ping':
                        self.ws.send(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
        def handle_login_response(self, response):
            error_code = response.get('error_code', '')
            if not error_code:
                self.authenticated = True
                self.subscribe_to_game_updates()
        def subscribe_to_game_updates(self):
            if not self.authenticated:
                return
            subscription_message = {
                "type": "subscribe",
                "data": {
                    "type": "dump_game",
                    "game_id": 1
                }
            }
            self.ws.send(json.dumps(subscription_message))
        def on_error(self, ws, error):
            pass
        def on_close(self, ws, close_status_code, close_msg):
            pass
        def on_open(self, ws):
            self.authenticate()
        def authenticate(self):
            auth_message = {
                "type": "login",
                "token": self.token
            }
            self.ws.send(json.dumps(auth_message))
        def connect(self):
            self.ws = websocket.WebSocketApp(
                self.ws_game_url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            self.ws.on_open = self.on_open
            self.ws.run_forever()
    client = GameWebSocketClient(ws_game_url, token)
    client.connect()
    return client.game_id

def get_balance(token_id, token_index):
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token_id}",
        "origin": "https://app.duckcoop.xyz",
        "referer": "https://app.duckcoop.xyz/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(get_balance_url, headers=headers)
        response.raise_for_status()
        result = response.json()
        if result.get("error_code") == "OK":
            data = result.get("data", {})
            age = data.get("age", "0")
            premium = data.get("premium", "0")
            friends = data.get("friends", "0")
            total = data.get("total", "0")
            print(f"[*] Tài khoản số: {token_index}")
            print(f"[*] Số điểm hiện tại: {total}")
        else:
            print(f"[*] Hiện tại không thể truy xuất thông tin dữ liệu cho tài khoản.")
    except requests.RequestException as e:
        print(f"[*] Đã xảy ra lỗi khi lấy thông tin cho tài khoản!")

def claim_checkin(token_id):
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token_id}",
        "origin": "https://app.duckcoop.xyz",
        "referer": "https://app.duckcoop.xyz/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    try:
        response = requests.post(claim_checkin_url, headers=headers)
        response.raise_for_status()
        result = response.json()
        if result.get("error_code") == "OK":
            print(f"[*] Đã điểm danh thành công cho tài khoản ngày hôm nay.")
        else:
            print(f"[*] Hiện tại không thể điểm danh thành công cho tài khoản ngày hôm nay.")
    except requests.RequestException as e:
        print(f"[*] Đã xảy ra lỗi khi điểm danh cho tài khoản ngày hôm nay!")

def get_partner_mission_list(token_id):
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token_id}",
        "origin": "https://app.duckcoop.xyz",
        "referer": "https://app.duckcoop.xyz/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(partner_mission_list_url, headers=headers)
        response.raise_for_status()
        result = response.json()
        if result.get("error_code") == "OK":
            missions = result.get("data", {}).get("data", [])
            mission_ids = []
            for partner in missions:
                partner_missions = partner.get("partner_missions", [])
                for mission in partner_missions:
                    mission_ids.append(mission.get("pm_id"))
            return mission_ids
        else:
            print(f"[*] Hiện tại không thể truy xuất dữ liệu nhiệm vụ của tài khoản thành công.")
            return None
    except requests.RequestException as e:
        print(f"[*] Đã xảy ra lỗi khi lấy dữ liệu nhiệm vụ của tài khoản!")
        return None

def claim_mission(token_id, partner_mission_ids):
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token_id}",
        "origin": "https://app.duckcoop.xyz",
        "referer": "https://app.duckcoop.xyz/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    mission_success = []
    mission_errors = []
    for partner_mission_id in partner_mission_ids:
        payload = {"partner_mission_id": partner_mission_id}
        try:
            response = requests.post(claim_mission_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            if result.get("error_code") == "OK":
                mission_success.append(partner_mission_id)
            else:
                mission_errors.append(partner_mission_id)
        except requests.RequestException:
            mission_errors.append(partner_mission_id)
    if mission_success:
        print(f"[*] Đã hoàn thành xong thành công tất cả nhiệm vụ cho tài khoản.")
    if mission_errors:
        print(f"[*] Đã xảy ra lỗi khi hoàn thành các nhiệm vụ cho tài khoản!")
 
def create_order(token_id, dump_game_id, game_id, price_out, quantity):
    headers = {
        "accept": "application/json, text/plain, */*",
        "authorization": f"Bearer {token_id}",
        "origin": "https://app.duckcoop.xyz",
        "referer": "https://app.duckcoop.xyz/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
    }
    payload = {"dump_game_id": dump_game_id,"game_id": game_id,"quantity": quantity,"price_out": price_out}
    try:
        response = requests.post(create_order_url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        if result.get("error_code") == "OK":
            print(f"[*] Đã đặt cược trò chơi thành công với số điểm: {price_out}.")
        else:
            print(f"[*] Hiện tại không thể đặt cược trò chơi thành công với số điểm: {price_out}.")
    except requests.RequestException as e:
        print(f"[*] Đã xảy ra lỗi khi đặt cược trò chơi!")

def main():
    while True:
        clear_console()
        token_ids = read_token_ids_from_file('data.txt')
        for index, token_id in enumerate(token_ids, start=1):
            print("-" * 60)
            get_balance(token_id, index)
            claim_checkin(token_id)
            mission_ids = get_partner_mission_list(token_id)
            claim_mission(token_id, mission_ids)            
            game_id = get_game_id(ws_game_url, token_id)
            create_order(token_id, dump_game_id=game_id, game_id=1, price_out=1.16, quantity=500)
        print("-" * 60)
        print(f"[*] Đã hoàn thành xong tất cả tài khoản! Vui lòng đợi một xíu để tiếp tục vòng lặp.")
        time.sleep(6)

if __name__ == "__main__":
    main()
