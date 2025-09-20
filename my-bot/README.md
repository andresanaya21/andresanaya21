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

CONTACT = {
    "name": "Monica Pérez Villarroel",
    "id": "Z0428685Q",        # DNI/NIE/Pasaporte
    "email": "monicaperezvillarroel060@gmail.com",
    "phone": "613304514",
}