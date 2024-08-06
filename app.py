from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Admin user IDs (as a list of strings)
admin_ids = ["5935306519", "6356252393"]

# In-memory storage
allowed_user_ids = set()
user_approval_expiry = {}
logs = []

USER_FILE = "users.txt"
LOG_FILE = "log.txt"

def read_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, "r") as file:
            return set(file.read().splitlines())
    return set()

def write_users():
    with open(USER_FILE, "w") as file:
        for user_id in allowed_user_ids:
            file.write(f"{user_id}\n")

def append_log(entry):
    with open(LOG_FILE, "a") as file:
        file.write(entry + "\n")
    logs.append(entry)

@app.route('/add_user', methods=['POST'])
def add_user():
    user_id = request.json.get('user_id')
    duration = request.json.get('duration')
    if user_id in admin_ids:
        duration_str = duration
        try:
            duration = int(duration_str[:-4])
            if duration <= 0:
                raise ValueError
            time_unit = duration_str[-4:].lower()
            if time_unit not in ('hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months'):
                raise ValueError
        except ValueError:
            return jsonify({"error": "Invalid duration format."}), 400

        if user_id not in allowed_user_ids:
            allowed_user_ids.add(user_id)
            write_users()
            current_time = datetime.now()
            if time_unit == "hour" or time_unit == "hours":
                expiry_date = current_time + timedelta(hours=duration)
            elif time_unit == "day" or time_unit == "days":
                expiry_date = current_time + timedelta(days=duration)
            elif time_unit == "week" or time_unit == "weeks":
                expiry_date = current_time + timedelta(weeks=duration)
            elif time_unit == "month" or time_unit == "months":
                expiry_date = current_time + timedelta(days=30 * duration)
            user_approval_expiry[user_id] = expiry_date
            response = f"User {user_id} added successfully for {duration} {time_unit}. Access will expire on {expiry_date}."
        else:
            response = "User already exists."
    else:
        response = "Unauthorized."
    return jsonify({"response": response})

@app.route('/remove_user', methods=['POST'])
def remove_user():
    user_id = request.json.get('user_id')
    if user_id in admin_ids:
        user_to_remove = request.json.get('user_to_remove')
        if user_to_remove in allowed_user_ids:
            allowed_user_ids.remove(user_to_remove)
            write_users()
            response = f"User {user_to_remove} removed successfully."
        else:
            response = "User not found."
    else:
        response = "Unauthorized."
    return jsonify({"response": response})

@app.route('/clear_logs', methods=['POST'])
def clear_logs():
    if request.json.get('user_id') in admin_ids:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
            logs.clear()
            response = "Logs cleared successfully."
        else:
            response = "No logs found."
    else:
        response = "Unauthorized."
    return jsonify({"response": response})

@app.route('/show_logs', methods=['GET'])
def show_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as file:
            log_content = file.read()
        return jsonify({"logs": log_content})
    else:
        return jsonify({"logs": "No logs found."})

@app.route('/user_info', methods=['GET'])
def user_info():
    user_id = request.args.get('user_id')
    username = "N/A"  # Replace with actual username lookup if needed
    role = "Admin" if user_id in admin_ids else "User"
    expiry_date = user_approval_expiry.get(user_id, 'Not Approved')
    remaining_time = str(user_approval_expiry.get(user_id) - datetime.now()) if user_id in user_approval_expiry else "N/A"
    response = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "approval_expiry_date": expiry_date,
        "remaining_approval_time": remaining_time
    }
    return jsonify(response)

@app.route('/broadcast', methods=['POST'])
def broadcast():
    if request.json.get('user_id') in admin_ids:
        message = request.json.get('message')
        for user_id in allowed_user_ids:
            append_log(f"Broadcast message to {user_id}: {message}")
        return jsonify({"response": "Broadcast message sent successfully."})
    else:
        return jsonify({"response": "Unauthorized."})

if __name__ == '__main__':
    app.run(debug=True)
