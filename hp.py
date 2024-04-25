

from time import sleep

# Updating the system path is not required if you have pip-installed
# rticonnextdds-connector
from sys import path as sys_path
from os import path as os_path
file_path = os_path.dirname(os_path.realpath(__file__))
sys_path.append(file_path + "/../../../")

import rticonnextdds_connector as rti

with rti.open_connector(
        config_name="MyParticipantLibrary::HealthcareProviderParticipant",
        url=file_path + "./PatientVitalSigns.xml") as connector:

    # publish requests to the server
    output = connector.get_output("HPPublisher::HPWriter")
    # subsribe to replays of requests published to the server
    server_input = connector.get_input("HPSubscriber::HPReader") # used to get patient data from server
    HP_ID = input('Enter Healthcare Provider ID: ')
    Req = input('Enter Requested subscription criteria: ')
    print("Waiting for Server Connection...")
    # keep subscribing to the same patients based on the subscription criteria
    while True:
        output.instance.set_string("HP_ID", HP_ID)
        output.instance.set_string("Req", Req)
        output.write()

        server_input.take()
        sleep(.5)
        for sample in server_input.samples.valid_data_iter:
            # get all the fields in a get_dictionary()
            data = sample.get_dictionary()
            HP_ID_Res = data['HP_ID']
            patienID = data['patienID']
            HeartRate = data['HeartRate']
            BloodPressuer = data['BloodPressuer']  # take values as numbers
            OxygenSaturation = data['OxygenSaturation'] # take values as strings
            
            # if the requested subscription criteria is not valid reprompt the HP to enter valid criteria 
            if HP_ID_Res == HP_ID:
                if patienID.split()[0] == 'Invalid':
                    print(patienID) # PatientID is used to piggyback the error message from server
                    Req = input('Enter Requested subscription criteria: ')
                    print("Waiting for Server Connection...")
                    output.instance.set_string("HP_ID", HP_ID)
                    output.instance.set_string("Req", Req)
                    output.write()
                    print("Request Sent!")
    
                else:
                    print("Patient: " + repr(patienID) + " HR: " + repr(HeartRate) +
                            " BP: " + repr(BloodPressuer) + " SpO2: " + repr(OxygenSaturation)+"\n")
