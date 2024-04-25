from __future__ import print_function


from datetime import time
from datetime import datetime
from time import sleep
from sys import path as sys_path
from os import path as os_path

file_path = os_path.dirname(os_path.realpath(__file__))
sys_path.append(file_path + "./")

import rticonnextdds_connector as rti

with rti.open_connector(
        config_name="MyParticipantLibrary::ServerParticipant",
        url=file_path + "./PatientVitalSigns.xml") as connector:



    def process_sensor_data(sensor_input, patients, start_time):
        sensor_input.take()
        for sample in sensor_input.samples.valid_data_iter:
            data = sample.get_dictionary()
            patienID = data['patienID']
            HeartRate = data['HeartRate']
            BloodPressuer = data['BloodPressuer']
            OxygenSaturation = data['OxygenSaturation']

            patients[patienID.lower()] = [HeartRate, BloodPressuer, OxygenSaturation]
            print("Patients: " + str(patients) + '\n')

            patient_data = str(patients)
            file.write(str(datetime.now()) + ": " + patient_data + "\n")

            if not patients:
                print("NO SENSOR CONNECTED!!!")
                time.sleep(1)


    def process_hp_requests(HP_input, HP_output, patients, subscribed_HPs):
        HP_input.take() # used to subsribe to HPs Requests
        for sample in HP_input.samples.valid_data_iter:
            Req_data = sample.get_dictionary()
            HP_ID = Req_data['HP_ID'] # Extract The HP ID
            Req = Req_data['Req']   # Extract The Request 
            Req = Req.split()   # toknize the request to analyze the request
            sub_criteria = Req[0].lower()   # specifies subscription criteria (i.e., by patient id or vitals)
            HP_patients = []
            
            try:
                Request_details = Req[1].lower()    # details of the request (i.e., specific Patient ID or vital sign value)
                if sub_criteria == 'patient':   # handle requets of a specific patient 
                    if Request_details in patients:
                        print("HP: " + str(HP_ID) + " subsribed to patient: " + str(Request_details))
                        subscribed_HPs[HP_ID] = [Request_details]
                    else:
                        print(HP_ID+" Patient NOT Found")
                        HP_output.clear_members()
                        HP_output.instance.set_string("patienID", str(subscribed_HPs[HP_ID])+"Sensor NOT Connected!")
                        HP_output.instance.set_string("HP_ID", HP_ID)
                        HP_output.write()
                
                # CHECK FOR SUBSCRIBTION CRITERIA BASED ON HEART RATE
                elif sub_criteria.lower() == 'hr':
                    if Req[1] =='<': 
                        print("HP: " + str(HP_ID) + " subsribed to patients with HR <" + str(Req[2]))
                        for patient in patients:
                            if patients[patient][0] < int(Req[2]):
                               HP_patients.append(patient)
                               subscribed_HPs[HP_ID] = HP_patients
                    elif Req[1] =='>':
                        print("HP: " + str(HP_ID) + " subsribed to patients with HR >" + str(Req[2]))
                        for patient in patients:
                            if patients[patient][0] > int(Req[2]):
                               HP_patients.append(patient)
                               subscribed_HPs[HP_ID] = HP_patients
                
                # CHECK FOR SUBSCRIBTION CRITERIA BASED ON BLOOD PRESSURE               
                elif sub_criteria.lower() == 'bp':
                    if Req[1] =='<': 
                        print("HP: " + str(HP_ID) + " subsribed to patients with BP <" + str(Req[2]))
                        for patient in patients:
                            if patients[patient][1] < int(Req[2]):
                               HP_patients.append(patient)
                               subscribed_HPs[HP_ID] = HP_patients
                    elif Req[1] =='>':
                        print("HP: " + str(HP_ID) + " subsribed to patients with BP >" + str(Req[2]))
                        for patient in patients:
                            if patients[patient][1] > int(Req[2]):
                               HP_patients.append(patient)
                               subscribed_HPs[HP_ID] = HP_patients
                               
                # CHECK FOR SUBSCRIBTION CRITERIA BASED ON OXYGEN SATURATION               
                elif sub_criteria.lower() == 'spo2':
                    if Req[1] =='<': 
                        print("HP: " + str(HP_ID) + " subsribed to patients with Sp02 <" + str(Req[2]))
                        for patient in patients:
                            if patients[patient][2] < int(Req[2]):
                               HP_patients.append(patient)
                               subscribed_HPs[HP_ID] = HP_patients
                    elif Req[1] =='>':
                        print("HP: " + str(HP_ID) + " subsribed to patients with SpO2 >" + str(Req[2]))
                        for patient in patients:
                            if patients[patient][2] > int(Req[2]):
                               HP_patients.append(patient)
                               subscribed_HPs[HP_ID] = HP_patients
                                
                # CATCH ANY INVALID REQUESTS FROM HPs               
                else:
                    print("Invalid Request by HP!")
                    HP_output.clear_members()
                    HP_output.instance.set_string("patienID", "Invalid Request: Invalid Subscribtion Criteria")
                    HP_output.instance.set_string("HP_ID", HP_ID)
                    HP_output.write()

            except IndexError:
                print("Invalid Request by HP!")
                HP_output.clear_members()
                HP_output.instance.set_string("patienID", "Invalid Request: Invalid Subscribtion Criteria (Index Error)")
                HP_output.instance.set_string("HP_ID", HP_ID)
                HP_output.write()
            except KeyError:
                print("Unrecognized HP!")
                HP_output.clear_members()
                HP_output.instance.set_string("patienID", "Invalid Request: Invalid Subscribtion Criteria (Index Error)")
                HP_output.instance.set_string("HP_ID", HP_ID)
                HP_output.write()

        # SEND PATIENTS DETAILS TO HPs                
        for HP_ID in subscribed_HPs:
            for patient in subscribed_HPs[HP_ID]:
                try:
                    if patient in patients:
                        HP_output.instance.set_string("HP_ID", HP_ID)
                        HP_output.instance.set_string("patienID", str(patient))
                        HP_output.instance.set_number("HeartRate", patients[patient][0])
                        HP_output.instance.set_number("BloodPressuer", patients[patient][1])
                        HP_output.instance.set_number("OxygenSaturation", patients[patient][2])
                        HP_output.write()
                        sleep(1)    
                        conn_attempt_counter = 0
                        matched_subs = HP_output.matched_subscriptions
                        
                except KeyError:
                    conn_attempt_counter += 1
                    if (conn_attempt_counter > 5):
                        HP_output.clear_members() 
                        HP_output.instance.set_string("patienID","Invalid Request: Patient Sensor Disconnected!")
                        HP_output.instance.set_string("HP_ID", HP_ID)
                        HP_output.write()
                        sleep(1)


    if __name__ == "__main__":
        with rti.open_connector(
                config_name="MyParticipantLibrary::ServerParticipant",
                url=file_path + "./PatientVitalSigns.xml") as connector:

            sensor_input = connector.get_input("ServerSubscriber::Server_Sensor_Reader")
            HP_input = connector.get_input("ServerSubscriber::Server_HP_Reader")
            HP_output = connector.get_output("ServerPublisher::ServerWriter")

            patients = {}
            subscribed_HPs = {}
            start_time = datetime.now()
            conn_attempt_counter = 0

            file = open('Patients_Log.txt', 'a')
            file.write('Time            |   PatientID: HR  |   BP  |   SpO2\n')

            while True:
               process_sensor_data(sensor_input, patients, start_time)
               process_hp_requests(HP_input, HP_output, patients, subscribed_HPs)