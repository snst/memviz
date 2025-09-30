import yaml
import svg
from enum import Enum, auto
import argparse
import os

entries = []
address_dict = {}
bars = []


colors = [
    "#e6194b",
    "#3cb44b",
    "#c6af19",
    "#4363d8",
    "#f58231",
    "#911eb4",
    "#46f0f0",
    "#f032e6",
    "#808080",
    "#008080",
    "#9a6324",
    "#800000",
    "#808000",
]
color_index = 0


def get_color():
    global color_index
    color_index += 1
    return colors[color_index % len(colors)]


class AddrList:
    def __init__(self):
        self.start = []
        self.end = []


def add_addr(addr):
    if not addr in address_dict:
        items = AddrList()
        address_dict[addr] = items
    else:
        items = address_dict[addr]
    return items


def add_addr_start(entry):
    entries = add_addr(entry.start).start
    for i in range(0, len(entries)):
        if entry.size > entries[i].size:
            entries.insert(i, entry)
            return
    entries.append(entry)


def add_addr_end(entry):
    entries = add_addr(entry.end).end
    for i in range(0, len(entries)):
        if entry.size < entries[i].size:
            entries.insert(i, entry)
            return
    entries.append(entry)


class RamEntry:
    def __init__(self, data):
        self.start = self.get(data, "start")
        self.end = self.get(data, "end")
        self.size = self.get(data, "size")
        self.name = data.get("name", "")
        if self.end is None and self.size is not None:
            self.end = self.start + self.size - 1
        if self.size is None and self.end is not None:
            self.size = self.end + self.start
        add_addr_start(self)
        add_addr_end(self)

    def get(self, data, name):
        if name in data:
            return int(data[name])
        return None


def load_ram_layout(yaml_path):
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
    items = data.get("layout", [])
    for item in items:
        entries.append(RamEntry(item))


def add_start(ram, y):
    global bars
    col = get_color()
    for i in range(0, len(bars)):
        if bars[i] is None:
            bars[i] = (ram, y, col)
            return col
    bars.append((ram, y, col))
    return col


def get_start(ram):
    global bars
    for i in range(0, len(bars)):
        if bars[i] is not None and bars[i][0] == ram:
            ret = bars[i][1]
            ret_color = bars[i][2]
            bars[i] = None
            return i, ret, ret_color
    return None


def draw_layout(svg_path):
    font_height = 14
    x = 0
    y = font_height
    bar_width = 15
    bar_x = 80
    addr_color = "#000000"
    addr_space = 20

    text_y_offset = font_height / 2 - 2
    elements: list[svg.Element] = []
    elements2: list[svg.Element] = []
    elements_addr: list[svg.Element] = []
    last_addr = None
    for addr, items in sorted(address_dict.items()):
        if addr - 1 != last_addr:
            y += addr_space

        start_y = y
        addr_y = start_y + text_y_offset

        for item in items.end:
            i, start_bar_y, col = get_start(item)
            text = svg.Text(
                x=0,
                y=y + text_y_offset,
                text=f"- {item.name}",
                font_size=font_height,
                fill=col,
            )
            elements2.append(text)
            addr_y = text.y
            # bar
            bar_ext = 7
            rect = svg.Rect(
                x=x + bar_x + i * bar_width,
                y=start_bar_y - (font_height / 2),
                width=bar_width,
                height=start_y - start_bar_y + font_height * (len(items.end) + 0),
                fill=col,
            )  # , stroke="#333")
            elements.append(rect)
            y += font_height
        for item in items.start:
            col = add_start(item, start_y)
            text = svg.Text(
                x=0,
                y=y + text_y_offset,
                text=f"+ {item.name} [0x{(item.size):x}, {item.size}]",
                font_size=14,
                fill=col,
            )
            elements2.append(text)
            y += font_height

        text = svg.Text(
            x=x, y=addr_y, text=f"0x{addr:08x}", font_size=font_height, fill=addr_color
        )
        elements_addr.append(text)

        last_addr = addr

    desc_x = max(bar_x + len(bars) * bar_width + 5, bar_x)
    for e in elements2:
        e.x += desc_x

    bg = svg.Rect(x=0, y=0, width=300, height=y - addr_space / 2 + 20, fill="#ffffff")
    canvas = svg.SVG(
        viewBox=svg.ViewBoxSpec(0, 0, bg.width, bg.height),
        elements=[bg] + elements + elements2 + elements_addr,
    )

    with open(svg_path, "w") as f:
        f.write(str(canvas))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Draw RAM layout from YAML file.")
    parser.add_argument("filename", help="YAML file describing RAM layout")
    args = parser.parse_args()
    layout = load_ram_layout(args.filename)
    svg_path = os.path.splitext(args.filename)[0] + ".svg"
    draw_layout(svg_path)
