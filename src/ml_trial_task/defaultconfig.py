"""Default configuration file contents"""

# Remember to add tests for keys into test_ml_trial_task.py
DEFAULT_CONFIG_STR = """
[zmq]
pub_sockets = ["ipc:///tmp/ml_trial_task_pub.sock", "tcp://*:56853"]
rep_sockets = ["ipc:///tmp/ml_trial_task_rep.sock", "tcp://*:56854"]

""".lstrip()
