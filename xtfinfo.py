import numpy as np
from pyxtf import xtf_read, concatenate_channel, XTFHeaderType, XTFChannelType

xtf_path = 'xtfs\sasi-P-upper-20240314-110550-wrk_l1.xtf'

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points
    on the earth (specified in decimal degrees)
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of earth in kilometers. Use 3956 for miles
    return c * r

def main():
    (fh, p) = xtf_read(xtf_path)
    print(fh)
    if XTFHeaderType.sonar in p:
        
        first_ping = p[XTFHeaderType.sonar][0]
        last_ping = p[XTFHeaderType.sonar][-1]

        print(first_ping.PingNumber, first_ping.SensorYcoordinate, first_ping.SensorXcoordinate)
        print(last_ping.PingNumber, last_ping.SensorYcoordinate, last_ping.SensorXcoordinate)

        distance = haversine(first_ping.SensorYcoordinate, first_ping.SensorXcoordinate, last_ping.SensorYcoordinate, last_ping.SensorXcoordinate)

        print(f"The distance between the points is {distance:.2f} km.")
        print(f"The distance between the points is {distance*1000:.2f} m.")

        for ping in p[XTFHeaderType.sonar]:
            data_elements_in_ping = len(ping.data[0])
            print(f"{ping.PingNumber}, {data_elements_in_ping} {ping.SensorYcoordinate}, {ping.SensorXcoordinate}, {ping.ping_chan_headers[0].SlantRange}, {ping.ping_chan_headers[0].GroundRange}, {ping.ping_chan_headers[0].SlantRange/data_elements_in_ping*100} cm/pixel")


if __name__ == "__main__":
    main()