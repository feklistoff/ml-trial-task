=============================
ml-trial-task
=============================

The task:
---------

  Make a toy service that will accept a list of image URLs over ZeroMQ REQ/REP socket which will then fetch those URLs and run object detection/classification on them.

  Once classification is done PUBlish the results per image over ZeroMQ.

  Provide unit tests (100% coverage not neccessary), provide working Dockerfile to run this. Extra points for a CLI tool that will parse URLs from CSV file, send the REQuest and then listen for the PUBlished messages printing results until all inferences have been received.

  https://pypi.org/project/datastreamservicelib/ (and the linked template) will help you a lot.

  Choice of image classification models etc is up to you. Service must remain responsive to new REQuests while processing previous list of URLs.



My solution
-----------

I've used the provided template to create a project. I've added a simple service that uses a pre-trained object detection model from torchvision to classify images.
The service is built using aiohttp and ZeroMQ. The service is able to classify multiple images at the same time and it will return the results for each image as soon as they processed.
Basedd on the task description, the project implements:

- A service that accepts a list of image URLs over ZeroMQ REQ/REP socket
- The service fetches the URLs and runs object detection on them
- The service publishes the results per image over ZeroMQ
- A CLI tool that takes a list of URLs or parses URLs from a CSV file, sends the request and listens for the published messages printing the results until all inferences have been received
- A simple Dockerfile to run the service in a containerized environment (minimum working example)
- Some unit tests for the service


Local setup
-----------

To run the service locally, you need to have Python (3.9 or higher) installed.

Create a virtual environment and activate it:
    ```
    python -m venv venv;
    source venv/bin/activate
    ```

Install Poetry: https://python-poetry.org/docs/#installation

You can install the dependencies using poetry:
    ```
    poetry install
    ```

Implemented stuff
^^^^^^^^^^^^^^^^^^^^^

``class ImagePredictionService`` - the service itself. It has two main methods:

- ``predict`` - the main method that accepts a list of image URLs and spans a new task for each image to classify it.

- ``process_image`` - the helper method that downloads the images, runs the object detection model on them and returns the results

``console.py`` - the CLI tool that can be used to start the service and send requests to the service. It has the following commands:

- ``run_service`` - starts the service

- ``run_predict`` - sends a request to the service to classify a list of images

Example usage
^^^^^^^^^^^^^^

To start the service run the following command:
    ```
    python src/ml_trial_task/console.py service -vv config.toml
    ```

In a separate terminal run the following command to start the CLI tool:
    ```
    python src/ml_trial_task/console.py predict -u "https://i.imgur.com/ivN5dal.jpeg, https://i.imgur.com/lcpzlEl.jpeg" config.toml
    ```

The example output:

  Predict command response: PubSubDataMessage(... 'response': {'status': 'processing', 'num_images': 2}})

  Subscribed and waiting for results

  Received: PubSubDataMessage(topic=b'results', ... 'boxes': [[1675, 954, 1990, 1205], [2296, 416, 2457, 537], ...], 'labels': ['car', 'car', ...], 'scores': [0.9985753297805786, 0.9982516169548035, ...]})

  Received: PubSubDataMessage(topic=b'results', ... 'boxes': [[1087, 2147, 1961, 4889], [795, 2170, 1499, 4831]], 'labels': ['person', 'person'], 'scores': [0.997600257396698, 0.996813952922821]})

  All results received, exiting.

Additionally, an example of a csv file with URLs is provided in the repository. You can use it to test the CLI tool with the following command:
    ```
    python src/ml_trial_task/console.py predict -c urls.csv config.toml
    ```

Docker
------

The Dockerfile is provided. This will let you test the service in a containerized environment.

This is a simple minimum working Dockerfile that will run the service. In oreder to quickly test the service in a containerized environment, I didn't use they provided Dockerfile template(s).

The image can be built with the following command:
    ```
    docker build -t ml-trial-task .
    ```

The image can be run with the following command:
    ```
    docker run -it --rm --name ml_trial_task ml_trial_task
    ```

The service will start running and listening for requests. Also, it will download the model.

After that in a separate terminal run the following command to start the CLI tool:
    ```
    docker exec -it ml_trial_task python src/ml_trial_task/console.py predict -u "https://i.imgur.com/ivN5dal.jpeg, https://i.imgur.com/lcpzlEl.jpeg" config.toml
    ```

NOTE: The csv option probably would fail. I didn't have much time to do everything thoroughly and test everything.
