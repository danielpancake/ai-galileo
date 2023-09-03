# How to run

```bash
docker run -d -p 27017:27017 --name m1 mongo
docker run -d -p 6379:6379 --name r1 redis
docker ps

python worker.py stories

python main.py --verbose
```
