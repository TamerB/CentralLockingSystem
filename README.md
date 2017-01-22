# CentralLockingSystem
Simple Central Locking System written in python using Flask, Flask-socket.io

Funcionalities:
- Execlusive access to shared resources.
- Ability to request and release resources.
- Release resources after Timeout.
- assigning resources to clients in the waiting queue.
- Still no deadlock handling yet.

To the run the application:
1.  run "pip3 install -r requirements.txt"
2.  check the ip address in templates/index.html and edit it if nicessary.
3.  run "$python3 main.py"
4.  run templates/index.html file
