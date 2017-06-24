import serial
ser = serial.Serial('/dev/ttyACM0', 9600)
while True :
    try:
        state=ser.readline()
        print(state)
	print(float(state[7:10])/10)
	print(float(state[11:14])/10)
	print(float(state[15:])/10)
    except:
	print("No data received")
        pass