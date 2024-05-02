from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo import ASCENDING
from datetime import datetime, timezone, timedelta
import time
import asyncio
from bleak import BleakScanner

def calc_dist(RSSI, A=-59, n=2.5):
    dist = 10 ** ((A-RSSI) / (10 * n))
    if dist<18:
        return dist
    else:
        return 19

async def BLErun(client, start_time):
    print('Scanning for BLE devices with names...')
    try:
        ScanNumber = 0
        while True: 
            tag1_results = []
            tag2_results = []
            # print_time = start_time + timedelta(seconds=8 * ScanNumber) # calculates the time at which a BLE (Bluetooth Low Energy) scan should start
            # timedelta is used to efficiently + or - two times
            print_time = datetime.now()
            formatted_time = print_time.strftime("%H:%M:%S.%f")[:-3]  # truncate microseconds to milliseconds
            print(f"Scan started at      {formatted_time}")
            ScanNumber+=1
            start_timer = time.perf_counter()
            devices = await BleakScanner.discover(timeout=3.75)
            for device in devices:
                if device.name == "Ttag123456789":  # Check if the device has a name
                    Tag_distance = calc_dist(device.rssi)
                    print(f"Found BLE device: {device.name}, Signal Strength: {device.rssi} dBm, Tag Distance: {Tag_distance} m, Scan Number: {ScanNumber}.")
                    tag1_results.append(Tag_distance)
                if device.name == "Ttag2":  # Check if the device has a name
                    Tag_distance = calc_dist(device.rssi,-60, 1.5)
                    print(f"Found BLE device: {device.name}, Signal Strength: {device.rssi} dBm, Tag Distance: {Tag_distance} m.")
                    tag2_results.append(Tag_distance)
            end_timer = time.perf_counter()
            elapsed_time = end_timer - start_timer
            print(f"Elapsed time for BLE scanning 1 is {elapsed_time:.3f} seconds")
            start_timer = time.perf_counter()
            devices = await BleakScanner.discover(timeout=3.75)
            for device in devices:
                if device.name == "Ttag123456789":  # Check if the device has a name
                    Tag_distance = calc_dist(device.rssi)
                    tag1_results.append(Tag_distance)
                    print(f"Found BLE device: {device.name}, Signal Strength: {device.rssi} dBm, Tag Distance: {Tag_distance} m, Scan Number: {ScanNumber}.")
                if device.name == "Ttag2":  # Check if the device has a name
                    Tag_distance = calc_dist(device.rssi,-60, 1.5)
                    print(f"Found BLE device: {device.name}, Signal Strength: {device.rssi} dBm, Tag Distance: {Tag_distance} m.")
                    tag2_results.append(Tag_distance)
            end_timer = time.perf_counter()
            elapsed_time = end_timer - start_timer
            print(f"Elapsed time for BLE scanning 2 is {elapsed_time:.3f} seconds")
            if len(tag1_results)==2:
                tag_distance = round((sum(tag1_results)/2),1)
                client.update_local_location(tag_distance, 1, 1, ScanNumber)
                print(f"Tag 1: {tag_distance} m, Scan Number: {ScanNumber}, averaged sent.")
            if len(tag1_results)==1:
                tag_distance = round((tag1_results[0]*7/4),1)
                client.update_local_location(tag_distance, 1, 1, ScanNumber)

            if len(tag2_results)==2:
                tag_distance = round((sum(tag2_results)/2),)
                client.update_local_location(tag_distance, 2, 1, ScanNumber)
            if len(tag2_results)==1:
                tag_distance = round((tag2_results[0]*7/4),1)
                client.update_local_location(tag_distance, 2, 1, ScanNumber)

# Get the current time
            current_time = datetime.now()
            formatted_time = current_time.strftime("%H:%M:%S.%f")[:-3]  # truncate microseconds to milliseconds
            print(f"Finished scanning at {formatted_time}")
            print(f"Time for sleeping is {max(0, (print_time + timedelta(seconds=8) - datetime.now()).total_seconds())}")
            time.sleep(max(0, (print_time + timedelta(seconds=8) - datetime.now()).total_seconds()))

    except KeyboardInterrupt:
        print("Stopped by Control-C")

class MongoDBCentral:
    def __init__(self):
        # Initialize the MongoDB Client with the given URI.
        self.uri = "mongodb+srv://om453:mongodb012@cluster0.wodzmcz.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        self.client = None
        self.connect()

    def connect(self):
        # Connect to the MongoDB server using the URI provided.
        try:
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
            self.client.admin.command('ping')  # Ping to test the connection.
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
           
    def update_local_location(self, radius, TagID, ReceiverID, ScanNumber):
        db = self.client['Demo1'] 
        ttag_local_collection = db['T_tags_local']  
        ttag_global_collection = db['T_tags']  
        receiver_collection = db['Receivers']  


           # Check to see if the tag with 'TagID' is active
        active_tag = ttag_global_collection.find_one(
                    {'TagID': TagID, 'Active': True}
                )
        
        receiver_acode = receiver_collection.find_one({'ReceiverID': ReceiverID}, {'AreaCode': 1})

        # If the tag is inactive or not found, print a message and return
        if not active_tag:
            print(f"Tag with ID {TagID} isn't active or doesn't exist. Activate tag before use")
            return

        # Construct the tracker tag data dictionary
        tracker_tag_data = {
            'Time_of_update': datetime.now(timezone.utc),
            'TagID': TagID,
            'ReceiverID': ReceiverID,  # Replace with the actual receiver ID
            'radius': radius,  # Replace with the actual radius value
            'Area code' : receiver_acode,
            'Scan Number': ScanNumber 
        }

    # Insert the document in the collection
        try:
            insert_result = ttag_local_collection.insert_one(tracker_tag_data)

            if insert_result.acknowledged:
                print(f"TagID {TagID} local location document added.")
            else:
                print(f"No document with TagID {TagID} found to update.")
        except Exception as e:
            print(f"An error occurred while updating the document: {e}")

if __name__ == "__main__":
    # Instantiate the MongoDBClient, which connects to the MongoDB database
    mongo_client = MongoDBCentral()
    # # mongo_client.DeleteTTagUsingID(12)
    # mongo_client.update_local_location(10, 2, 121)

    # for i in range(50):
    #     time.sleep(5)  # Wait for 2.5 seconds

    #     mongo_client.update_local_location(10, 2, 121, i)
    # Synchronize to the next minute and then to the next 5-second mark

    current_time = datetime.now()
    formatted_time = current_time.strftime("%H:%M:%S.%f")[:-3]  # truncate microseconds to milliseconds
    print(f"The program has started at {formatted_time}")

    sleep_time = 60 - datetime.now().second - datetime.now().microsecond / 1e6
    print(f"Sleeping for {sleep_time} seconds")
    time.sleep(sleep_time)

    start_time = datetime.now()
    current_time = start_time.strftime("%H:%M:%S.%f")[:-3]  # truncate microseconds to milliseconds
    print(f"Start time =  {start_time}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(BLErun(mongo_client, start_time))
