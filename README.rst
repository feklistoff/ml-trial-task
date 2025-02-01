=============================
ml-trial-task
=============================

!!!! READ ME FIRST: Start by going to the "Local Development" section at end of this document !!!!

!!!! FIXME: You MUST edit this file, read it through *with thought* !!!!

!!!! FIXME: Check CI config file, should you change the repo pointer ?? !!!!

!!!! FIXME: Check pyroject.toml: repo pointer, license, authors etc !!!!

ml trial task

Docker
------

For more controlled deployments and to get rid of "works on my computer" -syndrome, we always
make sure our software works under docker.

It's also a quick way to get started with a standard development environment.

SSH agent forwarding
^^^^^^^^^^^^^^^^^^^^

We need buildkit_::

    export DOCKER_BUILDKIT=1

.. _buildkit: https://docs.docker.com/develop/develop-images/build_enhancements/

And also the exact way for forwarding agent to running instance is different on OSX::

    export DOCKER_SSHAGENT="-v /run/host-services/ssh-auth.sock:/run/host-services/ssh-auth.sock -e SSH_AUTH_SOCK=/run/host-services/ssh-auth.sock"

and Linux::

    export DOCKER_SSHAGENT="-v $SSH_AUTH_SOCK:$SSH_AUTH_SOCK -e SSH_AUTH_SOCK"

Creating a development container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

!!! FIXME switch the 1234 port(s) to the port from src/ml_trial_task/defaultconfig.py !!!

Build image, create container and start it::

    docker build --progress plain --ssh default --target devel_shell -t ml_trial_task:devel_shell .
    docker create --name ml_trial_task_devel -p 1234:1234 -v "$(pwd):/app" -it -v /tmp:/tmp $(echo $DOCKER_SSHAGENT) ml_trial_task:devel_shell
    docker start -i ml_trial_task_devel

pre-commit considerations
^^^^^^^^^^^^^^^^^^^^^^^^^

If working in Docker instead of native env you need to run the pre-commit checks in docker too::

    docker exec -i ml_trial_task_devel /bin/bash -c "pre-commit install"
    docker exec -i ml_trial_task_devel /bin/bash -c "pre-commit run --all-files"

You need to have the container running, see above. Or alternatively use the docker run syntax but using
the running container is faster::

    docker run -it --rm -v "$(pwd):/app" ml_trial_task:devel_shell -c "pre-commit run --all-files"

Test suite
^^^^^^^^^^

You can use the devel shell to run py.test when doing development, for CI use
the "tox" target in the Dockerfile::

    docker build --progress plain --ssh default --target tox -t ml_trial_task:tox .
    docker run -it --rm -v "$(pwd):/app" $(echo $DOCKER_SSHAGENT) ml_trial_task:tox

Production docker
^^^^^^^^^^^^^^^^^

!!! FIXME switch the 1234 port(s) to the port from src/ml_trial_task/defaultconfig.py !!!

There's a "production" target as well for running the application and remember to change that architecture tag to arm64 if building on ARM::

    docker build --progress plain --ssh default --target production -t ml_trial_task:amd64-latest .
    docker run --rm -it --name ml_trial_task_config ml_trial_task:amd64-latest ml_trial_task --defaultconfig >config.toml
    docker run -it --name ml_trial_task -v "$(pwd)/config.toml:/app/docker_config.toml" -p 1234:1234 -v /tmp:/tmp $(echo $DOCKER_SSHAGENT) ml_trial_task:amd64-latest


Local Development
-----------------

!!! FIXME: Remove the repo init from this document after you have done it. !!!

TLDR:

- Create and activate a Python 3.11 virtualenv (assuming virtualenvwrapper)::

    mkvirtualenv -p $(which python3.11) my_virtualenv

- Init your repo (first create it on-line and make note of the remote URI)::

    git init && git add .  # This should have been done automatically by cookiecutter
    git commit -m 'Cookiecutter stubs'
    git remote add origin MYREPOURI
    git branch -m main
    git push origin main

- change to a branch::

    git checkout -b my_branch

- install Poetry: https://python-poetry.org/docs/#installation
- Install project deps and pre-commit hooks::

    poetry install
    git add poetry.lock
    pre-commit install
    pre-commit run --all-files

If you get weird errors about missing packages from pre-commit try running it with "poetry run pre-commit".

- Ready to go, try the following::

    ml_trial_task --defaultconfig >config.toml
    ml_trial_task -vv config.toml

Remember to activate your virtualenv whenever working on the repo, this is needed
because pylint and mypy pre-commit hooks use the "system" python for now (because reasons).

Running "pre-commit run --all-files" and "py.test -v" regularly during development and
especially before committing will save you some headache.

Monitoring ZMQ messgaes
^^^^^^^^^^^^^^^^^^^^^^^

Datastreamservicelib that we depend on provides a tool called testsubscriber::

    testsubscriber -s ipc:///tmp/ml_trial_task_pub.sock -t "HEARTBEAT"

set -t (--topic) to the prefix you want to filter for. If you expect ImageMessages add "-i" to make life less binary.

Pro tip: -t "" give you ALL messages published in the socket, it can be useful but it is generally overwhelming.
