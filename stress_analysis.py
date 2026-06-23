import numpy as np

def calculate_lewis_form_factor(num_teeth):
    """Approximates the Lewis Form Factor for a standard 20-degree pressure angle gear."""
    return 0.154 - (0.912 / num_teeth)

def analyze_gear_stresses(torque_nm, module, num_teeth_1, num_teeth_2, face_width_mm, pressure_angle_deg=20.0):
    """
    Calculates root bending stress and surface contact stress for a meshing gear pair.
    Assumes standard steel properties (E = 210 GPa, nu = 0.3).
    """
    # 1. Kinematic & Load Preliminaries
    r_pitch_1 = (module * num_teeth_1) / 2.0 / 1000.0  # Convert mm to meters
    d_pitch_1_mm = module * num_teeth_1
    
    # Tangential Force Wt (Newtons) = Torque (Nm) / Radius (m)
    W_t = torque_nm / r_pitch_1
    
    # Gear Ratio
    G = num_teeth_2 / num_teeth_1
    phi = np.radians(pressure_angle_deg)
    
    # 2. Bending Stress (Lewis Equation)
    Y = calculate_lewis_form_factor(num_teeth_1)
    # sigma_b = Wt / (b * m * Y) -> convert face_width and module to mm if staying in MPa
    bending_stress_mpa = W_t / (face_width_mm * module * Y)
    
    # 3. Contact Stress (Hertzian Contact approximation for Steel)
    C_p = 191.0  # Elastic coefficient for steel (MPa^0.5)
    I = (np.sin(phi) * np.cos(phi) / 2.0) * (G / (G + 1))
    
    contact_stress_mpa = C_p * np.sqrt(W_t / (face_width_mm * d_pitch_1_mm * I))
    
    return bending_stress_mpa, contact_stress_mpa

if __name__ == "__main__":
    # Test Case / Verification Setup
    INPUT_TORQUE = 150.0  # Nm
    M = 2.0              # Module
    N1 = 24              # Pinion teeth
    N2 = 48              # Gear teeth
    B = 25.0             # Face width (mm)
    
    sigma_b, sigma_c = analyze_gear_stresses(INPUT_TORQUE, M, N1, N2, B)
    
    print("AGMA Stress Analysis Results")
    print(f"Tangential Load: {INPUT_TORQUE / ((M * N1) / 2.0 / 1000.0):.2f} N")
    print(f"Root Bending Stress: {sigma_b:.2f} MPa")
    print(f"Surface Contact Stress: {sigma_c:.2f} MPa")
