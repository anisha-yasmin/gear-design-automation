import numpy as np
from stress_analysis import analyze_gear_stresses

def optimize_gear_pair(required_ratio, input_torque_nm, material_yield_mpa=250.0):
    safety_factor = 1.5
    allowable_stress = material_yield_mpa / safety_factor
    
    best_design = None
    min_weight_factor = float('inf')
    
    possible_modules = [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
    possible_pinion_teeth = range(15, 35)
    possible_face_widths = range(15, 55, 5)
    
    for m in possible_modules:
        for N1 in possible_pinion_teeth:
            N2 = int(round(N1 * required_ratio))
            actual_ratio = N2 / N1
            
            if abs(actual_ratio - required_ratio) / required_ratio > 0.02:
                continue
                
            for b in possible_face_widths:
                sigma_b, sigma_c = analyze_gear_stresses(input_torque_nm, m, N1, N2, b)
                
                if sigma_b <= allowable_stress and sigma_c <= allowable_stress:
                    r1 = (m * N1) / 2.0
                    r2 = (m * N2) / 2.0
                    weight_factor = (r1**2 * b) + (r2**2 * b)
                    
                    if weight_factor < min_weight_factor:
                        min_weight_factor = weight_factor
                        best_design = {
                            "Module": m,
                            "Pinion Teeth (N1)": N1,
                            "Gear Teeth (N2)": N2,
                            "Face Width (mm)": b,
                            "Bending Stress (MPa)": sigma_b,
                            "Contact Stress (MPa)": sigma_c,
                            "Actual Ratio": actual_ratio
                        }
                        
    return best_design

if __name__ == "__main__":
    TARGET_RATIO = 2.0
    TORQUE = 120.0
    STEEL_YIELD = 250.0
    
    result = optimize_gear_pair(TARGET_RATIO, TORQUE, STEEL_YIELD)
    
    print("\nOptimal Structural Design Found")
    if result:
        for key, value in result.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
    else:
        print("No valid design found within constraints.")
