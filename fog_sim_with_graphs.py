import simpy
import random
import matplotlib.pyplot as plt

# Simulation parameters
NUM_SENSORS = 5
NUM_FOG_NODES = 1
NUM_TASKS = 200
FOG_PROCESSING_TIME = 2
CLOUD_PROCESSING_TIME = 5
NETWORK_DELAY = 2
OFFLOAD_PROB = 0.25  # Probability that a task is offloaded to the cloud

random.seed(42)  # For reproducibility

completion_times = []
where_processed = []

def sensor(env, fog_node, sensor_id):
    for i in range(NUM_TASKS // NUM_SENSORS):
        arrival_time = env.now
        task = {'id': f'sensor{sensor_id}_task{i}', 'arrival_time': arrival_time}
        env.process(fog_node.process_task(env, task))
        yield env.timeout(random.expovariate(1.0))  # Random interval between tasks

class FogNode:
    def __init__(self, env):
        self.env = env

    def process_task(self, env, task):
        if random.random() < OFFLOAD_PROB:
            # Offload to cloud
            yield env.timeout(NETWORK_DELAY)
            yield env.process(cloud_node.process_task(env, task))
            where_processed.append('cloud')
        else:
            # Process in fog
            yield env.timeout(FOG_PROCESSING_TIME)
            completion_time = env.now - task['arrival_time']
            completion_times.append(completion_time)
            where_processed.append('fog')

class CloudNode:
    def __init__(self, env):
        self.env = env

    def process_task(self, env, task):
        yield env.timeout(CLOUD_PROCESSING_TIME)
        completion_time = env.now - task['arrival_time']
        completion_times.append(completion_time)

# Setup simulation
env = simpy.Environment()
fog_node = FogNode(env)
cloud_node = CloudNode(env)

for i in range(NUM_SENSORS):
    env.process(sensor(env, fog_node, i))

env.run()

# Collect stats
num_fog = where_processed.count('fog')
num_cloud = where_processed.count('cloud')

print("\n--- Simulation Results ---")
print(f"Total tasks processed: {num_fog + num_cloud}")
print(f"Processed in Fog: {num_fog}")
print(f"Processed in Cloud: {num_cloud}")
print(f"Average completion time: {sum(completion_times)/len(completion_times):.2f} seconds")
print(f"Max completion time: {max(completion_times):.2f} seconds")
print(f"Min completion time: {min(completion_times):.2f} seconds")

# --- PLOT BAR CHART (Fog vs Cloud tasks) ---
plt.figure(figsize=(6, 4))
plt.bar(['Fog', 'Cloud'], [num_fog, num_cloud], color=['#4CAF50', '#2196F3'])
plt.title('Number of Tasks Processed')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig('tasks_fog_vs_cloud.png')
plt.close()

# --- PLOT HISTOGRAM (Task completion times) ---
plt.figure(figsize=(6, 4))
plt.hist(completion_times, bins=15, color='#FF9800', edgecolor='black')
plt.title('Task Completion Time Distribution')
plt.xlabel('Completion Time (s)')
plt.ylabel('Number of Tasks')
plt.tight_layout()
plt.savefig('completion_times_hist.png')
plt.close()

print("\nGraphs saved: 'tasks_fog_vs_cloud.png' and 'completion_times_hist.png'")
