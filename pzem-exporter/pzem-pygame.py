import pygame
import requests
import time
import os

# Initialize Pygame
pygame.init()

# Set the framebuffer device
framebuffer_device = "/dev/fb0"
os.environ["SDL_FBDEV"] = framebuffer_device

# Set fullscreen mode
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
width, height = screen.get_size()

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Set up font
font_large = pygame.font.Font(None, 60)  # Font size for title
font_small = pygame.font.Font(None, 50)  # Updated smaller font size

# Prometheus server details
prometheus_url = "http://192.168.0.103:9090/api/v1/query"

# Metric names
metrics = {
    "watts": "watts",
    "voltage": "voltage",
    "current": "current",
    "energy": "energy",
    "power_factor": "power_factor",
    "frequency": "frequency",
}

# Function to query Prometheus
def query_prometheus(metric_name):
    try:
        response = requests.get(prometheus_url, params={"query": metric_name}, timeout=5)
        response.raise_for_status()
        data = response.json()
        results = data.get("data", {}).get("result", [])
        if results:
            value = float(results[0]["value"][1])  # Extract the metric value
            print(f"Metric '{metric_name}': {value}")
            return value
        else:
            print(f"Metric '{metric_name}' not found or no data available.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error querying Prometheus for '{metric_name}': {e}")
        return None
    except ValueError:
        print(f"Invalid JSON response for '{metric_name}': {response.text}")
        return None

# Function to display text on the screen
def display_text(text, x, y, font, color=WHITE):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

# Main loop
running = True
while running:
    # Clear the screen
    screen.fill(BLACK)

    # Query Prometheus for metrics
    watts = query_prometheus(metrics["watts"])
    voltage = query_prometheus(metrics["voltage"])
    current = query_prometheus(metrics["current"])
    energy = query_prometheus(metrics["energy"])
    power_factor = query_prometheus(metrics["power_factor"])
    frequency = query_prometheus(metrics["frequency"])

    # Centered title
    title = "Power Metrics"
    title_surface = font_large.render(title, True, BLUE)
    title_width = title_surface.get_width()
    screen.blit(title_surface, ((width - title_width) // 2, 20))

    # Display metrics
    display_text("Watts:", 50, 100, font_small)
    display_text(f"{watts:.2f} W" if watts is not None else "N/A", 300, 100, font_small, GREEN if watts else RED)

    display_text("Voltage:", 50, 160, font_small)
    display_text(f"{voltage:.2f} V" if voltage is not None else "N/A", 300, 160, font_small, GREEN if voltage else RED)

    display_text("Current:", 50, 220, font_small)
    display_text(f"{current:.2f} A" if current is not None else "N/A", 300, 220, font_small, GREEN if current else RED)

    display_text("Energy:", 50, 280, font_small)
    display_text(f"{energy:.2f} Wh" if energy is not None else "N/A", 300, 280, font_small, GREEN if energy else RED)

    display_text("PF:", 50, 340, font_small)
    display_text(f"{power_factor:.2f}" if power_factor is not None else "N/A", 300, 340, font_small, GREEN if power_factor else RED)

    display_text("Freq:", 50, 400, font_small)
    display_text(f"{frequency:.2f} Hz" if frequency is not None else "N/A", 300, 400, font_small, GREEN if frequency else RED)

    # Update display
    pygame.display.update()

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # Update every 5 seconds
    time.sleep(5)

# Quit Pygame
pygame.quit()
