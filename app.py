import streamlit as st
import numpy as np
import plotly.graph_objects as go

from geometry import calculate_gear_parameters, generate_involute_points
from stress_analysis import analyze_gear_stresses
from kinematics import optimize_gear_pair

st.set_page_config(page_title="Gear Synthesis Suite", layout="centered")

st.title("Parametric Gear Design & Optimization Suite")
st.markdown("Automated AGMA structural optimization and high-fidelity profile generation.")
st.markdown("---")

st.subheader("Design Constraints")
target_ratio = st.slider("Target Gear Ratio", 1.5, 4.0, 2.0, 0.1)
input_torque = st.slider("Input Torque (Nm)", 10, 500, 120, 10)
material_yield = st.selectbox("Material Class", 
                              options=[250.0, 400.0], 
                              format_func=lambda x: f"Grade Steel ({int(x)} MPa)")

execute = st.button("Run Optimization Loop", use_container_width=True)

st.markdown("---")

if execute:
    result = optimize_gear_pair(target_ratio, input_torque, material_yield)
    
    if result:
        st.subheader("Optimized Parameters")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Module", f"{result['Module']} mm")
        col2.metric("Pinion Teeth (N1)", int(result['Pinion Teeth (N1)']))
        col3.metric("Face Width", f"{result['Face Width (mm)']} mm")
        
        st.markdown("### Structural Margins")
        st.info(f"Root Bending Stress: **{result['Bending Stress (MPa)']:.1f} MPa**")
        st.info(f"Hertzian Contact Stress: **{result['Contact Stress (MPa)']:.1f} MPa**")
        
        st.markdown("### High-Fidelity Geometry Synthesis")
        
        m = result['Module']
        N = int(result['Pinion Teeth (N1)'])
        rb, rp, ra, rd = calculate_gear_parameters(m, N, 20.0)
        
        st.markdown(f"""
        | Reference Boundary | Radius | Diameter |
        | :--- | :--- | :--- |
        | **Outer Tip (Addendum)** | {ra:.2f} mm | {2*ra:.2f} mm |
        | **Pitch Circle** | {rp:.2f} mm | {2*rp:.2f} mm |
        | **Base Circle** | {rb:.2f} mm | {2*rb:.2f} mm |
        | **Root Land (Dedendum)** | {rd:.2f} mm | {2*rd:.2f} mm |
        """)
        
        # 1. Generate primary side of a single tooth profile
        x_side1, y_side1 = generate_involute_points(rb, ra)
        
        # 2. Mirror profile mathematically to create a solid tooth thickness
        # Tooth thickness at pitch circle = (pi * m) / 2
        pitch_angle = (np.pi * m) / (2 * rp)
        
        # Find the angle of the involute point crossing the pitch circle to properly align mirrored face
        t_pitch = np.sqrt(max((rp / rb)**2 - 1, 0))
        inv_pitch_angle = np.arctan(t_pitch) - t_pitch
        
        # Apply thickness offset shift
        theta_offset = pitch_angle - 2 * inv_pitch_angle
        
        x_side2 = x_side1 * np.cos(theta_offset) + y_side1 * np.sin(theta_offset)
        y_side2 = -x_side1 * np.sin(theta_offset) + y_side1 * np.cos(theta_offset)
        
        # Reverse side 2 array direction so coordinates form a continuous outer loop contour path
        x_side2, y_side2 = x_side2[::-1], y_side2[::-1]
        
        # Combine faces to form one closed single tooth crown profile contour boundary
        x_tooth = np.insert(x_side1, 0, 0)
        x_tooth = np.append(x_tooth, x_side2)
        x_tooth = np.append(x_tooth, 0)

        y_tooth = np.insert(y_side1, 0, rd)
        y_tooth = np.append(y_tooth, y_side2)
        y_tooth = np.append(y_tooth, rd)
        
        fig = go.Figure()
        
        # Render clean reference circles background layers
        angles = np.linspace(0, 2 * np.pi, 250)
        fig.add_trace(go.Scatter(x=rp * np.cos(angles), y=rp * np.sin(angles), mode='lines', name='Pitch Circle', line=dict(color='orange', dash='dash'), hovertemplate="Pitch Radius: %{x:.2f} mm<extra></extra>"))
        fig.add_trace(go.Scatter(x=rb * np.cos(angles), y=rb * np.sin(angles), mode='lines', name='Base Circle', line=dict(color='gray', dash='dot'), hovertemplate="Base Radius: %{x:.2f} mm<extra></extra>"))
        fig.add_trace(go.Scatter(x=rd * np.cos(angles), y=rd * np.sin(angles), mode='lines', name='Dedendum (Root)', line=dict(color='purple', dash='solid', width=1), hovertemplate="Root Radius: %{x:.2f} mm<extra></extra>"))
        
        # Accumulate all coordinate sequences to generate a unified solid fill region geometry map
        x_full_gear = []
        y_full_gear = []
        
        for i in range(N):
            beta = (2 * np.pi * i) / N
            x_rot = x_tooth * np.cos(beta) - y_tooth * np.sin(beta)
            y_rot = x_tooth * np.sin(beta) + y_tooth * np.cos(beta)
            
            x_full_gear.extend(x_rot)
            y_full_gear.extend(y_rot)
            
        # Draw the complete structural solid gear polygon asset
        fig.add_trace(go.Scatter(
            x=x_full_gear, y=y_full_gear, 
            fill="toself", 
            fillcolor="rgba(30, 136, 229, 0.2)", 
            line=dict(color='#1E88E5', width=2), 
            name='Solid Gear Blank Profile',
            hoverinfo='skip'
        ))
        
        fig.update_layout(
            xaxis=dict(title="X Axis Coordinate (mm)", scaleanchor="y", scaleratio=1, gridcolor='rgba(0,0,0,0.05)'),
            yaxis=dict(title="Y Axis Coordinate (mm)", gridcolor='rgba(0,0,0,0.05)'),
            template="plotly_white",
            height=650,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.error("Static Failure Mode Alert: Design constraints exceed allowable margins for selected material bounds.")
else:
    st.info("Awaiting input initialization. Adjust constraints above and execute the loop.")
