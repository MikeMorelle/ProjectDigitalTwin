import streamlit as st

def build_css(status):
    css = "<style>"

    for comp, state in status.items():
        if state == "critical":
            css += f"""
            #{comp} {{
                fill: black !important;
                animation: blink 0.8s infinite;
                filter: drop-shadow(0 0 10px white);
            }}
            """
        elif state == "warning":
            css += f"""
            #{comp} {{
                fill: black !important;
                animation: blink 2s infinite;
                filter: drop-shadow(0 0 8px white);
            }}
            """

    css += """
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.4; }
        100% { opacity: 1; }
    }
    </style>
    """

    return css
svg = """
<svg
    viewBox="0 0 1000 350"
    width="100%"
    height="100%"
    preserveAspectRatio="xMidYMid meet">

<style>
    .part {
        fill: #27408B;
        transition: all 0.25s ease;
        cursor: pointer;
    }

    .part:hover {
        fill: #ff3b3b;
        filter: drop-shadow(0 0 12px red);
    }

    .fan {
        fill: #4876FF;
        transition: all 0.25s ease;
        cursor: pointer;
    }

    .fan:hover {
        fill: #ff3b3b;
        filter: drop-shadow(0 0 12px red);
    }

    .core {
        fill: #d6b44c;
        transition: all 0.25s ease;
        cursor: pointer;
    }

    .core:hover {
        fill: #ff3b3b;
        filter: drop-shadow(0 0 12px red);
    }

    .hot {
        fill: #ff3b3b;
        transition: all 0.25s ease;
        cursor: pointer;
    }

    .hot:hover {
        fill: #ff8888;
        filter: drop-shadow(0 0 14px red);
    }

    .casing {
        fill: none;
        stroke: #7f8c8d;
        stroke-width: 20;
    }

</style>

<!-- OUTER CASING TOP -->
<path class="casing"
      d="
      M35 95

      Q120 40 260 55
      Q420 20 600 45
      Q760 65 960 120
      " />

<!-- OUTER CASING BOTTOM -->
<path class="casing"
      d="
      M35 255

      Q120 310 260 295
      Q420 330 600 305
      Q760 285 960 230
      " />

<!-- FAN -->
<rect id="Fan" class="fan"
      x="120" y="65"
      width="22"
      height="220">
    <title>Fan</title>

</rect>

<!-- LPC -->
<polygon id="LPC" class="part"
         points="
         200,95
         270,95
         310,120
         330,175
         310,230
         270,255
         200,255
         80,175
         ">
    <title>LPC</title>
</polygon>

<!-- HPC -->
<polygon id="HPC" class="core"
         points="
         320,115
         470,115
         510,145
         525,175
         510,205
         470,235
         320,235
         340,175
         ">
    <title>HPC</title>
</polygon>

<!-- COMBUSTOR TOP -->
<rect id="Combustor_top" class="hot"
      x="590"
      y="105"
      rx="20"
      ry="20"
      width="90"
      height="35">
    <title>Combustor_top</title>
</rect>

<!-- COMBUSTOR BOTTOM -->
<rect id="Combustor_bottom" class="hot"
      x="590"
      y="210"
      rx="20"
      ry="20"
      width="90"
      height="35">
    <title>Combustor_bottom</title>
</rect>

<!-- N1 -->
<rect id="N1_shaft" class="core"
      x="515"
      y="150"
      width="180"
      height="50">
    <title>N1_shaft</title>
</rect>

<!-- HPT -->
<rect id="HPT" class="core"
      x="705"
      y="90"
      width="10"
      height="180">
    <title>HPT</title>
</rect>

<!-- LPT -->
<rect id="LPT" class="part"
      x="730"
      y="90"
      width="10"
      height="180">
    <title>LPT</title>
</rect>

<!-- N2 SHAFT -->
<rect id="N2_shaft" class="part"
      x="325"
      y="165"
      width="500"
      height="20">
    <title>N2_shaft</title>
</rect>


<!-- NOZZLE -->
<polygon id="Nozzle" class="part"
         points="
         750,130
         980,175
         750,220
         ">
    <title>Nozzle</title>
</polygon>

</svg>
"""

COMPONENT_SENSORS = {

    "Fan": [
        ("T2", "Total temperature at fan inlet", "°R", "sensor_1_streak"),
        ("P2", "Pressure at fan inlet", "psia", "sensor_5_streak"),
        ("Nf", "Physical fan speed", "rpm", "sensor_8_streak"),
        ("NRf", "Corrected fan speed", "rpm", "sensor_13_streak"),
        ("Nf_dmd", "Demanded fan speed", "rpm", "sensor_18_streak"),
        ("PCNfR_dmd", "Demanded corrected fan speed", "rpm", "sensor_19_streak"),
    ],

    "LPC": [
        ("T24", "Total temperature at LPC outlet", "°R", "sensor_2_streak"),
        ("P15", "Total pressure in bypass duct", "psia", "sensor_6_streak"),
        ("BPR", "Bypass ratio", "-", "sensor_15_streak"),
    ],

    "HPC": [
        ("T30", "Total temperature at HPC outlet", "°R", "sensor_3_streak"),
        ("P30", "Total pressure at HPC outlet", "psia", "sensor_7_streak"),
        ("Ps30", "Static pressure at HPC outlet", "psia", "sensor_11_streak"),
        ("Nc", "Physical core speed", "rpm", "sensor_9_streak"),
        ("NRc", "Corrected core speed", "rpm", "sensor_14_streak"),
    ],

    "Combustor_top": [
        ("farB", "Burner fuel-air ratio", "-", "sensor_16_streak"),
        ("phi", "Fuel flow / Ps30 ratio", "pps/psi", "sensor_12_streak"),
    ],

    "Combustor_bottom": [
        ("epr", "Engine pressure ratio (P50/P2)", "-", "sensor_10_streak"),
    ],

    "HPT": [
        ("htBleed", "Bleed enthalpy", "--", "sensor_17_streak"),
        ("W31", "HPT coolant bleed", "lbm/s", "sensor_20_streak"),
    ],

    "LPT": [
        ("T50", "Total temperature at LPT outlet", "°R", "sensor_4_streak"),
        ("W32", "LPT coolant bleed", "lbm/s", "sensor_21_streak"),
    ],

    "N1_shaft": [
        ("Nf", "Low-pressure shaft speed", "rpm", "sensor_8_streak"),
        ("NRf", "Corrected low-pressure shaft speed", "rpm", "sensor_13_streak"),
    ],

    "N2_shaft": [
        ("Nc", "High-pressure shaft speed", "rpm", "sensor_9_streak"),
        ("NRc", "Corrected high-pressure shaft speed", "rpm", "sensor_14_streak"),
    ],

    "Nozzle": [
        ("epr", "Engine pressure ratio", "-", "sensor_10_streak"),
        ("T50", "LPT outlet temperature", "°R", "sensor_4_streak"),
    ],
}


def compute_streaks(series):
    change = series.ne(series.shift())
    groups = change.cumsum()
    return series.groupby(groups).cumcount() + 1


def build_engine_view(latest):
    status = {}
    dynamic_svg = svg
    unchanged = []

    for component, sensors in COMPONENT_SENSORS.items():

        tooltip = f"{component}\n\n"
        critical = False

        for name, desc, unit, streak_col in sensors:

            streak = int(latest[streak_col])

            if streak >= STREAK_THRESHOLD:

                critical = True

                tooltip += (
                    f"{name} ({unit})\n"
                    f"{desc}\n"
                    f"Unchanged since {streak} cycles\n\n"
                )

                unchanged.append({
                    "component": component,
                    "sensor": name,
                    "description": desc,
                    "unit": unit,
                    "streak": streak
                })

        if not critical:
            tooltip += "No unchanged sensors."

        status[component] = "critical" if critical else "ok"

        dynamic_svg = dynamic_svg.replace(
            f"<title>{component}</title>",
            f"<title>{tooltip}</title>"
        )

    return status, dynamic_svg, unchanged

def render_engine(latest):

    status, dynamic_svg, unchanged = build_engine_view(latest)

    st.iframe(
        build_css(status) + dynamic_svg,
        height="content"
    )

    st.subheader(f"Sensors with unchanged values at cycle {latest['cycle']}")
    st.write("Think about better sensor placement if sensors keep unchanged over whole life cycle. This can affect the quality of ML models.")
    
    if not unchanged:
        st.success("No sensors exceeded the threshold.")
        return

    for sensor in unchanged:

        st.markdown(
            f"- **{sensor['component']}** → "
            f"**{sensor['sensor']}** ({sensor['unit']})  \n"
            f"  {sensor['description']}  \n"
            f"  **Unchanged for {sensor['streak']} cycles**"
        )