import math
from trajectory import generate_well_trajectory

surface = (0.0, 0.0, 0.0)
target = (1200.0, 800.0, 4820.0)
df, summary = generate_well_trajectory(surface, 1000.0, target, 1.5, trajectory_type='S-Type (Type III)', drop_rate=3.0, max_inclination=45.0)
print(summary)
coords = df.iloc[-1][['Northing (ft)', 'Easting (ft)', 'TVD (ft)']].to_dict()
print('Final coords', coords)
print('Final horiz disp', math.hypot(coords['Northing (ft)'], coords['Easting (ft)']))
print('Final MD', df.iloc[-1]['MD (ft)'])
