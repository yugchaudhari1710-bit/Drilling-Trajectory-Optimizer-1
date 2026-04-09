import math
import random
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.title("Drilling Trajectory Visualization")

# -------- USER INPUT --------
st.sidebar.header("Input Coordinates")

Ns = st.sidebar.number_input("Surface Northing", value=0.0)
Es = st.sidebar.number_input("Surface Easting", value=0.0)
Zs = st.sidebar.number_input("Surface TVD", value=0.0)

Nt = st.sidebar.number_input("Target Northing", value=1200.0)
Et = st.sidebar.number_input("Target Easting", value=800.0)
Zt = st.sidebar.number_input("Target TVD", value=2500.0)

surface = (Ns, Es, Zs)
target = (Nt, Et, Zt)

# -------- TRAJECTORY FUNCTION --------
def generate_well_trajectory(surface, target, step=50):
    Ns, Es, Zs = surface
    Nt, Et, Zt = target

    N, E, Z = Ns, Es, Zs
    inclination = 0
    MD = 0
    data = []

    while Z < Zt:
        dN = Nt - N
        dE = Et - E
        dZ = Zt - Z

        target_inc = math.degrees(math.atan2(
            math.sqrt(dN**2 + dE**2), dZ
        ))
        azimuth = math.degrees(math.atan2(dE, dN))

        build_rate = 1.5
        if inclination < target_inc:
            inclination += min(build_rate, target_inc - inclination)

        inclination += random.uniform(-2, 2)
        inclination = max(0, min(85, inclination))

        inc_rad = math.radians(inclination)
        az_rad = math.radians(azimuth)

        dZ_step = step * math.cos(inc_rad)
        dH_step = step * math.sin(inc_rad)

        N += dH_step * math.cos(az_rad)
        E += dH_step * math.sin(az_rad)
        Z += dZ_step
        MD += step

        data.append({
            "MD": MD,
            "Inclination": inclination,
            "Azimuth": azimuth,
            "Northing": N,
            "Easting": E,
            "TVD": Z
        })

        if Z >= Zt:
            break

    return pd.DataFrame(data)


# -------- RUN BUTTON --------
if st.button("Generate Trajectory"):

    df = generate_well_trajectory(surface, target)

    # Section classification
    sections = []
    for i in range(1, len(df)):
        diff = df.loc[i, "Inclination"] - df.loc[i-1, "Inclination"]

        if df.loc[i, "Inclination"] < 2:
            section = "Vertical"
        elif diff > 0.2:
            section = "Build"
        elif diff < -0.2:
            section = "Drop"
        else:
            section = "Hold"

        sections.append(section)

    sections.insert(0, "Vertical")
    df["Section"] = sections

    # Plot
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

    st.success("Trajectory Generated Successfully ✅")

    st.dataframe(df)
