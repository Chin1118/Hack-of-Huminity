import matplotlib.pyplot as plt
import matplotlib.animation as animation
import json
import os

# Load data from JSON file
def load_system_data():
    json_path = os.path.join(os.path.dirname(__file__), '../../utils/data.json')
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: data.json not found at {json_path}")
        return {"drivers": [], "tasks": []}


def visualize_map(frame):
    # Load fresh data from JSON file each time
    system_data = load_system_data()
    axes.clear()

    # Lists to keep track of all coordinates for auto-scaling
    all_x_coords = []
    all_y_coords = []
    
    for task in system_data['tasks']:
        pickup_x, pickup_y = task['pickup']['location']
        dropoff_x, dropoff_y = task['dropoff']['location']

        # Add task coordinates to tracking lists
        all_x_coords.extend([pickup_x, dropoff_x])
        all_y_coords.extend([pickup_y, dropoff_y])
        
        axes.scatter(
            pickup_x, 
            pickup_y, 
            color='blue', 
            marker='s', 
            s=100, 
            label='Task Pickup Point'
        )
        
        axes.text(
            x=pickup_x + 0.2, 
            y=pickup_y, 
            s=f"Task {task['id']}", 
            fontsize=9, 
            color='blue'
        )

        axes.scatter(
            dropoff_x, 
            dropoff_y, 
            color='blue', 
            marker='x', 
            s=100, 
            label='Task Dropoff Point'
        )

        axes.arrow(
            x=pickup_x, 
            y=pickup_y, 
            dx=(dropoff_x - pickup_x), 
            dy=(dropoff_y - pickup_y), 
            head_width=0.2, 
            facecolor='lightblue', 
            edgecolor='lightblue', 
            linestyle='--'
        )

    for driver in system_data['drivers']:
        x, y = driver['start_location']

        # Add driver coordinates to our tracking lists
        all_x_coords.append(x)
        all_y_coords.append(y)
        
        marker_color = 'green' if driver['vehicle_type'] == 'ev' else 'red'
        
        axes.scatter(
            x, 
            y, 
            color=marker_color, 
            s=150, 
            marker='o', 
            label=f"Driver {driver['vehicle_type'].upper()}", 
            edgecolors='black'
        )
        
        axes.text(
            x + 0.2, 
            y, 
            s=f"Driver {driver['id']}", 
            fontsize=12, 
            fontweight='bold'
        )

    axes.set_title("Real-Time Visualization")
    axes.set_xlabel("X")
    axes.set_ylabel("Y")
    axes.grid(True, linestyle='--', alpha=0.6)

    # Auto-scale axes based on all coordinates
    padding = 2
    min_x, max_x = min(all_x_coords), max(all_x_coords)
    min_y, max_y = min(all_y_coords), max(all_y_coords) 
    axes.set_xlim(min_x - padding, max_x + padding)
    axes.set_ylim(min_y - padding, max_y + padding)

    handles, labels = plt.gca().get_legend_handles_labels()
    unique_labels = dict(zip(labels, handles))
    axes.legend(unique_labels.values(), unique_labels.keys(), loc='upper left')


# Initialize and start the real-time visualization
def start_visualization():  
    global figure, axes, ani
    figure, axes = plt.subplots(figsize=(10, 8))
    ani = animation.FuncAnimation(figure, visualize_map, interval=1000)
    plt.show()


# Testing
if __name__ == "__main__":
    start_visualization()