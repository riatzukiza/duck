const path = require('path');

module.exports = {
    apps: [
        {
            name: "tts",
            cwd: "./services/tts",
            script: "./services/tts/run.sh",
            interpreter:"bash",
            "exec_mode": "fork",
            watch: ["./services/tts"],
            instances: 1,
            autorestart: true,
            env: {

                PYTHONPATH: path.resolve(__dirname),
                PYTHONUNBUFFERED: "1",
                FLASK_APP: "app.py",
                FLASK_ENV: "production",
            },
            restart_delay: 10000,
            kill_timeout: 10000 

        },
        {
            name: "stt",
            cwd: "./services/stt",
            script: "./services/stt/run.sh",
            interpreter: "bash",
            exec_mode: "fork",
            watch: ["./services/stt"],
            instances: 1,
            autorestart: true,
            out_file: "./logs/stt-out.log",
            error_file: "./logs/stt-err.log",
            merge_logs: true,
            env: {
                PYTHONUNBUFFERED: "1",
                PYTHONPATH: path.resolve(__dirname),
            },

            restart_delay: 10000,
            kill_timeout: 10000 // wait 5s before SIGKILL
        },
        {
            name: "discord_indexer",
            cwd: "./services/discord_indexer",
            script: "python",
            args: "-m pipenv run python -m main",

            "exec_mode": "fork",
            watch: ["./services/discord_indexer"],
            instances: 1,
            autorestart: true,
            env: {
                PYTHONPATH: path.resolve(__dirname),
                PYTHONUTF8: "1",
                PYTHONUNBUFFERED: "1",
            },

            restart_delay: 10000,
            kill_timeout: 10000
        },
        {
            "name": "discord_speaker_js",
            "watch": ["./services/discord_speaker_js/src"],
            "cwd": "./services/discord_speaker_js",
            "script": "src/index.ts",
            "interpreter": "node",
            "node_args": ["--loader", "ts-node/esm"],
            "autorestart": true,
            "env_file": ".env",

            restart_delay: 10000,
            kill_timeout: 10000 // wait 5s before SIGKILL

        },
        {
            "name": "embedder",
            "watch": ["./services/embedder/src"],
            "cwd": "./services/embedder",
            "interpreter": "node",
            "script": "./src/index.ts",
            // "script":"./services/embedder/src/index.ts",
            "node_args": ["--loader", "ts-node/esm"],
            "autorestart": true,
            "env_file": ".env"

        },
        {
            "name": "chromadb",
            "script": "python",
            "args": "-m pipenv run chroma run --path ./chroma_data",
        }

    ]
};
