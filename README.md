# constellation
Constellation is a landing page to display all of the results of Kuiper Linux testing on hardware.

Requirements on running:

cloned constellation
cloned telemetry
virtual environment of constellation


--> Constellation setup <--
(Recommended: Run to vm)
1. Create owner folder or go to your preferred folder in your linux server.
        mkrdir <owner_folder> or cd <owner_folder>
2. Clone Constellation and Telemetry
        git clone https://github.com/sdgtt/constellation.git
        git clone https://github.com/sdgtt/telemetry.git
3. Create virtual environment, to create type this to your terminal:
    python3 -m virtualenv <env_folder_name>
4. Go to Telemetry cloned folder and install requirements
       cd telemetry/
       pip install -r requirements.txt
       pip install -r requirements_dev.txt
       cd ..
5. Run or activate your virtualenv
        source envConstellation/bin/activate

6. Go to Constellation cloned folder and install requirements
        pip install telemetry
        pip install -r requirements.txt
        pip install -r requirements_dev.txt
7. Once installed, run the in development mode.
        export FLASK_ENV=development
        export ES=192.168.10.12
        flask run --host=0.0.0.0 --port=5002
