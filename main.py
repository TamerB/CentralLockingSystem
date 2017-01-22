from flask import Flask, request
from flask_socketio import SocketIO, send
import time, threading, subprocess, collections

resources = {}
clients = {}
queue = collections.defaultdict(list)
start = True

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app)

@socketio.on('message')
def handleMessage(msg):
	print(msg)
	message = dict(msg)
	print(message)

	if message['resource'].endswith(" ") or message['resource'].endswith("/"):
		message['resource'] = message['resource'].replace(message['resource'][len(message['resource']) - 1], "")

	if 'type' in message:
		if message['type'] == 'demand':
			for r in resources:
				if message['resource'] == r or message['resource'].startswith(r + "/"):
					for c in clients[request.sid]:
						if message['resource'] == c or message['resource'].startswith(c + "/"):
							send(message['resource'] + " is already under your control")
							return
					send(message['resource'] + " is currently locked")
					queue[message['resource']].append(request.sid)
					if start === True:
						threading.Thread(check_deadlocks(message['resource'], request.sid)).start()
						start = False
					return

				if r.startswith(message['resource'] + "/") and r in clients[request.sid]:
					clients[request.sid][clients[request.sid].index(r)] = message['resource']
					del r
					resources[message['resource']] = time.time()
					send(message['resource'] + " is now under your control")
					treading.Thread(check_timeout(message['resource'], request.sid)).start()
					return

			resources[message['resource']] = time.time()
			clients[request.sid].append(message['resource'])
			send(message['resource'] + " is now under your control")
			threading.Thread(check_timeout(message['resource'], request.sid)).start()

		elif message['type'] == 'release':
			for c in clients[request.sid]:
				if c == message['resource']:
					for r in resources:
						if c == r:
							del r
							clients[request.sid].remove(message['resource'])
							send(message['resource'] + " released")
							threading.Thread(next_request(message['resource'])).start()
							return
				if message['resource'].startswith(c + "/"):
					send("All of " + c + " is already under your control... You can release it as a whole if you wish")
					return
			send(message['resource'] + " is not under your control")

		# A simple example of linux command on the last acquired resource for this user
		elif message['type'] == 'command':
			stdoutdata = subprocess.getoutput(message['resource'] + " " + clients[request.sid][len(clients[request.sid]) - 1])
			resources[message['resource']] = time.time()
			send(stdoutdata)

def next_request(msg):
	if msg in queue:
		print(resources[msg])
		print(queue[msg])
		index = queue[msg][0]
		resources[msg] = time.time()
		clients[queue[msg][0]].append(msg)
		queue[msg].remove(queue[msg][0])
		send(msg + " is now under you control", room = index)
		return

def check_timeout(r, sid):
	while True:
		time.sleep(10)
		if time.time() - resources[r] >= 10:
			clients[sid].remove(r)
			del resources[r]
			send("Timeout: " + r + " has been released", room = sid)
			threading.Thread(next_request(r)).start()
			return

def check_deadlocks(r, sid):
	pass

@socketio.on('connect')
def test_connect():
	print("%s connected" % (request.sid))
	clients[request.sid] = []
	send(request.sid + 'has entered the room.')
	#send("Welcome... You are now connected")

@socketio.on('disconnect')
def test_disconnect():
	for r in resources:
		if r == clients[request.sid]:
			del r
			del clients[request.sid]
	print ("%s disconeected" % (request.sid))

if __name__ == '__main__':
	socketio.run(app)