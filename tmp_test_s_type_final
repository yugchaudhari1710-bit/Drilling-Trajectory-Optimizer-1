def generate_well_trajectory(surface, Vb, target, phi, step=50,
                             trajectory_type="S-Type (Type III)",
                             drop_rate=None, max_inclination=None):

    import math
    import pandas as pd

    Na, Ea, Zs = surface
    Nt, Et, Vt = target

    # Basic geometry
    H_t = math.sqrt((Nt - Na)**2 + (Et - Ea)**2)
    beta_rad = math.atan2(Et - Ea, Nt - Na)
    beta_deg = math.degrees(beta_rad)

    R_build = 18000.0 / (math.pi * phi)
    R_drop  = 18000.0 / (math.pi * drop_rate)

    alpha_max_rad = math.radians(max_inclination)

    # ─────────────────────────────────────────────
    # STEP 1: Build section
    # ─────────────────────────────────────────────
    MD_kop = Vb
    MD_build = MD_kop + (100.0 * max_inclination / phi)

    V_build = R_build * math.sin(alpha_max_rad)
    H_build = R_build * (1 - math.cos(alpha_max_rad))

    # ─────────────────────────────────────────────
    # STEP 2: Solve final inclination (same as before)
    # ─────────────────────────────────────────────
    dV_total = Vt - Zs

    def residual(alpha_final):
        H_drop = R_drop * (math.cos(alpha_final) - math.cos(alpha_max_rad))
        V_drop = R_drop * (math.sin(alpha_max_rad) - math.sin(alpha_final))

        H_rem = H_t - H_build - H_drop
        V_rem = dV_total - V_build - V_drop

        return H_rem - V_rem * math.tan(alpha_final)

    low = 1e-6
    high = alpha_max_rad - 1e-6

    for _ in range(80):
        mid = 0.5 * (low + high)
        if residual(low) * residual(mid) <= 0:
            high = mid
        else:
            low = mid

    alpha_final = mid

    # ─────────────────────────────────────────────
    # STEP 3: Compute drop section
    # ─────────────────────────────────────────────
    MD_drop = (100.0 * math.degrees(alpha_max_rad - alpha_final) / drop_rate)

    # ─────────────────────────────────────────────
    # STEP 4: Solve tangent length (NEW)
    # ─────────────────────────────────────────────
    H_drop = R_drop * (math.cos(alpha_final) - math.cos(alpha_max_rad))
    V_drop = R_drop * (math.sin(alpha_max_rad) - math.sin(alpha_final))

    H_remaining = H_t - H_build - H_drop
    V_remaining = dV_total - V_build - V_drop

    # tangent + final hold combined
    MD_remaining = V_remaining / math.cos(alpha_final)

    # split into tangent + final hold
    MD_tangent = MD_remaining * 0.4   # adjustable (can optimize later)
    MD_hold_final = MD_remaining * 0.6

    # Section boundaries
    MD_tangent_end = MD_build + MD_tangent
    MD_drop_end = MD_tangent_end + MD_drop
    MD_target = MD_drop_end + MD_hold_final

    # ─────────────────────────────────────────────
    # STEP 5: Walk trajectory
    # ─────────────────────────────────────────────
    BR = math.radians(phi) / 100.0
    DR = math.radians(drop_rate) / 100.0

    MD = 0.0
    N, E, Z = Na, Ea, Zs
    inc = 0.0

    data = []

    while MD < MD_target:

        if MD < MD_kop:
            section = "Vertical"
            inc_next = 0.0

        elif MD < MD_build:
            section = "Build"
            inc_next = min(inc + BR * step, alpha_max_rad)

        elif MD < MD_tangent_end:
            section = "Hold_max"
            inc_next = alpha_max_rad

        elif MD < MD_drop_end:
            section = "Drop"
            inc_next = max(inc - DR * step, alpha_final)

        else:
            section = "Hold_final"
            inc_next = alpha_final

        next_MD = min(MD + step, MD_target)
        dMD = next_MD - MD

        theta1, theta2 = inc, inc_next

        dTVD = (dMD / 2) * (math.cos(theta1) + math.cos(theta2))
        dN   = (dMD / 2) * (math.sin(theta1) + math.sin(theta2)) * math.cos(beta_rad)
        dE   = (dMD / 2) * (math.sin(theta1) + math.sin(theta2)) * math.sin(beta_rad)

        Z += dTVD
        N += dN
        E += dE

        MD = next_MD
        inc = inc_next

        data.append({
            "MD (ft)": round(MD, 2),
            "Inclination (°)": round(math.degrees(inc), 4),
            "Azimuth (°)": round(beta_deg, 4),
            "Northing (ft)": round(N, 4),
            "Easting (ft)": round(E, 4),
            "TVD (ft)": round(Z, 4),
            "Section": section
        })

    df = pd.DataFrame(data)

    summary = {
        "H_t": round(H_t, 2),
        "β": round(beta_deg, 2),
        "α_max": round(math.degrees(alpha_max_rad), 2),
        "α_final": round(math.degrees(alpha_final), 2),
        "MD_target": round(MD_target, 2)
    }

    return df, summary
