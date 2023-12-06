import math

maxLatLonDiff = 0.005
maxDist = 80  # meters


def main(args):
    lmap = {}
    #with open("C:/Users/Michael/Documents/ADFC-Job/RVP/billwerder.txt", "r", encoding="utf-8") as input:
    with open("C:/Users/Michael/Documents/ADFC-Job/RVP/locs.txt", "r", encoding="utf-8") as input:
        for l in input:
            x = l.find(',')
            y = l.find(')')
            lat = float(l[1:x])
            lon = float(l[x + 2: y])
            loc = l[y + 2:].strip()
            # print(lat, lon, loc)
            lmap[(lat, lon, loc)] = (lat, lon)

    print("Map entries:", len(lmap))
    count = len(lmap)
    while (count != 0):
        cmap = {}
        count = 0
        print("next iteration", count)
        for x1, t1 in enumerate(lmap.keys()):
            for x2, t2 in enumerate(lmap.keys()):
                if x1 == x2: continue
                l1 = lmap[t1]
                l2 = lmap[t2]
                if abs(l1[0] - l2[0]) > maxLatLonDiff or abs(l1[1] - l2[1]) > maxLatLonDiff:
                    d = maxDist
                else:
                    d = distance((l1[0], l1[1]), (l2[0], l2[1]))
                if d >= maxDist:
                    #print("notsame", d, t1[2], "|", t2[2])
                    continue
                elif d > 1:
                    #print("same", d, t1[2], "|", t2[2])
                    mlat = (l1[0] + l2[0]) / 2.0
                    mlon = (l1[1] + l2[1]) / 2.0
                    oldSet = cmap.get(l1)
                    if oldSet is not None:
                        for t in oldSet:
                            lmap[t] = (mlat, mlon)
                        del cmap[(l1[0], l1[1])]
                        cmap[(mlat, mlon)] = oldSet
                    else:
                        oldSet = set()
                        cmap[(mlat, mlon)] = oldSet
                    lmap[t1] = (mlat, mlon)
                    lmap[t2] = (mlat, mlon)
                    oldSet.add(t1)
                    oldSet.add(t2)
                    count += 1
                else:
                    #print("equal")
                    pass
    sortedMap = {}
    for t in lmap.keys():
        (lat,lon) = lmap[t]
        lat = str(round(lat, 6))
        lon = str(round(lon, 6))
        lset = sortedMap.get((lat, lon))
        if lset is None:
            lset = set()
            sortedMap[(lat,lon)] = lset
        lset.add(t)
    print(f"{len(sortedMap)} verschiedene Orte")
    print('[');
    for key in sortedMap.keys():
        lset = sortedMap[key]
        llist = list(lset)
        key = average(llist)
        lat = str(key[0]).replace(".", ",")
        lon = str(key[1]).replace(".", ",")
        for t in llist:
            # print(f'{{"latitude": {lat}, "longitude": {lon}, "key": "{lat}:{lon}", "ort": "{t[2]}"}},')
            print(f"{lat};{lon};{t[2]}")
    print(']');


        # t = llist[0]
        # dist = int(distance((float(key[0]), float(key[1])), (t[0], t[1])))
        # print(f"{key[0]}:{key[1]}\t{t[0]}:{t[1]}\t{t[2]}  {dist}")
        # for t in llist[1:]:
        #     dist = int(distance((float(key[0]), float(key[1])), (t[0], t[1])))
        #     print(f"\t\t\t\t\t{t[0]}:{t[1]}\t{t[2]}  {dist}")






def distance(origin, destination):
    """
    Calculate the Haversine distance.

    Parameters
    ----------
    origin : tuple of float
        (lat, long)
    destination : tuple of float
        (lat, long)

    Returns
    -------
    distance_in_km : float

    Examples
    --------
    >>> origin = (48.1372, 11.5756)  # Munich
    >>> destination = (52.5186, 13.4083)  # Berlin
    >>> round(distance(origin, destination), 1)
    504.2
    """
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371  # km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    d = radius * c * 1000.0  # return meters
    return d

def average(llist):
    latsum = 0
    lonsum = 0
    for l in llist:
        latsum += l[0]
        lonsum += l[1]
    lat = latsum/len(llist)
    lon = lonsum/len(llist)
    return (str(round(lat,6)), str(round(lon,6)))

if __name__ == '__main__':
    # print("dist1", distance((53.0, 10.0), (53.01, 10.0)))
    # print("dist2", distance((53.0, 10.0), (53.0, 10.01)))
    # loc1 = (53.109009, 9.398985)
    # locs = ((53.109347, 9.399108), (53.108813, 9.39859), (53.10864, 9.399257), (53.10842, 9.399008))
    # for l in locs:
    #     print(distance(loc1, l))

    """
    locs = (
    (53.497363,10.131987),
    (53.497342,10.131894),
    (53.497387,10.13193),
    (53.497505,10.132248),
    (53.497275,10.131916),
    (53.49762,10.132281),
    (53.497824,10.132699),
    (53.49799,10.132506),
    (53.498096,10.132356),
    (53.498562,10.132781),
    (53.498342,10.132087),
    )
    loc = average(locs)
    for l in locs:
        print(loc, l, int(distance(loc, l)))

    loc = (53.498358, 10.132516)
    for l in locs:
        print(loc, l, int(distance(loc, l)))
    """

    """
    St. Georg:
    locm = ((53.552415,10.008388), (53.553102,10.005534), (53.553605,10.023834), (53.55387,10.00763))
    locd = ((53.552415,10.008388), (53.553154,10.005544), (53.553193,10.005261), (53.55296,10.005796), (53.553605,10.023834),
            (53.553812,10.007671), (53.553783,10.007654), (53.553732,10.007086), (53.553812,10.007654),
            (53.553983,10.007814), (53.554198,10.007451), (53.553771,10.008078))
    for lm in locm:
        for ld in locd:
            d = int(distance(lm, ld))
            if (d < 100):
                print(lm, ld, d)
    """

    """
    # Volksdorf
    locm = ((53.649279,10.163545),(53.650272,10.162787))
    locd = ((53.649279,10.163545), (53.65021,10.163145), (53.650392,10.1634), (53.650243,10.162301), (53.650243,10.162301))
    print("locm", int(distance(locm[0], locm[1])))
    for lm in locm:
        for ld in locd:
            d = int(distance(lm, ld))
            if (d < 100):
                print(lm, ld, d)
    """





    main(None)
