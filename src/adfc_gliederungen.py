_lv2NameMap = {}
_lv2KvMap = {}


def load(unitsJS):
    global _lv2KvMap
    units = unitsJS.get("units")
    for unit in iter(units):
        key = unit.get("key")
        if len(key) < 3:
            continue
        elif len(key) == 3:
            _lv2NameMap[key] = unit.get("name").split()[1]  # "ADFC Hamburg e.V." -> "Hamburg"
            continue
        lv = key[0:3]
        if lv not in _lv2KvMap:
            _lv2KvMap[lv] = {}
        kvMap = _lv2KvMap[lv]
        kvMap[key] = unit.get("name").replace("ADFC ", "").replace("ADFC-", "")
    for key in _lv2KvMap.keys():
        if key == "110":
            continue
        kvMap = _lv2KvMap[key]
        kvMap["0"] = "Alles"
        kvMap["1"] = "BV"
        kvMap[key] = "LV " + _lv2NameMap[key]
        pass  # so that we can insert a breakpoint here


def getLVs():
    return _lv2NameMap


def getLV(key):
    return _lv2KvMap[key]
