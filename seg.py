from itertools import product
letters = "GBRY"
nums = "1234"
levels = [ch + num for num, ch in product(nums, letters)]
level_codes = [2 ** i for i in range(len(levels))]
code_to_level = {i: j for i, j in zip(level_codes, levels)}
level_to_code = {j: i for i, j in zip(level_codes, levels)}

def read_seg(filename: str, encoding: str = "utf-8-sig") -> tuple[dict, list[dict]]:
    """
    This is a function that reads seg files
    """
    with open(filename, encoding=encoding) as f:
        lines = [line.strip() for line in f.readlines()]

    # найдём границы секций в списке строк:
    header_start = lines.index("[PARAMETERS]") + 1
    data_start = lines.index("[LABELS]") + 1

    # прочитаем параметры
    params = {}
    for line in lines[header_start:data_start - 1]:
        key, value = line.split("=")
        params[key] = int(value)

    # прочитаем метки
    labels = []
    for line in lines[data_start:]:
        # если в строке нет запятых, значит, это не метка и метки закончились
        if line.count(",") < 2:
            break
        pos, level, name = line.split(",", maxsplit=2)
        label = {
            "position": int(pos) // params["BYTE_PER_SAMPLE"] // params["N_CHANNEL"],
            "level": code_to_level[int(level)],
            "name": name
        }
        labels.append(label)
    return params, labels

def match_words_to_sounds(filename_upper, filename_lower):
    """
    This is a function that matches allophones to corresponding words
    """
    _, labels_upper = read_seg(filename_upper, encoding="cp1251")
    _, labels_lower = read_seg(filename_lower)
    res, global_positions = [], []
    ctr = 0
    for start, end in zip(labels_upper, labels_upper[1:]):
        if not start["name"]:
            continue  # паузы нас не интересуют
        labels = []
        for label in labels_lower[ctr:]:
            if start["position"] <= label["position"] < end["position"]:
                ctr += 1
                labels.append(label)
            elif end["position"] <= label["position"]:  # оптимизация
                break
        label_names = []
        positions = []
        for i in labels:
            phoneme = i["name"]
            if phoneme != '~':
                if phoneme[-1].isdigit() or phoneme[-1] in ("_", "'"):
                    phoneme = phoneme[:-1]
                label_names.append(phoneme)
                positions.append(i["position"])
            
        # label_names = [i["name"] for i in labels if i["name"]]
        res.append(label_names)
        global_positions.append(positions)

    return res, global_positions

def get_f0(filename: str, Y1, min_f0: float = 0.0) -> tuple[list[float]]:
    """
    This is a function that extracts f0 values and corresponding time marks
    """
    params, labels = read_seg(filename)
    labels = labels[1:-1]  # уберём метки с границами файла
    times, f0_values = [], []

    _, labelsY1 = read_seg(Y1, encoding="cp1251")
    word_counter = 0
    for l1, l2 in zip(labelsY1, labelsY1[1:]):
        times.append([])
        f0_values.append([])
        for left, right in zip(labels, labels[1:]):
            time = (right["position"] + left["position"]) / 2
            if time < l1["position"] or time > l2["position"]:
                continue
            f0 = 1 / ((right["position"] - left["position"]) / params["SAMPLING_FREQ"])
            times[word_counter].append(time)
            if f0 < min_f0 or left["name"] == "0":  # обозначение в CORPRES
                f0_values[word_counter].append(0)
            else:   
                f0_values[word_counter].append(int(f0))
        word_counter += 1
    return times, f0_values

def words_middle(seg_Y1):
    """
    This is a function that extracts a middle point of each word in a seg_Y1 file
    """
    _, labels = read_seg(seg_Y1, encoding="cp1251")
    middle_points = []
    for l1, l2 in zip(labels, labels[1:]):
        middle_point = l2["position"] - l1["position"]
        middle_points.append(middle_point)

    return middle_points
