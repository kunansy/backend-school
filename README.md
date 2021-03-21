# _Candy Delivery App_ Documentation
<small> version 1.0 </small>

## Installing
1. Download the source code.
2. Create virtual environment and activate it:
   ```shell
   python3 -m venv venv/
   . venv/bin/activate
   ```
3. Install all requirements: `pip install -r requirements.txt`.
4. Create `.env` file in project root folder:
```editorconfig
HOST='0.0.0.0'
PORT=8080
DEBUG=False
ACCESS_LOG=True
FILE_LOGGING=True
LOG_FOLDER=./logs/
```


## Running
```shell
python3 src/server.py
```


## Docs
You can see docs, examples and try to use the service on `127.0.0.1:8080/swagger`.


## Testing
Run tests:
```shell
pytest -svv tests/
```

> To run tests you should have `docker` installed on the machine.


## Benchmark
Also, you can see service productivity (RPS):
```shell

```


## Requires
* Python3.9
* docker