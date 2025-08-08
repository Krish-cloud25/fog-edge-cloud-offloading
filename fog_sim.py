import simpy
import random
import matplotlib.pyplot as plt
import boto3
import os

# ---- CONFIG ----
NUM_SENSORS = 10
NUM_FOG_NODES = 2
FOG_PROCESSING_TIME = 2
CLOUD_PROCESSING_TIME = 6
NETWORK_DELAY_TO_CLOUD = 3
SIM_DURATION = 100
OFFLOAD_PROB = 0.3
S3_BUCKET_NAME = "ifogedege"

# ---- METRICS ----
task_completion_times = []
fog_task_count = 0
cloud_task_count = 0

def iot_sensor(env, sensor_id, fog_nodes):
    while True:
        yield env.timeout(random.expovariate(1/5))
        fog_node = random.choice(fog_nodes)
        env.process(fog_node_process(env, f"Task_from_{sensor_id}", fog_node))

def fog_node_process(env, task_id, fog_node_id):
    global fog_task_count, cloud_task_count
    arrival_time = env.now

    if random.random() < OFFLOAD_PROB:
        yield env.timeout(NETWORK_DELAY_TO_CLOUD)
        yield env.process(cloud_node_process(env, task_id))
        cloud_task_count += 1
    else:
        yield env.timeout(FOG_PROCESSING_TIME)
        fog_task_count += 1

    completion_time = env.now - arrival_time
    task_completion_times.append(completion_time)

def cloud_node_process(env, task_id):
    yield env.timeout(CLOUD_PROCESSING_TIME)

def save_results_to_s3(text_content, graph_path):
    s3 = boto3.client("s3")

    # Upload text file
    with open("simulation_results.txt", "w") as f:
        f.write(text_content)
    s3.upload_file("simulation_results.txt", S3_BUCKET_NAME, "simulation_results.txt")

    # Upload graph
    s3.upload_file(graph_path, S3_BUCKET_NAME, "completion_times.png")

    print(f"\n✅ Uploaded results and graph to S3 bucket: {S3_BUCKET_NAME}")

def run_simulation():
    env = simpy.Environment()
    fog_nodes = [f"FogNode_{i}" for i in range(NUM_FOG_NODES)]

    for i in range(NUM_SENSORS):
        env.process(iot_sensor(env, i, fog_nodes))

    env.run(until=SIM_DURATION)

    avg_time = sum(task_completion_times) / len(task_completion_times)
    max_time = max(task_completion_times)
    min_time = min(task_completion_times)

    # Prepare results text
    results_text = (
        f"--- Simulation Results ---\n"
        f"Total tasks processed: {len(task_completion_times)}\n"
        f"Processed in Fog: {fog_task_count}\n"
        f"Processed in Cloud: {cloud_task_count}\n"
        f"Average completion time: {avg_time:.2f} seconds\n"
        f"Max completion time: {max_time:.2f} seconds\n"
        f"Min completion time: {min_time:.2f} seconds\n"
    )

    print(results_text)

    # Create graph
    plt.figure(figsize=(8, 5))
    plt.hist(task_completion_times, bins=10, color="skyblue", edgecolor="black")
    plt.title("Task Completion Time Distribution")
    plt.xlabel("Completion Time (seconds)")
    plt.ylabel("Number of Tasks")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    graph_path = "completion_times.png"
    plt.savefig(graph_path)

    # Show graph locally
    plt.show()

    # Save both results & graph to S3
    save_results_to_s3(results_text, graph_path)

if __name__ == "__main__":
    run_simulation()
