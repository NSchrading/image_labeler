#!/usr/bin/env python

import argparse
import os
import sqlite3
import tkinter

import matplotlib.pyplot as plt
from PIL import Image
from mpl_toolkits.axes_grid1 import ImageGrid


def get_db(directory):
    conn = sqlite3.connect(os.path.join(directory, 'images.db'))
    cursor = conn.cursor()
    return conn, cursor


def create_table():
    cursor.execute("CREATE TABLE if not exists images (path text UNIQUE, label text)")
    conn.commit()


def set_label(filename, label):
    cursor.execute("UPDATE images SET label = ? where path = ?", (label, filename))
    print("setting {} to {}".format(filename, label))


def initialize_db(directory):
    print("Initializing database of images...")
    create_table()
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            if filename.endswith('.jpg') or filename.endswith('.png') or filename.endswith('.jpeg'):
                cursor.execute("INSERT OR IGNORE INTO images(path, label) VALUES (?, ?)",
                               (os.path.join(dirpath, filename), 'unlabeled'))
    conn.commit()
    print("Done. Ready to label images.")


def get_images(directory):
    try:
        result = cursor.execute("select path from images where label = '' or label = 'unlabeled'")
    except sqlite3.OperationalError:
        initialize_db(directory)
        result = cursor.execute("select path from images where label = '' or label = 'unlabeled'")
    images = result.fetchall()
    if not images:
        print(
            "No images to label. Either:\n\t1) All images are already labeled,\n\t2) You need to initialize the db (pass --init) or, \n\t3) No images are available to label in the provided directory.")
    return images


def resize_preserve_aspect_ratio(image, max_size):
    # Take the greater value, and use it for the ratio
    max_dim = float(max(image.width, image.height))
    ratio = max_dim / max_size

    new_width = int(float(image.width) / ratio)
    new_height = int(float(image.height) / ratio)

    scaled = image.resize((new_width, new_height), Image.LANCZOS)
    offset = (((max_size - scaled.width) // 2), ((max_size - scaled.height) // 2))
    new_image = Image.new("RGB", (max_size, max_size))
    new_image.paste(scaled, offset)

    return new_image


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def setup_plots(num_images, figure_inches):
    plt.rcParams['toolbar'] = 'None'
    f = plt.figure(1, (figure_inches, figure_inches), dpi=dpi)
    grid = ImageGrid(f, 111, nrows_ncols=(num_images, num_images), axes_pad=0.02, share_all=True, aspect=True)
    plt.axis('off')
    plt.tight_layout(pad=0)
    return f, grid


def show_image(filename, ax, i):
    image = Image.open(filename)
    image = resize_preserve_aspect_ratio(image, max_im_size_pixels)

    ax.set_axis_off()
    ax.set_picker(5)
    ax.set_visible(True)
    if first:
        im = ax.imshow(image, interpolation='nearest', aspect='auto')
        image_spaces[i] = im
    else:
        image_spaces[i].set_data(image)
        image_spaces[i].set_extent((-0.5, image.width - 0.5, image.height - 0.5, -0.5))
    ax.image_filename = filename


def onpick(event):
    image = event.artist
    image.set_visible(not image.get_visible())


def label_image(image):
    if hasattr(image, 'image_filename') and image.image_filename is not None:
        if args.hide_positive:
            label = args.negative_label if image.get_visible() else args.positive_label
        else:
            label = args.positive_label if image.get_visible() else args.negative_label
        set_label(image.image_filename, label)


def save_image_labels():
    for ax in grid:
        label_image(ax)
    conn.commit()


def cycle_images(event):
    global done
    global first
    if event.key == 'enter':
        if not first:
            save_image_labels()
        try:
            chunk = next(chunk_generator)
            for i, (ax, filename) in enumerate(zip(grid, chunk)):
                filename = filename[0]
                show_image(filename, ax, i)
            if i < num_images ** 2 - 1:
                for rest in range(i + 1, num_images ** 2):
                    grid[rest].image_filename = None
                    grid[rest].set_visible(False)
            first = False
        except StopIteration:
            print("No more unlabeled images.")
            save_image_labels()
            done = True
    elif event.key == 'escape':
        answer = None
        while answer not in {'y', 'n'}:
            answer = input("Do you want to save this set of images? (y/n) ").lower()
        if answer == 'y':
            save_image_labels()
        done = True


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", help="Path to directory of images to label. Also where the database is located.",
                        default='.')
    parser.add_argument("--positive_label", help="What to label the positive class.", default="1")
    parser.add_argument("--negative_label", help="What to label the negative class.", default="0")
    parser.add_argument("--hide_positive",
                        help="Pass this to make it so that you click on (hide) the positive class instead of the negative class.",
                        action='store_true')
    parser.add_argument("--init",
                        help="Pass this argument to initialize the database of images or if new images have been added to the directory.",
                        action='store_true')
    parser.add_argument("--num_images", help="The number of images to display per row and column.", default=3)
    args = parser.parse_args()
    return args


def calculate_size():
    root = tkinter.Tk()
    root.withdraw()
    res_w, res_h = root.winfo_screenwidth(), root.winfo_screenheight()
    figure_inches = min((res_w / dpi) - 2, (res_h / dpi) - 2)
    max_im_size_pixels = int((figure_inches * dpi) / num_images)
    return figure_inches, max_im_size_pixels


def main():
    f.canvas.mpl_connect('pick_event', onpick)
    f.canvas.mpl_connect('key_press_event', cycle_images)
    plt.ion()

    class FakeEvent(object):
        key = 'enter'

    cycle_images(FakeEvent())


if __name__ == "__main__":
    args = get_args()
    num_images = int(args.num_images)
    dpi = 96
    image_spaces = [None for _ in range(num_images ** 2)]
    figure_inches, max_im_size_pixels = calculate_size()

    conn, cursor = get_db(args.directory)
    with conn:
        if args.init:
            initialize_db(args.directory)
        images = get_images(args.directory)
        if images:
            chunk_generator = chunks(images, num_images ** 2)
            first = True
            done = False
            f, grid = setup_plots(num_images, figure_inches)
            main()
            while not done:
                plt.pause(0.1)
