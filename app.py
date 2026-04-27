import math
import random
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np

st.set_page_config(layout="wide")

st.title("Drilling Trajectory Visualization")

# -------- INPUT --------
st.sidebar.header("Input Coordinates")

Ns = st.sidebar.number_input("Surface Northing", value=0.0)
Es = st.sidebar.number_input("Surface Easting", value=0.0)
Zs = st.sidebar.number_input("Surface TVD", value=0.0)
Kop = st.sidebar.number_input("Kickoff point", value=1000.0)
Nt = st.sidebar.number_input("Northing (Degree)", value=1200.0)
Et = st.sidebar.number_input("Easting (Degree)", value=800.0)
Zt = st.sidebar.number_input("TVD", value=4820.0)
build_rate = st.sidebar.number_input("Build Rate (°/100 ft)", value=1.5)

surface = (Ns, Es, Zs)
target = (Nt, Et, Zt)

# -------- TRAJECTORY FUNCTION --------
def generate_well_trajectory(surface, kop, target, build_rate_deg_per_100ft, step=50):
    Ns, Es, Zs = surface
    Nt, Et, Zt = target
    
    # Calculate azimuth to target
    azimuth_deg = math.degrees(math.atan2(Et - Es, Nt - Ns))
    azimuth_rad = math.radians(azimuth_deg)
    
    # Calculate total horizontal displacement
    dH_total = math.sqrt((Nt - Ns)**2 + (Et - Es)**2)
    
    # Vertical section MD
    MD_vertical = kop - Zs
    
    # Build rate in radians per foot
    BR_rad_per_ft = (build_rate_deg_per_100ft * math.pi / 180) / 100
    
    # Radius of curvature
    R = 1 / BR_rad_per_ft if BR_rad_per_ft > 0 else float('inf')
    
    # Build section parameters
    dTVD_build = R * (1 - math.cos(math.pi / 2))  # R for 90° build
    dH_build = R * math.sin(math.pi / 2)  # R
    
    # Ensure Zt matches L-type (adjust if necessary, but assume input is correct)
    expected_Zt = Zs + kop + dTVD_build
    Zt = expected_Zt  # Override input Zt to match L-type trajectory
    target = (Nt, Et, Zt)  # Update target with corrected Zt
    
    # Build section MD
    delta_MD_build = (math.pi / 2) / BR_rad_per_ft
    
    # Horizontal section
    dH_horizontal = dH_total - dH_build
    MD_horizontal = dH_horizontal
    
    # Total MD
    total_MD = MD_vertical + delta_MD_build + MD_horizontal
    
    # Initialize
    MD = 0
    N, E, Z = Ns, Es, Zs
    inclination_rad = 0
    data = []
    
    while MD < total_MD:
        # Determine section
        if MD < MD_vertical:
            section = "Vertical"
            next_inclination_rad = 0
            next_azimuth_rad = azimuth_rad
        elif MD < MD_vertical + delta_MD_build:
            section = "Build"
            s = MD - MD_vertical
            next_inclination_rad = BR_rad_per_ft * s
            next_azimuth_rad = azimuth_rad
        else:
            section = "Horizontal"
            next_inclination_rad = math.pi / 2
            next_azimuth_rad = azimuth_rad
        
        # Calculate next MD
        next_MD = min(MD + step, total_MD)
        delta_MD = next_MD - MD
        
        # Use minimum curvature for position update
        theta1 = inclination_rad
        theta2 = next_inclination_rad
        phi1 = azimuth_rad
        phi2 = next_azimuth_rad
        
        delta_theta = theta2 - theta1
        delta_phi = phi2 - phi1
        
        cos_delta_theta = math.cos(delta_theta)
        sin_theta1 = math.sin(theta1)
        sin_theta2 = math.sin(theta2)
        cos_delta_phi = math.cos(delta_phi)
        
        beta = math.acos(cos_delta_theta - sin_theta1 * sin_theta2 * (1 - cos_delta_phi))
        
        if beta == 0:
            RF = 1
        else:
            RF = (2 / delta_MD) * math.tan(beta / 2)
        
        delta_TVD = (delta_MD / 2) * (math.cos(theta1) + math.cos(theta2)) * RF
        delta_N = (delta_MD / 2) * (sin_theta1 * math.cos(phi1) + sin_theta2 * math.cos(phi2)) * RF
        delta_E = (delta_MD / 2) * (sin_theta1 * math.sin(phi1) + sin_theta2 * math.sin(phi2)) * RF
        
        # Update positions
        Z += delta_TVD
        N += delta_N
        E += delta_E
        MD = next_MD
        inclination_rad = next_inclination_rad
        
        # Append to data
        data.append({
            "MD": MD,
            "Inclination": math.degrees(inclination_rad),
            "Azimuth": azimuth_deg,
            "Northing": N,
            "Easting": E,
            "TVD": Z,
            "Section": section
        })
    
    return pd.DataFrame(data)


# -------- ALWAYS RUN (NO BUTTON) --------
df = generate_well_trajectory(surface, Kop, target, build_rate)

# -------- PLOT --------
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

color_map = {
    "Vertical": "blue",
    "Build": "orange",
    "Hold": "green",
    "Drop": "red"
}

for sec in df["Section"].unique():
    subset = df[df["Section"] == sec]
    ax.plot(subset["Northing"], subset["Easting"], subset["TVD"],
            label=sec, color=color_map[sec])

ax.set_xlabel("Northing")
ax.set_ylabel("Easting")
ax.set_zlabel("TVD")
ax.set_title("Well Trajectory")
ax.legend()
ax.invert_zaxis()

st.pyplot(fig)

# -------- TABLE --------
st.subheader("Survey Table")
st.dataframe(df)

st.success("App Running Successfully ✅")
