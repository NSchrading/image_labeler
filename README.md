A pure-python image labeling tool for binary image classification.

Displays a configurable grid of clickable images. Clicking on the image will hide it so you are left with the
positive (or negative if you wish) class. Pressing enter will move on to the next set of images until all images
are labeled.

Supported actions:
* Click: Hide/unhide an image to label it as a class.
* Enter: Commit labels and move onto the next set of images.
* Esc: End; choose to commit/discard the latest set of labels.


usage: label.py [-h] [--directory DIRECTORY] [--positive_label POSITIVE_LABEL]
                [--negative_label NEGATIVE_LABEL] [--hide_positive] [--init]
                [--num_images NUM_IMAGES]

optional arguments:
  -h, --help            show this help message and exit
  --directory DIRECTORY
                        Path to directory of images to label. Also where the
                        database is located.
  --positive_label POSITIVE_LABEL
                        What to label the positive class.
  --negative_label NEGATIVE_LABEL
                        What to label the negative class.
  --hide_positive       Pass this to make it so that you click on (hide) the
                        positive class instead of the negative class.
  --init                Pass this argument to initialize the database of
                        images or if new images have been added to the
                        directory.
  --num_images NUM_IMAGES
                        The number of images to display per row and column.


Stores labels and image paths in a sqlite3 database, images.db:
Table images, columns = (path text, label text)