import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from threading import Thread
from run import app
import time

# Database connection settings
DATABASE_URL = "postgresql://gift:gift123@localhost:5432/realtime_app"

def listen_for_changes():
    try:
        # Establishing a connection to PostgreSQL
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()

        # Start listening to the 'user_changes' channel
        cur.execute('LISTEN user_changes;')
        print("Listening on the 'user_changes' channel...")

        while True:
            # Wait for a notification
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop()
                print(f"Received notification: {notify.payload}")

                # Handle the notification (e.g., broadcast, log, etc.)
                try:
                    event_type, user_id = notify.payload.split(":")
                    print(f"Event: {event_type}, User ID: {user_id}")
                except ValueError:
                    print(f"Error parsing notification payload: {notify.payload}")

            time.sleep(1)  # Sleep for a short time to avoid busy-waiting

    except Exception as e:
        print(f"Error in listener: {e}")

def start_listener():
    # Start the listener in a separate thread
    thread = Thread(target=listen_for_changes)
    thread.daemon = True
    thread.start()
    print("Listener thread started.")

# Use app.app_context() to start listener after the app is fully initialized
with app.app_context():
    start_listener()
    print("Listener started and listening for database changes.")
if __name__ == '__main__':
    app.run(debug=True)
