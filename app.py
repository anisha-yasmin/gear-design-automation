import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import numpy as np
import plotly.graph_objects as go
from src.geometry import calculate_gear_parameters, generate_involute_points
from src.stress_analysis import analyze_gear_stresses
from src.kinematics import optimize_gear_pair
st.set_page_config(page_title="Parametric Gear Optimizer", layout="centered")

st.title("Parametric Gear Design & Structural Optimizer")
st.write("This app runs a live optimization loop using your backend scripts to find the lightest gear configuration.")

# Sidebar Inputs
st.sidebar.header("Design Requirements")
target_ratio = st.sidebar.slider("Target Gear Ratio", 1.5, 4.0, 2.0, 0.1)
input_torque = st.sidebar.slider("Input Torque (Nm)", 10, 500, 120, 10)
material_yield = st.sidebar.selectbox("Material Yield Strength", 
                                      options=[250.0, 400.0], 
                                      format_func=lambda x: f"Steel ({int(x)} MPa)")

#Triggering the Optimization Loop
if st.sidebar.button("Optimize Gear Train"):
    # Call the optimization function from kinematics.py
    result = optimize_gear_pair(target_ratio, input_torque, material_yield)
    
    if result:
        st.subheader("Optimal Design Configuration")
        
        # Display the real calculated metrics in clean columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Module", f"{result['Module']} mm")
        col2.metric("Pinion Teeth (N1)", int(result['Pinion Teeth (N1)']))
        col4.metric("Face Width", f"{result['Face Width (mm)']} mm")
        
        st.success(f"Bending Stress: {result['Bending Stress (MPa)']:.1f} MPa")
        st.success(f"Contact Stress: {result['Contact Stress (MPa)']:.1f} MPa")
        
        # Plot the exact geometry from geometry.py
        st.subheader("Mathematically Generated Tooth Profile")
        
        rb, rp, ra, rd = calculate_gear_parameters(result['Module'], result['Pinion Teeth (N1)'], 20.0)
        x_pts, y_pts = generate_involute_points(rb, ra)
        
        # Draw an interactive graph
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x_pts, y=y_pts, mode='lines+markers', line=dict(color='#FF4B4B', width=3)))
        fig.update_layout(xaxis_title="X (mm)", yaxis_title="Y (mm)", template="plotly_white", showlegend=False)
        st.plotly_chart(fig)
        
    else:
        st.error("No safe design configuration fits within these boundaries. Try increasing material specifications.")
