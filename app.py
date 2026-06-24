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
        st.markdown("###3D Parametric CAD Generation")
        st.write("Drag to rotate, scroll to zoom. This model displays the exact structure of the gear")
        
        m = result['Module']
        N = int(result['Pinion Teeth (N1)'])
        b = result['Face Width (mm)']
        rb, rp, ra, rd = calculate_gear_parameters(m, N, 20.0)
        x_face, y_face = generate_involute_points(rb, ra)
        
        # Build unified continuous tooth profile for a single tooth
        # Mirroring to get the second side
        pitch_angle = (np.pi * m) / (2 * rp)
        t_pitch = np.sqrt(max((rp / rb)**2 - 1, 0))
        inv_pitch_angle = np.arctan(t_pitch) - t_pitch
        theta_offset = pitch_angle - 2 * inv_pitch_angle
        
        x_side2 = x_face * np.cos(theta_offset) + y_face * np.sin(theta_offset)
        y_side2 = -x_face * np.sin(theta_offset) + y_face * np.cos(theta_offset)
        x_side2, y_side2 = x_side2[::-1], y_side2[::-1]
        
        # Convert arrays to flat standard lists, combine them, then cast back to numpy
        x_tooth_list = [x_face] + list(x_face) + list(x_side2) + [x_side2[-1]]
        y_tooth_list = [rd] + list(y_face) + list(y_side2) + [rd]
        
        x_tooth_base = np.array(x_tooth_list)
        y_tooth_base = np.array(y_tooth_list)
        
        # Generate full 2D profile coordinates around the circle
        x_profile_2d = []
        y_profile_2d = []
        for i in range(N):
            beta = (2 * np.pi * i) / N
            x_rot = x_tooth_base * np.cos(beta) - y_tooth_base * np.sin(beta)
            y_rot = x_tooth_base * np.sin(beta) + y_tooth_base * np.cos(beta)
            x_profile_2d.extend(x_rot)
            y_profile_2d.extend(y_rot)
            
        x_profile_2d = np.array(x_profile_2d)
        y_profile_2d = np.array(y_profile_2d)
        num_pts = len(x_profile_2d)
        
        # Create 3D vertices: Front face (z=0) and Back face (z=b)
        x_vertices = np.concatenate([x_profile_2d, x_profile_2d])
        y_vertices = np.concatenate([y_profile_2d, y_profile_2d])
        z_vertices = np.concatenate([np.zeros(num_pts), np.full(num_pts, b)])
        
        # Build the triangular mesh faces connecting front and back vertices
        i_indices = []
        j_indices = []
        k_indices = []
        
        for idx in range(num_pts):
            next_idx = (idx + 1) % num_pts
            
            # Triangle 1 connecting front point to back point
            i_indices.append(idx)
            j_indices.append(next_idx)
            k_indices.append(idx + num_pts)
            
            # Triangle 2 completing the quad panel face
            i_indices.append(next_idx)
            j_indices.append(next_idx + num_pts)
            k_indices.append(idx + num_pts)
            
        fig_3d = go.Figure()
        
        # Add the solid surface mesh
        fig_3d.add_trace(go.Mesh3d(
            x=x_vertices, y=y_vertices, z=z_vertices,
            i=i_indices, j=j_indices, k=k_indices,
            color='#1E88E5',
            opacity=0.9,
            name='Solid Gear Body',
            flatshading=True
        ))
        
        # Add crisp edge outlines on front and back faces to look like clear CAD boundaries
        angles = np.linspace(0, 2 * np.pi, 250)
        fig_3d.add_trace(go.Scatter3d(x=x_profile_2d, y=y_profile_2d, z=np.zeros(num_pts), mode='lines', line=dict(color='black', width=2), name='Front Edge Profile'))
        fig_3d.add_trace(go.Scatter3d(x=x_profile_2d, y=y_profile_2d, z=np.full(num_pts, b), mode='lines', line=dict(color='black', width=2), name='Rear Edge Profile'))
        
        fig_3d.update_layout(
            template="plotly_white",
            height=700,
            scene=dict(
                xaxis_title="X (mm)",
                yaxis_title="Y (mm)",
                zaxis_title="Z (Width mm)",
                aspectmode='data',
                camera=dict(eye=dict(x=1.25, y=1.25, z=1.25))
            )
        )
        st.plotly_chart(fig_3d, use_container_width=True)
        
    else:
        st.error("Static Failure Mode Alert: Design constraints exceed allowable margins for selected material bounds.")
else:
    st.info("Awaiting input initialization. Adjust constraints above and execute the loop.")
