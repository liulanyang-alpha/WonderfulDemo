import operator
import subprocess
import xmltodict
import json
import argparse
import glob
import os
import time
import cv2
import numpy as np
from PIL import Image
from pillow_heif import register_heif_opener

from datetime import datetime, timedelta


def convert_line(line, type):
    if type == "coord":
        sp = line.split()
        return [float(x) for x in sp]
    elif type == "when":
        return datetime.fromisoformat(line[:-1])
    elif type == "extend":
        sp = line.split(",")
        return [float(x) for x in sp]
    else:
        return line


def get_size(path, type="image"):
    if type == "image":
        img = Image.open(open(path, "rb"))
        return [img.width, img.height]
    elif type == "video":
        cap = cv2.VideoCapture(path)
        return [
            int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        ]
    else:
        return None


def assets_list_append_one(assets_list, icon_path, index):
    assets_list.append(
        {
            "type": "image",
            "index": index,
            "path": "",
            "size": None,
            "icon_path": icon_path,
            "icon_size": get_size(icon_path),
        }
    )


# use for convert iphone HEIC/MOV to jpg/mp4
def rename_file_by_create_time(path):
    exif_info = subprocess.Popen("exiftool " + path + """ | grep "Create Date" """, shell=True, stdout=subprocess.PIPE).stdout.readlines()
    create_time = exif_info[0].decode("utf-8").split(":", maxsplit=1)[-1].strip()
    create_datetime = datetime.fromtimestamp(time.mktime(time.strptime(create_time, "%Y:%m:%d %H:%M:%S")))

    register_heif_opener()

    # ("IMG_%Y%m%d_%H%M%S.jpg")
    if path.endswith(".HEIC"):
        path2 = create_datetime.strftime("IMG_%Y%m%d_%H%M%S.jpg")
        image = Image.open(path)
        image.save(os.path.join(os.path.dirname(path), path2))
    elif path.endswith(".MOV"):
        create_datetime = create_datetime + timedelta(hours=8)
        path2 = create_datetime.strftime("VID_%Y%m%d_%H%M%S.mp4")
        path2 = os.path.join(os.path.dirname(path), path2)
        os.system("/usr/bin/ffmpeg -i {} -crf 23 -preset medium -movflags +faststart -c:a aac {}".format(path, path2))


# pre_process_iphone data  convert: image/video
def pre_process_iphone_data(folder):
    files = glob.glob(os.path.join(folder, "*.HEIC")) + glob.glob(os.path.join(folder, "*.MOV"))
    for pa in files:
        rename_file_by_create_time(pa)


# 解析kml数据，获得gps数据
def parse_kml(kml_path):
    data = xmltodict.parse(open(kml_path, "r").read())
    place_mark = data["kml"]["Document"]["Folder"]["Placemark"]

    description = place_mark["description"]["div"]
    description_keys = ["本段里程", "最高海拔", "最低海拔", "累计爬升", "累计下降"]
    description_keys2 = ["开始时间", "结束时间"]
    description_dict = {k: 0 for k in description_keys}
    for desc in description:
        for k in description_keys:
            if k in desc:
                description_dict[k] = float(desc.split(":")[-1][:-1])
                break
        for k in description_keys2:
            if k in desc:
                description_dict[k] = desc.split(":", maxsplit=1)[-1]
                break
    print(description_dict)

    gx_coords = place_mark["gx:Track"]["gx:coord"]
    gx_coords = [convert_line(x, type="coord") for x in gx_coords]

    gx_extended_datas = place_mark["gx:Track"]["ExtendedData"]["Data"]["value"].split(";")[:-1]  # 去掉最后一个;导致的空字符
    gx_extended_datas = [convert_line(x, type="extend") for x in gx_extended_datas]

    start_time = datetime.fromisoformat(description_dict["开始时间"])

    gx_whens = place_mark["gx:Track"]["when"]
    gx_whens = [convert_line(x, type="when") for x in gx_whens]
    gx_whens = [x + (start_time - gx_whens[0]) for x in gx_whens]  # 时间修正， 原始的时间不准确
    # gx_whens_str = [x.strftime("%Y-%m-%d %H:%M:%S") for x in gx_whens]

    print(len(gx_coords), len(gx_whens), len(gx_extended_datas))

    description_dict["center"] = np.array(gx_coords).mean(axis=0).tolist()
    return {
        "description": description_dict,
        "gx_coords": gx_coords,
        "gx_whens": gx_whens,
        "gx_extended_datas": gx_extended_datas,
    }


def process_folder(args):
    kml_path = glob.glob(os.path.join(args.folder, "*.kml"))[0]
    images_path = glob.glob(os.path.join(args.folder, "*.jpg"))
    videos_path = glob.glob(os.path.join(args.folder, "*.mp4"))

    # load kml data to json
    infos = parse_kml(kml_path)

    image_whens = [time.strptime(os.path.basename(x), "IMG_%Y%m%d_%H%M%S.jpg") for x in images_path]
    video_whens = [time.strptime(os.path.basename(x), "VID_%Y%m%d_%H%M%S.mp4") for x in videos_path]

    image_whens = [datetime.fromtimestamp(time.mktime(x)) for x in image_whens]
    video_whens = [datetime.fromtimestamp(time.mktime(x)) for x in video_whens]

    # search nearest time
    assets_list = []
    assets_list_append_one(assets_list, icon_path="data/icons/startPointStyle.png", index=0)
    for i, t in enumerate(image_whens):
        diff = [abs(x - t) for x in infos["gx_whens"]]
        min_index, min_value = min(enumerate(diff), key=operator.itemgetter(1))
        size = get_size(images_path[i], type="image")
        icon_path = "data/icons/MarkerStylePicture.png"
        icon_size = get_size(icon_path)

        assets_list.append(
            {
                "type": "image",
                "index": min_index,
                "path": images_path[i],
                "size": size,
                "icon_path": icon_path,
                "icon_size": icon_size,
            }
        )

    for i, t in enumerate(video_whens):
        diff = [abs(x - t) for x in infos["gx_whens"]]
        min_index, min_value = min(enumerate(diff), key=operator.itemgetter(1))
        size = get_size(videos_path[i], type="video")
        icon_path = "data/icons/MarkerStyleVideo.png"
        icon_size = get_size(icon_path)
        assets_list.append({
            "type": "video",
            "index": min_index,
            "path": videos_path[i],
            "size": size,
            "icon_path": icon_path,
            "icon_size": icon_size,
        })

    # save
    assets_list_append_one(assets_list, icon_path="data/icons/endPointStyle.png", index=len(infos["gx_whens"]) - 1)
    assets_list = sorted(assets_list, key=lambda x: x["index"])
    gx_coords = np.array(infos["gx_coords"])
    gx_coords_diff = np.abs(gx_coords[1:] - gx_coords[:-1])[:, :2]
    speeds = []
    for i in range(0, len(assets_list) - 1):
        idx0 = assets_list[i]["index"]
        idx1 = assets_list[i + 1]["index"]
        s = np.sum(gx_coords_diff[idx0:idx1])
        s = max(s, 0.01)
        speeds.append(s)
    speeds.append(speeds[-1])
    speeds = np.array(speeds) / 0.01
    for i in range(len(assets_list)):
        assets_list[i]["speed"] = speeds[i]

    infos["assets"] = assets_list
    json.dump(
        infos,
        open(os.path.join(args.folder, "infos.json"), "w", encoding="utf-8"),
        indent=4,
        sort_keys=True,
        default=str,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--folder", default="data/妙峰山2-20220423")
    args = parser.parse_args()
    process_folder(args.type())

    # print(get_size("data/妙峰山-20220423/VID_20220423_160001.mp4", type="video"))
    # print(get_size("data/妙峰山-20220423/IMG_20220423_173013.jpg", type="image"))
    # pre_process_iphone_data(args.type())
