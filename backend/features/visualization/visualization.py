import matplotlib.pyplot as plt

data = {
  "drivers": [
    { "id": 1, "start_location": [0.0, 0.0], "vehicle_type": "ev", "available": True },
    { "id": 2, "start_location": [5.0, 5.0], "vehicle_type": "fuel", "available": True }
  ],
  "tasks": [
    { 
      "id": 101, 
      "pickup": { "location": [1.0, 2.0] }, 
      "dropoff": { "location": [12.0, 4.0] } 
    },
    { 
      "id": 102, 
      "pickup": { "location": [2.0, 1.0] }, 
      "dropoff": { "location": [6.0, 8.0] } 
    }
  ]
}

def visualize_map(data):
    fig, ax = plt.subplots(figsize=(10, 8))
    
    for driver in data['drivers']:
        x, y = driver['start_location']
        
        color = 'green' if driver['vehicle_type'] == 'ev' else 'red'
        
        ax.scatter(
            x, 
            y, 
            color=color, 
            s=150, 
            marker='o', 
            label=f"Driver {driver['vehicle_type'].upper()}", 
            edgecolors='black'
        )
        
        ax.text( 
            x + 0.2, 
            y, 
            f"Driver {driver['id']}", 
            fontsize=9, 
            fontweight='bold'
        )

    for task in data['tasks']:
        pickup_x, pickup_y = task['pickup']['location']
        dropoff_x, dropoff_y = task['dropoff']['location']
        
        ax.scatter(
            pickup_x, 
            pickup_y, 
            color='blue', 
            marker='s', 
            s=100, 
            label='Task Pickup Point'
        )

        ax.text(
            pickup_x + 0.2, 
            pickup_y, 
            f"Task {task['id']} (Start)", 
            fontsize=9,
            fontweight='bold'
        )
        
        ax.scatter(
            dropoff_x, 
            dropoff_y, 
            color='blue', 
            marker='x', 
            s=100,
            label='Task Dropoff Point'
        )
        
        ax.text(
            dropoff_x + 0.2, 
            dropoff_y, 
            f"Task {task['id']} (End)", 
            fontsize=9,
            fontweight='bold'
        )
        
        ax.arrow(
            pickup_x, 
            pickup_y, 
            (dropoff_x - pickup_x), 
            (dropoff_y - pickup_y), 
            head_width=0.1, 
            head_length=0.1, 
            facecolor='lightblue', 
            edgecolor='lightblue', 
            linestyle='--'
        )

    ax.set_title("Driver & Task Visualization")
    ax.set_xlabel("X (Longitude)")
    ax.set_ylabel("Y (Latitude)")
    ax.grid(True, linestyle='--', alpha=0.3)
    
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())

    plt.show()

if __name__ == "__main__":
    visualize_map(data)