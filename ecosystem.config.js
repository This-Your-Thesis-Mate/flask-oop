module.exports = {
    apps: [
        {
            name: "celery-worker",
            script: "./celery_worker.py",
            interpreter: "python",
            instances: 1,
            exec_mode: "fork",
            watch: false,
            max_memory_restart: "500M",
            error_file: "./logs/celery-error.log",
            out_file: "./logs/celery-out.log",
            log_date_format: "YYYY-MM-DD HH:mm:ss Z",
            env: {
                "PYTHONUNBUFFERED": "1"
            }
        },
        {
            name: "flower",
            script: ".",
            interpreter: "bash",
            instances: 1,
            exec_mode: "fork",
            watch: false,
            max_memory_restart: "300M",
            error_file: "./logs/flower-error.log",
            out_file: "./logs/flower-out.log",
            log_date_format: "YYYY-MM-DD HH:mm:ss Z",
            args: "-c 'celery -A app.celery_app flower --port=5555'",
            env: {
                "PYTHONUNBUFFERED": "1"
            }
        }
    ]
};
