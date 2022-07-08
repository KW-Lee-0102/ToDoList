This application is build in linux env.

To run the TodoList.py in Docker

options: 
1. run the command 'python3 TodoList.py' in terminal.
2. run via docker container
	- build the docker image by the command: 
          'docker build -t todo . -f DockerFile'
        - then run the image:
           'docker run -p 1234:1234 todo'

Once it's running, you will see the application is hosted in https:127.0.0.1:1234/

Read the 'HowToRun' doc to perform the testing.
