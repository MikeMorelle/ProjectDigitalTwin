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
<rect id="COMTOP" class="hot"
      x="590"
      y="105"
      rx="20"
      ry="20"
      width="90"
      height="35">
    <title>Combustor</title>
</rect>

<!-- COMBUSTOR BOTTOM -->
<rect id="COMBOT" class="hot"
      x="590"
      y="210"
      rx="20"
      ry="20"
      width="90"
      height="35">
    <title>Combustor</title>
</rect>

<!-- N1 -->
<rect id="N1" class="core"
      x="515"
      y="150"
      width="180"
      height="50">
    <title>N1 shaft</title>
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
<rect id="N2" class="part"
      x="325"
      y="165"
      width="500"
      height="20">
    <title>N2 shaft</title>
</rect>


<!-- NOZZLE -->
<polygon id="NOZZLE" class="part"
         points="
         750,130
         980,175
         750,220
         ">
    <title>Nozzle</title>
</polygon>

</svg>
"""
