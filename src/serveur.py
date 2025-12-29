__license__ = "Regarder le fichier LICENSE.txt dans le répertoire racine du projet. (exception unique de ce fichier : seule la distribution non commerciale dans le domaine public est autorisée)"
__author__ = "PFLIEGER-CHAKMA Nathan alias J0ytheC0de"

import socket
import threading
import json
import time
import sys
sys.stdout.reconfigure(encoding='utf-8')

from Assets.utils import get_local_ip

HOST = "0.0.0.0"
PORT = int(input("Entrez le port du serveur entre 3000 et 9999 (ex: 9999): ") or "9999")

clients = {}  # { (ip, port): {"x": , "y": , "z": , "player": str, "model": str, "last_seen": timestamp} }
door_states = {}  # { door_id: True/False }
CLIENT_TIMEOUT = 10  # secondes avant qu’un client soit considéré inactif
PING_INTERVAL = 10    # fréquence de ping automatique


def remove_inactive_clients():
    now = time.time()
    inactive = [c for c, d in clients.items() if now - d["last_seen"] > CLIENT_TIMEOUT]
    for c in inactive:
        print(f"⏱️ Client {clients[c].get('player', c)} inactif, supprimé.")
        del clients[c]

def broadcast_packet(sock, packet):
    """Envoi le packet à tous les clients, gestion des clients déco"""
    for c_addr in list(clients.keys()):
        try:
            sock.sendto(packet, c_addr)
        except OSError as e:
            if e.errno == 10054:
                print(f"⚠️ Client injoignable: {c_addr}, supprimé.")
                clients.pop(c_addr, None)
            else:
                print("Erreur envoi:", e)

def handle_clients(sock):
    print(f"✅ Serveur prêt sur {HOST}:{PORT}")
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            msg = json.loads(data.decode())

            # --- MESSAGE PORTE ---
            if msg.get("type") == "door_toggle":
                door_id = msg["door_id"]
                state = msg["state"]
                door_states[door_id] = state

                packet = json.dumps({
                    "type": "door_sync",
                    "door_id": door_id,
                    "state": state
                }).encode()

                broadcast_packet(sock, packet)
                continue

            # --- MESSAGE POSITIONS ---
            if msg.get("type") == "pos":
                clients[addr] = {
                    "x": msg["x"],
                    "y": msg["y"],
                    "z": msg["z"],
                    "player": msg.get("player", "Player"),
                    "model": msg.get("model", "default"),
                    "last_seen": time.time()
                }


            # --- MESSAGE DEMANDE SUPPRESSION ---
            if msg.get("type") == "remove_player":
                target_player = msg.get("player")
                removed = False
                for c, data in list(clients.items()):
                    if data.get("player") == target_player:
                        del clients[c]
                        removed = True
                        print(f"❌ Joueur {target_player} supprimé à la demande.")
                if removed:
                    continue

            # Nettoyer les clients inactifs
            remove_inactive_clients()

            # Préparer la liste des autres joueurs
            others = []
            for c_addr, c_data in clients.items():
                others.append({
                    "id": f"{c_addr[0]}:{c_addr[1]}",
                    "player": c_data["player"],
                    "model": c_data["model"],
                    "x": c_data["x"],
                    "y": c_data["y"],
                    "z": c_data["z"]
                })

            # Envoyer la liste à tous les clients
            # Envoyer la liste à tous les clients, inclure l'état des portes
            packet = json.dumps({
                "type": "players",
                "players": others,
                "doors": door_states  # dictionnaire { door_id: True/False }
            }).encode()
            broadcast_packet(sock, packet)


            broadcast_packet(sock, packet)

        except json.JSONDecodeError:
            print("⚠️ Paquet non valide reçu.")
        except Exception as e:
            print("Erreur réception:", e)

def ping_clients(sock):
    """Ping régulier pour détecter clients inactifs"""
    while True:
        time.sleep(PING_INTERVAL)
        now = time.time()
        for c_addr in list(clients.keys()):
            if now - clients[c_addr]["last_seen"] > CLIENT_TIMEOUT:
                print(f"⏱️ Client {clients[c_addr].get('player')} timeout, supprimé.")
                clients.pop(c_addr, None)

def start_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))

    local_ip = get_local_ip()
    print(f"✅ Serveur prêt sur {local_ip}:{PORT} (IP locale)")

    threading.Thread(target=handle_clients, args=(sock,), daemon=True).start()
    threading.Thread(target=ping_clients, args=(sock,), daemon=True).start()

    print("🟢 Serveur démarré. Ctrl+C pour quitter.")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    start_server()
