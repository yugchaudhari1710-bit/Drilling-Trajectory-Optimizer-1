import math
import random
import pandas as pd
import matplotlib.pyplot as plt

# ---------------- USER INPUT ----------------
# Change values here easily
surface = (0, 0, 0)              # (North, East, TVD)
target = (1200, 800, 2500)

# ---------------- TRAJECTORY FUNCTION ----------------
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

        # Build control
        build_rate = 1.5
        if inclination < target_inc:
            inclination += min(build_rate, target_inc - inclination)

        # Subsurface uncertainty
        inclination += random.uniform(-2, 2)

        inclination = max(0, min(85, inclination))

        inc_rad = math.radians(inclination)
        az_rad = math.radians(azimuth)

        dZ_step = step * math.cos(inc_rad)
        dH_step = step * math.sin(inc_rad)

        dN_step = dH_step * math.cos(az_rad)
        dE_step = dH_step * math.sin(az_rad)

        N += dN_step
        E += dE_step
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


# ---------------- GENERATE ----------------
df_actual = generate_well_trajectory(surface, target)

# ---------------- SECTION IDENTIFICATION ----------------
sections = []

for i in range(1, len(df_actual)):
    inc_prev = df_actual.loc[i-1, "Inclination"]
    inc_curr = df_actual.loc[i, "Inclination"]

    diff = inc_curr - inc_prev

    if inc_curr < 2:
        section = "Vertical"
    elif diff > 0.2:
        section = "Build"
    elif diff < -0.2:
        section = "Drop"
    else:
        section = "Hold"

    sections.append(section)

sections.insert(0, "Vertical")
df_actual["Section"] = sections

# ---------------- IDEAL PATH ----------------
def planned_path(surface, target, steps=50):
    Ns, Es, Zs = surface
    Nt, Et, Zt = target

    N_vals, E_vals, Z_vals = [], [], []

    for i in range(steps):
        frac = i / (steps - 1)
        N_vals.append(Ns + frac * (Nt - Ns))
        E_vals.append(Es + frac * (Et - Es))
        Z_vals.append(Zs + frac * (Zt - Zs))

    return N_vals, E_vals, Z_vals


N_plan, E_plan, Z_plan = planned_path(surface, target)

# ---------------- COLOR MAP ----------------
color_map = {
    "Vertical": "blue",
    "Build": "orange",
    "Hold": "green",
    "Drop": "red"
}

# ---------------- 3D PLOT WITH COLORS ----------------
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

# Plot each section separately
for sec in df_actual["Section"].unique():
    subset = df_actual[df_actual["Section"] == sec]
    ax.plot(subset["Northing"], subset["Easting"], subset["TVD"],
            label=sec, color=color_map[sec])

# Planned path
ax.plot(N_plan, E_plan, Z_plan, linestyle='dashed', label="Planned", color="black")

ax.set_xlabel("Northing")
ax.set_ylabel("Easting")
ax.set_zlabel("TVD")
ax.set_title("Well Trajectory (Color-coded Sections)")

ax.legend()
ax.invert_zaxis()

plt.show()

# ---------------- EXPORT ----------------
df_actual.to_excel("well_trajectory.xlsx", index=False)

print("\n✅ Survey table saved as: well_trajectory.xlsx")
print(df_actual.head())
