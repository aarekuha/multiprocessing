#### Rabbit-mq 3.9.3
```bash
docker compose up -d --build
```

#### Start
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python main.py

deactivate
```

#### Clean
```bash
docker compose stop
docker compose down
rm -rf venv
```
