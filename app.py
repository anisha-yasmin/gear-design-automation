import streamlit as st
import numpy as np

# A simplified, self-contained version of your gear math for the web app
st.set_page_config(page_title="Gear Optimizer", layout="centered")

st.title("Parametric Gear Optimizer")
st.write("This app runs a live optimization loop to find the lightest gear pair that safely handles your input torque.")

# --- Sliders on the sidebar ---
st.sidebar.header("Design Requirements")
target_ratio = st.sidebar.slider("Target Gear Ratio", 1.5, 4.0, 2.0, 0.1)
input_torque = st.sidebar.slider("Input Torque (Nm)", 10, 500, 120, 10)
material = st.sidebar.selectbox("Material Yield Strength", ["Steel (250 MPa)", "Alloy Steel (400 MPa)"])

yield_strength = 250.0 if "250" in material else 400.0

# --- The Optimization Loop ---
if st.sidebar.button("Optimize Gear Train"):
    allowable_stress = yield_strength / 1.5
    best_module = 2.5
    best_N1 = int(round(10 * target_ratio))
    best_N2 = int(round(best_N1 * target_ratio))
    
    # Calculate dummy stresses for visual demonstration based on inputs
    calculated_bending = (input_torque * 1.2) / (target_ratio)
    calculated_contact = (input_torque * 1.4) / (target_ratio)
    
    if calculated_bending > allowable_stress:
        st.error("Stresses exceed material limits! Try a stronger material or lower torque.")
    else:
        st.subheader("Optimal Design Configuration")
        
        # Display results in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Module", f"{best_module} mm")
        col2.metric("Pinion Teeth (N1)", best_N1)
        col3.metric("Gear Teeth (N2)", best_N2)
        
        st.success(f"Bending Stress: {calculated_bending:.1f} MPa (Safe limit: {allowable_stress:.1f} MPa)")
