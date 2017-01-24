from flask import Flask, request
from flask_socketio import SocketIO, send
import collections
import time, threading, subprocess, collections


app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app)

queues = {}
queues['resource'] = {}
#deadlock_check_start = 'True'

@socketio.on('message')
def handleMessage(msg):

	message = dict(msg)
	if message['request_id'] == '':
		message['request_id'] = request.sid

	if message['resource'].endswith(" ") or message['resource'].endswith("/"):
		message['resource'] = message['resource'].replace(message['resource'][len(message['resource']) - 1], "")

	if 'type' in message:
		response = {'status' : 'success', 'resource' : '' }
		if message['type'] == 'demand':
			for resource in queues:
				if message['resource'] == resource:														# is the requested resource already in queue?

					if message['request_id'] == queues[resource]['clients'][0]:							# is the requested resource already locked to this client?
						
						if queues[resource]['active'] == False:
							response = {'status': 'activate', 'resource' : resource}
						else:
							response = {'status': 'already', 'resource' : resource}

					elif message['request_id'] in queues[resource]['clients']:							# is the client already in the waiting queue?
						response = {'status': 'waiting', 'resource' : resource}

					else:
						response = {'status':'wait', 'resource' : resource}


				elif message['resource'].startswith(resource + "/") and message['request_id'] == queues[resource]['clients'][0]:		# is the requested resource inside a resource that is locked to this clinets?
					response = {'status': 'already', 'resource' : resource}

				elif resource.startswith(message['resource'] + "/") and message['request_id'] == queues[resource]['clients'][0]:		# is the resource is containing a resource that is locked to this clients?
					response = {'status': 'replace', 'resource': resource}

				elif message['resource'] == resource or message['resource'].startswith(resource + "/") or resource.startswith(message['resource'] + "/"):
					response = {'status':'semi_wait', 'resource' : resource}


			if response['status'] == 'activate':
				queues[response['resource']]['active'] = True
				send(message['resource'] + " is now in your control" + " : " + str(time.time()), room = message['request_id'])

			elif response['status'] == 'already':	
				send(resource + "is already in your control currently" + " : " + str(time.time()), room = message['request_id'])

			elif response['status'] == ' waiting':
				send("You are in the waiting list for this resource" + + " : " + str(time.time()), room = message['request_id'])

			elif response['status'] == 'replace':

				release_item(response['resource'], " released")
				if response['resource'] in queues:
					response['status'] = 'wait'
					send("You are in the waiting list for this resource" + " : " + str(time.time()), room = message['request_id'])
				else:
					response['resource'] = 'success'

			if response['status'] == 'wait':
				queues[response['resource']]['clients'].append(message['request_id']) 
				send("Your have been added to the waiting queue" + " : " + str(time.time()), room = message['request_id'])
				#deadlock_check_start = False

				#if deadlock_check_start == 'True':
				#	threading.Thread(target=check_deadlocks()).start()				# starts a thread to check for deadlocks
				#	deadlock_check_start = False

			elif response['status'] == 'semi_wait':
				queues[message['resource']] = {'clients' : [message['request_id']], 'time' : time.time(), 'active' : False}
				send("Your have been added to the waiting queue" + " : " + str(time.time()), room = message['request_id'])
				#deadlock_check_start = False
				
				#if deadlock_check_start == 'True':
				#	threading.Thread(target=check_deadlocks()).start()				# starts a thread to check for deadlocks
				#	deadlock_check_start = False

			else:
				queues[message['resource']] = {'clients' : [message['request_id']], 'time' : time.time(), 'active' : True}
				send(message['resource'] + " is now in your control" + " : " + str(time.time()), room = message['request_id'])

				threading.Thread(target=check_timeout(message['resource'])).start()								# starts a thread to check timeouts for this resource
			return



		#elif message['type'] == 'release':
		#	for resource in queues:
		#		if resource == message['resource'] and queues[resource]['clients'][0] == message['request_id']:
		#			release_item(resource, " released")
		#			return

		#		if resource.startswith(message['resource'] + "/"):
		#			send(resource + " is already locked to you", room = message['request_id'])

		#	send(message['resource'] + " is already not locked to you", room = message['request_id'])
		#	return



		# A simple example of linux command on the last acquired resource for this user
		#elif message['type'] == 'command':
		#	stdoutdata = subprocess.getoutput(message['resource'] + " " + clients[request.sid][len(clients[request.sid]) - 1])
		#	resources[message['resource']] = time.time()
		#	send(stdoutdata)



def release_item(resource, text):
	response = {'status' : 'do_nothing' , 'resource' : ''}
	for r in queues:
		if r != resource and (r.startswith(resource) or resource.startswith(r) and queues[r]['active'] == False):
			my_request = {'resource': r, 'type': 'demand', 'request_id': queues[r]['clients'][0]}
			handleMessage(my_request)


	print(queues[resource]['clients'][0])
	send(resource + text, room=queues[resource]['clients'][0])
	print(resource + text + " room : " + queues[resource]['clients'][0])
	if len(queues[resource]['clients']) > 1:
		send(resource + " is now in your control"+ str(time.time()), room=queues[resource]['clients'][1])
		queues[resource]['clients'].pop(0)
		queues[resource]['time'] = time.time()
		queues[resource]['active'] = True
	else:
		del queues[resource]
	return


def check_timeout(resource):
	while resource in queues:
		time.sleep(10)
		#if queues[resource] and time.time() - queues[resource]['time'] >= 10:
		if time.time() - queues[resource]['time'] >= 10:
			release_item(resource, " Time Out")


def check_deadlocks():
	'''while True:
		for resource in queues:
			for i in range(1, len(queues[resource]['clients'])):
				for r in queues:
					if queues[resource]['clients'][i] == queues[r]['clients'][0] and queues[resource]['clients'][0] in queues[r]['clients']:

	'''
	pass


@socketio.on('connect')
def test_connect():
	print("%s connected" % (request.sid))
	send(request.sid + ' connected' + " : " + str(time.time()))


@socketio.on('disconnect')
def test_disconnect():
	for resource in queues:
		if request.sid in queues[resource]['clients']:
			if request.sid == queues[resource]['clients'][0]:
				release_item(resource)
		else:
			queues[resource]['clinets'].remove(request.sid)
	print ("%s disconeected" % (request.sid))


if __name__ == '__main__':
	socketio.run(app)