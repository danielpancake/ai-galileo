# AI-Galileo

AI-Galileo is an interactive chatbot that produces voiced episode scripts for the show in the style of Galileo.

## Environment variables

The following environment variables are required to run the application. You must set them in a `.env` file in the root directory of the project.

| Key                     | Description                               | Default  |
| ----------------------- | ----------------------------------------- | -------- |
| `MONGO_URI`             | MongoDB URI                               | -        |
| `CLAUDE_API_COOKIE`     | Claude's cookie                           | -        |
| `OPENAI_API_KEY`        | ChatGPT API key                           | -        |
| `PREFERED_TEXT_GEN_API` | (Optional) String of `openai` or `claude` | `openai` |

## How to run

To run the application, you must have Docker installed. Then, run the following commands:

```bash
docker run -d -p 27017:27017 --name m1 mongo
docker run -d -p 6379:6379 --name r1 redis
```

These commands will start a MongoDB and a Redis container. You can check that they are running by running `docker ps`.

Then, you can run the application:

```bash
python main.py --rq-start
```

To see all the available options, run `python main.py --help`.
