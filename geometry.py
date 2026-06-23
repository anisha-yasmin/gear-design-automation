import numpy as np
import os

def calculate_gear_parameters(module, num_teeth, pressure_angle_deg):
    """Calculates fundamental circle radii for a spur gear."""
    phi = np.radians(pressure_angle_deg)
    
    # Radii calculations
    r_pitch = (module * num_teeth) / 2.0
    r_base = r_pitch * np.cos(phi)
    r_addendum = r_pitch + module
    r_dedendum = r_pitch - (1.25 * module) # Standard clearance factor
    
    return r_base, r_pitch, r_addendum, r_dedendum

def generate_involute_points(r_base, r_addendum, num_points=50):
    """Generates 2D coordinates for a single involute curve profile."""
    # Find the maximum roll angle theta where the curve hits the tip (addendum)
    # Using the geometry relation: r_addendum^2 = r_base^2 * (1 + theta^2)
    max_theta = np.sqrt((r_addendum / r_base)**2 - 1)
    
    # Generate theta array from 0 (base circle) to max_theta (tooth tip)
    theta = np.linspace(0, max_theta, num_points)
    
    # Parametric equations of an involute profile
    x = r_base * (np.sin(theta) - theta * np.cos(theta))
    y = r_base * (np.cos(theta) + theta * np.sin(theta))
    
    return x, y

def export_to_csv(x, y, filename="output_profile.csv"):
    """Saves coordinate points to a CSV file for CAD macro import."""
    os.makedirs("exports", exist_ok=True)
    filepath = os.path.join("exports", filename)
    
    data = np.column_stack((x, y, np.zeros_like(x))) # Adding a Z=0 coordinate for 3D CAD space
    np.savetxt(filepath, data, delimiter=",", header="X,Y,Z", comments="")
    print(f"🎉 Geometry successfully exported to: {filepath}")

# Quick script verification run
if __name__ == "__main__":
    # Example Design Inputs
    M = 2.0         # Module (mm)
    N = 24          # Number of teeth
    ALPHA = 20.0    # Pressure Angle (degrees)
    
    rb, rp, ra, rd = calculate_gear_parameters(M, N, ALPHA)
    x_pts, y_pts = generate_involute_points(rb, ra)
    
    export_to_csv(x_pts, y_pts, "single_tooth_profile.csv")
