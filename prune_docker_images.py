import docker
import datetime
from dateutil import parser
import pytz
import json
import logging

client = docker.from_env()
logging.basicConfig(level=logging.INFO)
THRESHOLD_IN_MINUTES = 365
TAGS_TO_RETAIN = 3


def prune_images(eligible_images):
    for image in eligible_images:
        try:
            client.images.remove(image=image, force=True)
        except docker.errors.APIError as e:
            if "image has dependent child images" in str(e):
                logging.warning(
                    "Can't delete image %s as it has dependent child images.", image)
            else:
                logging.error(str(e))

    logging.info("Pruned image versions - %s", eligible_images)


def get_eligible_images(images, TAGS_TO_RETAIN, THRESHOLD_IN_MINUTES):
    eligible_images = []

    for i in images:
        if len(images[i]) > TAGS_TO_RETAIN:
            for y in images[i]:
                for k, v in y.items():
                    createdTime = parser.parse(v)
                    if createdTime < datetime.datetime.now(pytz.utc)-datetime.timedelta(days=THRESHOLD_IN_MINUTES) and len(images[i]) > TAGS_TO_RETAIN:
                        eligible_images.append(k)

    logging.info("Eligible images for pruning %s", eligible_images)
    return eligible_images


def get_all_images():
    images = {}

    for image in client.images.list():
        # Assumption 1: Don't want to prune intermediate images as that might still be used in latest image versions
        # Assumption 2: Don't want to prune 1 image that has "n" tags, because technically that's still 1 version & we want to keep last 3 images
        if image.tags != [] and len(image.tags) == 1:
            base_image = image.tags[0].split(":")[0]
            id = image.id
            created_time = image.attrs['Created']

            # Initialize the dictionary with a list as value
            if not images.get(base_image):
                images[base_image] = []

            # Push images to dictionary
            images[base_image].append({id: created_time})

    print(json.dumps(images, indent=4))
    return images


if __name__ == "__main__":
    all_images = get_all_images()
    eligible_images = get_eligible_images(
        all_images, TAGS_TO_RETAIN, THRESHOLD_IN_MINUTES)

    prune_images(eligible_images)
