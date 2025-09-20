cd mock-qmatic/

python3 -m venv .venv 
source .venv/bin/activate
pip install flask 
python server.py

cd bot/
python3 -m venv .venv 
source .venv/bin/activate
pip install --upgrade pip
pip install flask playwright
python -m playwright install
sudo apt-get install libnspr4
sudo apt-get install libnss3
sudo apt-get install libasound2

python book_appointment.py
PWDEBUG=1 HEADLESS=false python book_appointment_real.py
BREAK_AT=after_step1,after_step2 HEADLESS=false SLOW_MO_MS=200 python book_appointment_real.py
HEADLESS=true SLOW_MO_MS=0 python book_appointment_real.py
playwright show-trace artifacts/trace.zip




CONTACT = {
    "name": "Monica Pérez Villarroel",
    "id": "Z0428685Q",        # DNI/NIE/Pasaporte
    "email": "monicaperezvillarroel060@gmail.com",
    "phone": "613304514",
}


# From the folder containing docker-compose.yml
docker-compose build --no-cache
# One-shot manual run to test:
docker-compose run --rm bot

# Start the scheduler daemon:
docker-compose up -d scheduler

# Watch logs (scheduled runs)
docker-compose logs -f scheduler
