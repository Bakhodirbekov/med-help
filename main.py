import csv
import os
import requests
from datetime import datetime

# Constants
TOKEN = 'YOUR_BOT_TOKEN'
USER_IDS_FILE = 'user_ids.csv'
POSTS_FILE = 'posts.csv'
ADMIN_LOGIN = 'admin@gmail.com'
ADMIN_PASSWORD = 'ise51'

def load_user_ids():
    """Load user IDs from the CSV file."""
    user_ids = set()
    if os.path.exists(USER_IDS_FILE):
        with open(USER_IDS_FILE, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:
                    user_ids.add(row[0])
    return user_ids

def save_user_id(user_id):
    """Save a user ID to the CSV file if it does not already exist."""
    user_ids = load_user_ids()
    if user_id not in user_ids:
        with open(USER_IDS_FILE, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([user_id])

def save_post(title, number, description, image_file):
    """Save post information to a CSV file."""
    with open(POSTS_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([title, number, description, image_file])

def send_message(chat_id, text):
    """Send a text message to a chat."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text}
    requests.post(url, data=payload)

def send_photo(chat_id, photo_path, caption):
    """Send a photo to a chat."""
    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        payload = {'chat_id': chat_id, 'caption': caption}
        files = {'photo': photo}
        requests.post(url, data=payload, files=files)

def get_updates():
    """Get updates from Telegram."""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    response = requests.get(url)
    return response.json().get('result', [])

def handle_start(update):
    chat_id = update['message']['chat']['id']
    save_user_id(chat_id)
    send_message(chat_id, "Welcome! You will receive updates from now on.")

def handle_add(update):
    chat_id = update['message']['chat']['id']
    send_message(chat_id, "Please login to add a post. Send your login and password in the format: login password")

    # Wait for login credentials
    updates = get_updates()
    for update in updates:
        if 'message' in update and update['message']['chat']['id'] == chat_id:
            credentials = update['message']['text'].split()
            if len(credentials) != 2:
                send_message(chat_id, "Please enter login and password separated by space.")
                continue

            login, password = credentials
            if login == ADMIN_LOGIN and password == ADMIN_PASSWORD:
                send_message(chat_id, "Logged in successfully. Please provide the post title.")
                
                # Wait for title
                updates = get_updates()
                for update in updates:
                    if 'message' in update and update['message']['chat']['id'] == chat_id:
                        title = update['message']['text']
                        send_message(chat_id, "Please provide the post number.")
                        
                        # Wait for number
                        updates = get_updates()
                        for update in updates:
                            if 'message' in update and update['message']['chat']['id'] == chat_id:
                                number = update['message']['text']
                                send_message(chat_id, "Please provide the post description.")
                                
                                # Wait for description
                                updates = get_updates()
                                for update in updates:
                                    if 'message' in update and update['message']['chat']['id'] == chat_id:
                                        description = update['message']['text']
                                        send_message(chat_id, "Please send the post image.")
                                        
                                        # Wait for image
                                        updates = get_updates()
                                        for update in updates:
                                            if 'message' in update and update['message']['chat']['id'] == chat_id and 'photo' in update['message']:
                                                file_id = update['message']['photo'][-1]['file_id']
                                                file_url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
                                                response = requests.get(file_url).json()
                                                file_path = response['result']['file_path']
                                                file_download_url = f"https://api.telegram.org/file/bot{TOKEN}/{file_path}"
                                                
                                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                                image_file_name = f'post_{timestamp}.jpg'
                                                
                                                # Download the image
                                                with requests.get(file_download_url, stream=True) as r:
                                                    with open(image_file_name, 'wb') as f:
                                                        for chunk in r.iter_content(chunk_size=8192):
                                                            f.write(chunk)
                                                
                                                caption = f"Title: {title}\nNumber: {number}\nDescription: {description}"
                                                send_photo(chat_id, image_file_name, caption)
                                                
                                                save_post(title, number, description, image_file_name)
                                                send_message(chat_id, "Post added successfully!")
                                                
                                                os.remove(image_file_name)
                                                return

def handle_broadcast(update):
    user_ids = load_user_ids()
    if not user_ids:
        send_message(update['message']['chat']['id'], "No users to broadcast to.")
        return

    if not os.path.exists(POSTS_FILE):
        send_message(update['message']['chat']['id'], "No posts available to broadcast.")
        return

    with open(POSTS_FILE, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 4:
                title, number, description, image_file = row
                if os.path.exists(image_file):
                    caption = f"Title: {title}\nNumber: {number}\nDescription: {description}"
                    for user_id in user_ids:
                        try:
                            send_photo(user_id, image_file, caption)
                        except Exception as e:
                            print(f"Failed to send message to {user_id}: {e}")
                else:
                    print(f"Image file {image_file} does not exist.")

def main():
    while True:
        updates = get_updates()
        for update in updates:
            if 'message' in update:
                text = update['message'].get('text', '')
                if text == '/start':
                    handle_start(update)
                elif text == '/add':
                    handle_add(update)
                elif text == '/broadcast':
                    handle_broadcast(update)

if __name__ == '__main__':
    main()
