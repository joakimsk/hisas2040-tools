import matplotlib.pyplot as plt
import numpy as np

def plot_image_and_graph(image_data, residual_tvg, beam_pattern):
    """
    Plots an 8-bit sonar image next to a graph showing residual TVG and beam pattern corrections.
    """
    # Normalize image data to 8-bit range (0-255)
    normalized_image = (255 * (image_data - np.min(image_data)) / (np.max(image_data) - np.min(image_data))).astype(np.uint8)

    # Create the figure
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), gridspec_kw={'width_ratios': [2, 1]})

    # Plot the 8-bit image
    axes[0].imshow(normalized_image, cmap='gray', aspect='auto')
    axes[0].set_title('Corrected Sonar Image (8-bit)')
    axes[0].set_xlabel('Across-Track Distance')
    axes[0].set_ylabel('Along-Track Distance')
    plt.colorbar(axes[0].images[0], ax=axes[0], fraction=0.046, pad=0.04, label='Amplitude')

    # Plot the graph with TVG and Beam Pattern
    axes[1].plot(residual_tvg, label='Residual TVG', color='blue')
    axes[1].plot(beam_pattern, label='Beam Pattern', color='green')
    axes[1].set_title('Correction Factors')
    axes[1].set_xlabel('Sample Index')
    axes[1].set_ylabel('Amplitude')
    axes[1].legend()
    axes[1].grid(True)

    # Adjust layout and display
    plt.tight_layout()
    plt.show()

# Generate example sonar image data
np.random.seed(42)  # For reproducibility
image_data_example = np.random.rand(100, 256) * 50  # Random data simulating sonar intensities

# Generate synthetic Residual TVG and Beam Pattern data
residual_tvg_example = np.linspace(1, 2, 256) + 0.1 * np.random.rand(256)  # Linear trend with noise
beam_pattern_example = np.sin(np.linspace(0, 2 * np.pi, 100)) + 1  # Sinusoidal beam pattern

# Plot the image and graph
plot_image_and_graph(image_data_example, residual_tvg_example, beam_pattern_example)
