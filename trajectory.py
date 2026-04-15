import math
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(layout="wide")

st.title("Drilling Trajectory Visualization — L-Type (Type I Profile)")

# -------- INPUT --------
st.sidebar.header("Input Coordinates")

Ns = st.sidebar.number_input("Surface Northing (Na)", value=0.0)
Es = st.sidebar.number_input("Surface Easting (Ea)", value=0.0)
Zs = st.sidebar.number_input("Surface TVD", value=0.0)

Vb = st.sidebar.number_input("TVD to KOP (Vb)", value=1000.0)
Nt = st.sidebar.number_input("Target Northing (Nt)", value=1200.0)
Et = st.sidebar.number_input("Target Easting (Et)", value=800.0)
Vt = st.sidebar.number_input("Target TVD (Vt)", value=4820.0)
build_rate = st.sidebar.number_input("Build Rate φ (°/100 ft)", value=1.5, min_value=0.01)

step = st.sidebar.number_input("Survey Step (ft)", value=50, min_value=1)

surface = (Ns, Es, Zs)
target = (Nt, Et, Vt)

# -------- TRAJECTORY FUNCTION --------
def generate_well_trajectory(surface, Vb, target, phi, step=50):
    """
    L-Type (Type I) trajectory using formulas from Geometrical Planning for Type I Profile.

    Symbols match the textbook exactly:
      Na, Ea        = surface (slot) Northing / Easting
      Nt, Et        = target Northing / Easting
      Vb            = TVD to KOP (point B)
      Vt            = target TVD
      phi (φ)       = build rate in degrees per 100 ft
      R             = radius of curvature = 18000 / (π * φ)
      H_t           = horizontal displacement to target = sqrt((Nt-Na)^2 + (Et-Ea)^2)
      β             = target bearing = atan2(Et-Ea, Nt-Na)
      α             = maximum inclination angle at end of build section (point C)
      Vc            = TVD at point C = Vb + R*sin(α)
      Hc            = horizontal departure at C = R*(1 - cos(α))
      MD_b          = measured depth at KOP = Vb
      MD_c          = MD at point C = MD_b + 100*α/φ
      MD_t          = MD at target = MD_c + (Vt - Vc) / cos(α)
    """
    Na, Ea, Zs = surface
    Nt, Et, Vt = target

    # ── Step 1: Horizontal displacement H_t ──────────────────────────────────
    # Formula: H_t = sqrt((N_t - N_a)^2 + (E_t - E_a)^2)
    H_t = math.sqrt((Nt - Na)**2 + (Et - Ea)**2)

    # ── Step 2: Target bearing β ──────────────────────────────────────────────
    # Formula: β = tan⁻¹((E_t - E_a) / (N_t - N_a))
    beta_rad = math.atan2(Et - Ea, Nt - Na)
    beta_deg = math.degrees(beta_rad)

    # ── Step 3: Radius of curvature R ────────────────────────────────────────
    # Formula: R = 18000 / (π * φ)
    R = 18000.0 / (math.pi * phi)

    # ── Step 4: Maximum inclination angle α ──────────────────────────────────
    # From the textbook geometry (Fig. 4.8):
    #   tan x = (H_t - R) / (V_t - V_b)
    #   sin y = R*cos(x) / PT  where PT = sqrt((H_t-R)^2 + (V_t-V_b)^2)
    #   α = x + y
    # Formula: α = tan⁻¹((H_t - R)/(V_t - V_b)) + sin⁻¹(R*cos(x) / PT)
    dV = Vt - Vb          # vertical distance from KOP to target
    dH_minus_R = H_t - R  # horizontal distance minus radius

    PT = math.sqrt(dH_minus_R**2 + dV**2)  # = FT (hypotenuse in the triangle)

    x_rad = math.atan2(dH_minus_R, dV)     # tan x = (H_t - R) / (V_t - V_b)
    y_rad = math.asin((R * math.cos(x_rad)) / PT)  # sin y = R*cos(x) / PT

    alpha_rad = x_rad + y_rad               # maximum inclination
    alpha_deg = math.degrees(alpha_rad)

    # ── Step 5: Coordinates at end of build (point C) ────────────────────────
    # True vertical depth:    Vc = Vb + R*sin(α)
    # Horizontal departure:   Hc = R*(1 - cos(α))
    Vc = Vb + R * math.sin(alpha_rad)
    Hc = R * (1 - math.cos(alpha_rad))

    # ── Step 6: Measured depths ───────────────────────────────────────────────
    # MD at B (KOP):     MD_b = V_b  (pure vertical)
    # Arc BC:            BC   = 100 * α / φ
    # MD at C:           MD_c = MD_b + BC
    # MD at target T:    MD_t = MD_c + (V_t - V_c) / cos(α)
    MD_b = Vb
    BC   = 100.0 * alpha_deg / phi         # arc length of build section
    MD_c = MD_b + BC
    MD_t = MD_c + (Vt - Vc) / math.cos(alpha_rad)

    # ── Step 7: Walk the wellbore step-by-step ───────────────────────────────
    BR_rad_per_ft = math.radians(phi) / 100.0   # build rate in rad/ft

    MD   = 0.0
    N, E, Z = Na, Ea, Zs
    inc_rad = 0.0
    data = []

    while MD < MD_t - 1e-6:
        # Determine section and inclination at current MD
        if MD <= MD_b:
            section = "Vertical"
            inc_next = 0.0
        elif MD <= MD_c:
            section = "Build"
            s = MD - MD_b          # distance drilled into build section
            inc_next = BR_rad_per_ft * s
        else:
            section = "Hold"
            inc_next = alpha_rad

        # Clamp inclination
        inc_next = min(inc_next, alpha_rad)

        # Next station
        next_MD    = min(MD + step, MD_t)
        delta_MD   = next_MD - MD

        # ── Minimum curvature position update ────────────────────────────────
        theta1, theta2 = inc_rad, inc_next
        phi1 = phi2 = beta_rad  # azimuth fixed toward target

        delta_theta  = theta2 - theta1
        sin_t1, sin_t2 = math.sin(theta1), math.sin(theta2)
        cos_t1, cos_t2 = math.cos(theta1), math.cos(theta2)

        beta_angle = math.acos(
            max(-1.0, min(1.0,
                math.cos(delta_theta) - sin_t1 * sin_t2 * (1 - math.cos(0))
            ))
        )

        RF = (2.0 / delta_MD) * math.tan(beta_angle / 2) if beta_angle != 0 else 1.0

        delta_TVD = (delta_MD / 2) * (cos_t1 + cos_t2) * RF
        delta_N   = (delta_MD / 2) * (sin_t1 * math.cos(phi1) + sin_t2 * math.cos(phi2)) * RF
        delta_E   = (delta_MD / 2) * (sin_t1 * math.sin(phi1) + sin_t2 * math.sin(phi2)) * RF

        Z   += delta_TVD
        N   += delta_N
        E   += delta_E
        MD   = next_MD
        inc_rad = inc_next

        data.append({
            "MD (ft)"          : round(MD, 2),
            "Inclination (°)"  : round(math.degrees(inc_rad), 4),
            "Azimuth (°)"      : round(beta_deg, 4),
            "Northing (ft)"    : round(N, 4),
            "Easting (ft)"     : round(E, 4),
            "TVD (ft)"         : round(Z, 4),
            "Section"          : section,
        })

    df = pd.DataFrame(data)

    # ── Summary results ───────────────────────────────────────────────────────
    summary = {
        "H_t (Horizontal Displacement, ft)": round(H_t, 2),
        "β (Target Bearing, °)"            : round(beta_deg, 4),
        "R (Radius of Curvature, ft)"      : round(R, 2),
        "α (Max Inclination, °)"           : round(alpha_deg, 4),
        "V_c (TVD at Point C, ft)"         : round(Vc, 2),
        "H_c (Horizontal Departure at C, ft)": round(Hc, 2),
        "MD at KOP (ft)"                   : round(MD_b, 2),
        "Arc BC (ft)"                      : round(BC, 2),
        "MD at C (ft)"                     : round(MD_c, 2),
        "MD at Target (ft)"                : round(MD_t, 2),
    }

    return df, summary


# -------- RUN --------
try:
    df, summary = generate_well_trajectory(surface, Vb, target, build_rate, int(step))

    # -------- SUMMARY --------
    st.subheader("📐 Calculated Parameters")
    col1, col2 = st.columns(2)
    items = list(summary.items())
    for i, (k, v) in enumerate(items):
        (col1 if i < len(items)//2 else col2).metric(k, v)

    # -------- PLOT --------
    st.subheader("3D Well Trajectory")
    fig = plt.figure(figsize=(10, 7))
    ax  = fig.add_subplot(111, projection='3d')

    color_map = {"Vertical": "blue", "Build": "orange", "Hold": "green"}

    for sec in df["Section"].unique():
        subset = df[df["Section"] == sec]
        ax.plot(subset["Northing (ft)"], subset["Easting (ft)"], subset["TVD (ft)"],
                label=sec, color=color_map.get(sec, "gray"), linewidth=2)

    ax.set_xlabel("Northing (ft)")
    ax.set_ylabel("Easting (ft)")
    ax.set_zlabel("TVD (ft)")
    ax.set_title("L-Type Well Trajectory (Type I Profile)")
    ax.legend()
    ax.invert_zaxis()

    st.pyplot(fig)

    # -------- TABLE --------
    st.subheader("📋 Survey Table")
    st.dataframe(df, use_container_width=True)

    st.success("App Running Successfully ✅")

except Exception as e:
    st.error(f"Error: {e}")
    st.info("Tip: Check that H_t > R (target must be beyond the build arc radius). "
            "Try increasing the target horizontal distance or reducing the build rate.")