import streamlit as st
import numpy as np
import plotly.graph_objects as go

from geometry import calculate_gear_parameters, generate_involute_points
from stress_analysis import analyze_gear_stresses
from kinematics import optimize_gear_pair

st.set_page_config(page_title="Gear Synthesis Suite", layout="centered")

st.title("Parametric Gear Design & Optimization Suite")
st.markdown("Automated AGMA structural optimization and multi-dimensional profile generation.")
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
        col3.metric("Face Width (b)", f"{result['Face Width (mm)']} mm")
        
        st.markdown("### Structural Margins")
        st.info(f"Root Bending Stress: **{result['Bending Stress (MPa)']:.1f} MPa**")
        st.info(f"Hertzian Contact Stress: **{result['Contact Stress (MPa)']:.1f} MPa**")
        
        # --- DATA PREPARATION ---
        m = result['Module']
        N = int(result['Pinion Teeth (N1)'])
        b = result['Face Width (mm)']
        rb, rp, ra, rd = calculate_gear_parameters(m, N, 20.0)
        
        st.markdown(f"""
        | Reference Boundary | Radius | Diameter |
        | :--- | :--- | :--- |
        | **Outer Tip (Addendum)** | {ra:.2f} mm | {2*ra:.2f} mm |
        | **Pitch Circle** | {rp:.2f} mm | {2*rp:.2f} mm |
        | **Base Circle** | {rb:.2f} mm | {2*rb:.2f} mm |
        | **Root Land (Dedendum)** | {rd:.2f} mm | {2*rd:.2f} mm |
        """)
        
        x_face, y_face = generate_involute_points(rb, ra)
        
        # --- GRAPH 1: 2D HIGH-PRECISION PROFILES ---
        st.markdown("### 2D Involute Geometry Inspection")
        
        fig_2d = go.Figure()
        
        # Reference circles (including the requested Dedendum)
        angles = np.linspace(0, 2 * np.pi, 250)
        fig_2d.add_trace(go.Scatter(x=rp * np.cos(angles), y=rp * np.sin(angles), mode='lines', name='Pitch Circle', line=dict(color='orange', dash='dash'), hovertemplate="Pitch Radius: %{x:.2f} mm<extra></extra>"))
        fig_2d.add_trace(go.Scatter(x=rb * np.cos(angles), y=rb * np.sin(angles), mode='lines', name='Base Circle', line=dict(color='gray', dash='dot'), hovertemplate="Base Radius: %{x:.2f} mm<extra></extra>"))
        fig_2d.add_trace(go.Scatter(x=rd * np.cos(angles), y=rd * np.sin(angles), mode='lines', name='Dedendum (Root)', line=dict(color='purple', dash='solid', width=1.5), hovertemplate="Root Radius: %{x:.2f} mm<extra></extra>"))
        fig_2d.add_trace(go.Scatter(x=ra * np.cos(angles), y=ra * np.sin(angles), mode='lines', name='Addendum (Tip)', line=dict(color='red', width=1), hovertemplate="Outer Radius: %{x:.2f} mm<extra></extra>"))
        
        # Plot the thin teeth profiles exactly as before
        for i in range(N):
            beta = (2 * np.pi * i) / N
            x_rot = x_face * np.cos(beta) - y_face * np.sin(beta)
            y_rot = x_face * np.sin(beta) + y_face * np.cos(beta)
            fig_2d.add_trace(go.Scatter(x=x_rot, y=y_rot, mode='lines', line=dict(color='#1E88E5', width=1.5), showlegend=False, hoverinfo='skip'))
        
        fig_2d.update_layout(
            xaxis=dict(title="X Coordinate (mm)", scaleanchor="y", scaleratio=1, gridcolor='rgba(0,0,0,0.05)'),
            yaxis=dict(title="Y Coordinate (mm)", gridcolor='rgba(0,0,0,0.05)'),
            template="plotly_white",
            height=600,
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
        )
        st.plotly_chart(fig_2d, use_container_width=True)
        
        # --- GRAPH 2: INTERACTIVE 3D EXTRUSION ---
        st.markdown("### 3D Parametric CAD Generation")
        st.write("Drag to rotate, scroll to zoom. This model displays the exact structure of the gear")
        
        m = result['Module']
        N = int(result['Pinion Teeth (N1)'])
        b = result['Face Width (mm)']
        rb, rp, ra, rd = calculate_gear_parameters(m, N, 20.0)
        x_face, y_face = generate_involute_points(rb, ra)
        
        # Build the full 2D tooth boundary array directly from the work you already did
        x_pts_2d = []
        y_pts_2d = []
        for i in range(N):
            beta = (2 * np.pi * i) / N
            x_rot = x_face * np.cos(beta) - y_face * np.sin(beta)
            y_rot = x_face * np.sin(beta) + y_face * np.cos(beta)
            x_pts_2d.extend(x_rot)
            y_pts_2d.extend(y_rot)
            
        # Extrude along the Z-axis by building a 2D grid matrix
        z_range = np.linspace(0, b, 10)
        
        # Create the 3D surface mesh matrices
        X_matrix = np.outer(np.array(x_pts_2d), np.ones_like(z_range))
        Y_matrix = np.outer(np.array(y_pts_2d), np.ones_like(z_range))
        Z_matrix = np.outer(np.ones_like(x_pts_2d), z_range)
        
        fig_3d = go.Figure()
        
        # 1. Outer Teeth Profile Skin
        fig_3d.add_trace(go.Surface(
            x=X_matrix, y=Y_matrix, z=Z_matrix,
            colorscale=[[0, '#1E88E5'], [1, '#1E88E5']],
            showscale=False, opacity=0.95, name="Outer Teeth Profile"
        ))
        
        # 2. Internal Shaft Hub Cylinder
        r_hub = rd * 0.65
        hub_angles = np.linspace(0, 2 * np.pi, 150)
        
        X_hub = np.outer(r_hub * np.cos(hub_angles), np.ones_like(z_range))
        Y_hub = np.outer(r_hub * np.sin(hub_angles), np.ones_like(z_range))
        Z_hub = np.outer(np.ones_like(hub_angles), z_range)
        
        fig_3d.add_trace(go.Surface(
            x=X_hub, y=Y_hub, z=Z_hub,
            colorscale=[[0, '#1E88E5'], [1, '#1E88E5']],
            showscale=False, opacity=0.95, name="Shaft Hub Bore"
        ))
        
        # 3. Clean Face Caps using a Radial Grid Matrix (Prevents internal triangle crossing)
        r_space = np.linspace(r_hub, rd, 2)
        X_cap = np.outer(np.cos(hub_angles), r_space)
        Y_cap = np.outer(np.sin(hub_angles), r_space)
        
        # Front solid cap plate (z = 0)
        fig_3d.add_trace(go.Surface(
            x=X_cap, y=Y_cap, z=np.zeros_like(X_cap),
            colorscale=[[0, '#1E88E5'], [1, '#1E88E5']],
            showscale=False, opacity=0.95, name="Front Face Plate"
        ))
        
        # Rear solid cap plate (z = b)
        fig_3d.add_trace(go.Surface(
            x=X_cap, y=Y_cap, z=np.full_like(X_cap, b),
            colorscale=[[0, '#1E88E5'], [1, '#1E88E5']],
            showscale=False, opacity=0.95, name="Rear Face Plate"
        ))
        
        # 4. Sharp Boundary Outline Silhouettes
        x_outer = np.array(x_pts_2d)
        y_outer = np.array(y_pts_2d)
        fig_3d.add_trace(go.Scatter3d(x=x_outer, y=y_outer, z=np.zeros_like(x_outer), mode='lines', line=dict(color='black', width=1.5), showlegend=False))
        fig_3d.add_trace(go.Scatter3d(x=x_outer, y=y_outer, z=np.full_like(x_outer, b), mode='lines', line=dict(color='black', width=1.5), showlegend=False))
        fig_3d.add_trace(go.Scatter3d(x=r_hub * np.cos(hub_angles), y=r_hub * np.sin(hub_angles), z=np.zeros_like(hub_angles), mode='lines', line=dict(color='black', width=1.5), showlegend=False))
        fig_3d.add_trace(go.Scatter3d(x=r_hub * np.cos(hub_angles), y=r_hub * np.sin(hub_angles), z=np.full_like(hub_angles, b), mode='lines', line=dict(color='black', width=1.5), showlegend=False))
        
        fig_3d.update_layout(
            template="plotly_white",
            height=700,
            scene=dict(
                xaxis_title="X (mm)", yaxis_title="Y (mm)", zaxis_title="Z (Width mm)",
                aspectmode='data',
                camera=dict(eye=dict(x=1.3, y=1.3, z=1.3))
            )
        )
        st.plotly_chart(fig_3d, use_container_width=True)
        
    else:
        st.error("Static Failure Mode Alert: Design constraints exceed allowable margins for selected material bounds.")
else:
    st.info("Awaiting input initialization. Adjust constraints above and execute the loop.")
