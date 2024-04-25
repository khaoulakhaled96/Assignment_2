import random
import time
import os
from rticonnextdds_connector import Connector

file_path = os.path.dirname(os.path.realpath(__file__))
connector = Connector(config_name="MyParticipantLibrary::SensorPubParticipant",
                      url=file_path + "./PatientVitalSigns.xml")

output = connector.get_output("SensorPublisher::SensorWriter")

repeat_patientID = True

while repeat_patientID:
    patient = input('Enter Patient ID: ')  # Set patient ID
    output.instance.set_string("patienID", patient.lower())
    
    if patient.split()[0].lower() == 'invalid':
        print('Patient ID cannot be used\n')
    else:
        repeat_patientID = False

print("Connecting to Server...")
output.wait_for_subscriptions()

print("Sending Patient Vital Signs...")

while True:
    # Send random values of the patient vital signs
    output.instance.set_number("HeartRate", 60 + random.randint(-30, 30))
    output.instance.set_number("BloodPressuer", 90 + random.randint(-30, 30))
    output.instance.set_number("OxygenSaturation", 95 + random.randint(-30, 30))
    output.write()
    time.sleep(1)  # Write at a rate of one sample every 1 second