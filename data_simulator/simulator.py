# simulator.py

import csv
import random
from datetime import datetime, timedelta

import config
from utils import generate_metrics, apply_cascading_failure, check_natural_failure

OUTPUT_FILE = "../data/api_logs.csv"


def run_simulation():
    current_time = datetime.now()
    base_load = 100

    with open(OUTPUT_FILE, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow([
            "timestamp",
            "service",
            "latency",
            "cpu",
            "memory",
            "requests",
            "errors",
            "failure"
        ])

        for i in range(config.TOTAL_REQUESTS):

            # traffic spike
            if random.random() < config.SPIKE_PROBABILITY:
                base_load += random.randint(50, 200)

            # keep load in range
            base_load = max(config.BASE_LOAD_MIN, min(base_load, config.BASE_LOAD_MAX))

            # database failure trigger
            db_failed = random.random() < config.DB_FAILURE_PROB

            for service in config.SERVICES:

                latency, cpu, memory, requests = generate_metrics(base_load)

                # cascading failure logic
                latency, cpu, errors, failure = apply_cascading_failure(
                    service, db_failed, latency, cpu
                )

                # natural failure check
                nat_fail, nat_err = check_natural_failure(latency, cpu)

                if nat_fail:
                    failure = 1
                    errors = 1

                writer.writerow([
                    current_time,
                    service,
                    int(latency),
                    int(cpu),
                    int(memory),
                    int(requests),
                    errors,
                    failure
                ])

            current_time += timedelta(seconds=1)

    print("✅ DONE: data/api_logs.csv generated")


if __name__ == "__main__":
    run_simulation()