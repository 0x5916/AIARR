import math

class PointStabilizer:
    def __init__(self, alpha_min: float = 0.05, alpha_max: float = 0.35, threshold: float = 100.0):
        """
        Initializes the point stabilizer with inverted dynamic alpha.

        Args:
            alpha_min (float): Minimum smoothing factor for small movements.
            alpha_max (float): Maximum smoothing factor for large movements.
            threshold (float): Distance threshold to switch between min and max alpha.
        """
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
        self.threshold = threshold
        self.stabilized_point: tuple[float, float] = (0.0, 0.0)
        self.is_initialized = False

    def calculate_dynamic_alpha(self, distance: float) -> float:
        """
        Calculates inverted dynamic alpha based on the distance.

        Args:
            distance (float): Distance between the current and new points.

        Returns:
            float: The calculated alpha value.
        """
        if distance > self.threshold:
            return self.alpha_max
        else:
            return self.alpha_min + (self.alpha_max - self.alpha_min) * (distance / self.threshold)

    def stabilize(self, new_point: tuple[int, int]) -> tuple[int, int]:
        """
        Stabilizes the given point using an inverted dynamic alpha.

        Args:
            new_point (Tuple[float, float]): The new point to stabilize.

        Returns:
            Tuple[float, float]: The stabilized point.
        """
        if not self.is_initialized:
            self.stabilized_point = new_point
            self.is_initialized = True
            return self.stabilized_point

        spx, spy = self.stabilized_point[0], self.stabilized_point[1]
        npx, npy = new_point[0], new_point[1]
        distance = math.sqrt(math.pow(npx - spx, 2) + math.pow(npy - spy, 2))

        # Calculate inverted dynamic alpha based on distance
        alpha = self.calculate_dynamic_alpha(distance)

        # Apply exponential moving average with dynamic alpha
        x_stabilized = alpha * npx + (1 - alpha) * spx
        y_stabilized = alpha * npy + (1 - alpha) * spy

        self.stabilized_point = (int(x_stabilized), int(y_stabilized))
        return self.stabilized_point
