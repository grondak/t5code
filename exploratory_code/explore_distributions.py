import numpy as np
import matplotlib.pyplot as plt

# Parameters for the log-normal distribution
mu = 2.6  # Mean of the log (adjust to center around 15-20 tons)
sigma = 0.7  # Standard deviation of the log (adjust for tail weight)

# Generate random cargo loads
loads = np.random.lognormal(mean=mu, sigma=sigma, size=1)

# Filter loads to a minimum of 1 ton and max of 100 tons
loads = loads[loads >= 1]
loads = loads[loads <= 100]
# Truncate the loads to ensure a minimum of 1 ton and clip to integers
loads = np.clip(loads, a_min=1, a_max=None)  # Ensure minimum of 1 ton
loads = np.rint(loads).astype(int)  # Round to nearest integer


# Plot the distribution
plt.hist(loads, bins=100, density=True, alpha=0.6, color="g")
plt.title("Log-Normal Distribution of Cargo Loads")
plt.xlabel("Cargo Load (tons)")
plt.ylabel("Density")
plt.show()

# Example: Inspect some sample loads
print("Sample cargo loads:", loads[:10])
