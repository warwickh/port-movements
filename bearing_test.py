import math, numpy as np
        
def get_bearing( lat1, lon1, lat2, lon2):
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)
    dLon = lon2 - lon1;
    y = math.sin(dLon) * math.cos(lat2);
    x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon);
    brng = np.rad2deg(math.atan2(y, x));
    if brng < 0: brng+= 360
    return brng

old = [39.18763333333333, -76.46496666666667]
new =  [39.18123333333333, -76.44356666666665]
print(get_bearing(old[0], old[1], new[0], new[1]))

#gives 163 but should be 110