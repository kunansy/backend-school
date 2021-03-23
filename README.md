# _Candy Delivery App_ Documentation
Version 1.0

## Installing
1. Download the source code.
2. Create virtual environment and activate it:
```shell
python3 -m venv venv/
. venv/bin/activate
```
3. Install all requirements: `pip install -r requirements.txt`.
4. Create `.env` file in the API root folder:
```editorconfig
HOST='0.0.0.0'
PORT=8080
DEBUG=False
LOG_FOLDER=./logs/
DB_DSN='postgres://postgres:12345@127.0.0.1:5432/candy_shop'
```

> To tun server or tests you mast have database working.

## Running
From root folder of the API:
```shell
python3 src/server.py
```


## Docs
You can see docs, examples and try to use the service on `http://<host>:8080/swagger`.


## Testing
Go to `tests/` folder and run tests:
```shell
pytest -svv tests/
```

## Benchmark
Also, you can see service productivity (RPS) and its performance.

1. Install benchmark soft
```shell
sudo apt install apache2-utils
```
2. Run benchmark
```shell
ab -n 5000 -c 500 http://<host>:8080/
```


## Requires
* Python>=3.8
* docker