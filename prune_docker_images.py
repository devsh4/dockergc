import docker
import datetime
from dateutil import parser
import logging
import pytz
import sys

# Initialize docker client
client = docker.from_env()
logging.basicConfig(level=logging.INFO)

# Constants
TAGS_TO_RETAIN = 3

def prune_images(images):
    for image in images:
        try:
            logging.info("Pruning image: %s", image)
            client.images.remove(image=image, force=True)
            logging.info("Successfully pruned image: %s \n", image)
        except docker.errors.APIError as e:
            if "image has dependent child images" in str(e):
                logging.warning(
                    "Can't delete image [%s] as it has dependent child images. \n", image)
            elif "image is being used by stopped container" in str(e):
                logging.warning(
                    "Can't delete image [%s] as it is in use. \n", image)
            else:
                logging.error(str(e))


def get_images_to_be_pruned(base_images, TAGS_TO_RETAIN, THRESHOLD_IN_MINUTES):
    images_to_be_pruned = []

    for base_image in base_images:
        # Preserving latest 3 images
        sorted_images = sorted(
            base_images[base_image], key=lambda d: d['created_at'], reverse=True)
        eligible_images = sorted_images[TAGS_TO_RETAIN:]

        # Filtering by THRESHOLD_IN_MINUTES
        for x in eligible_images:
            createdTime = parser.parse(x["created_at"])
            if createdTime < datetime.datetime.now(pytz.utc)-datetime.timedelta(minutes=THRESHOLD_IN_MINUTES):
                images_to_be_pruned.append(x["id"])

    return images_to_be_pruned


def get_all_images():
    images = {}

    for image in client.images.list():
        # Assumption 1: Don't want to prune intermediate images as that might still be used in latest image versions
        # Assumption 2: Don't want to prune 1 image that has "n" tags, because technically that's still 1 version & we want to keep last 3 images
        if image.tags != [] and len(image.tags) == 1:
            base_image = image.tags[0].split(":")[0]
            id = image.id
            created_time = image.attrs['Created']

            # Initialize the dictionary with empty list as value
            if not images.get(base_image):
                images[base_image] = []

            # Push images to dictionary
            images[base_image].append({"id": id, "created_at": created_time})

    return images


if __name__ == "__main__":
    # Parse argument
    THRESHOLD_IN_MINUTES = int(sys.argv[1]) if len(sys.argv) > 1 else 1440
    
    # Get all images
    all_images = get_all_images()
    
    # Get images to be pruned after applying filter
    images_to_be_pruned = get_images_to_be_pruned(
        all_images, TAGS_TO_RETAIN, THRESHOLD_IN_MINUTES)

    # Prune images
    prune_images(images_to_be_pruned)
