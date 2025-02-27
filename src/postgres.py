"""
Functions for interacting with Postgres.
"""

import os
from datetime import date
from typing import List, Optional

import psycopg
from dotenv import load_dotenv
from fastapi import APIRouter, Response, encoders
from pydantic import BaseModel

# Load dotenv in the base root refers to application_top
APP_ROOT = os.path.join(os.path.dirname(__file__), '..')
dotenv_path = os.path.join(APP_ROOT, '.env')
load_dotenv(dotenv_path)

# Prep our environment variables / upload .env to Railway.app
DB = os.getenv('PGDATABASE')
HOST = os.getenv('PGHOST')
PORT = os.getenv('PGPORT')
USER = os.getenv('PGUSER')
PW = os.getenv('PGPASSWORD')

# Instantiate a Postgres connection
conn = psycopg.connect(
    dbname=DB, user=USER, password=PW, host=HOST, port=PORT
)

# Create a new router for Postgres Routes
router_postgres = APIRouter()

print(DB, HOST, PORT, USER, PW)
print(conn)


class ImageModel(BaseModel):
    id: int
    name: str
    width: Optional[int]
    height: Optional[int]
    url: Optional[str]
    url_resize: Optional[str]
    date_added: Optional[date]
    date_identified: Optional[date]
    ai_labels: Optional[list]
    ai_text: Optional[list]


@router_postgres.get("/get-image-postgres/{id}", response_model=ImageModel, response_model_exclude_unset=True)
async def get_image_postgres(id: int):
    """
    Fetch a single image from the Postgres database.

    Args:
        id (int): The ID of the image to fetch.

    Returns:
        ImageModel: The image data as an ImageModel instance.
    """
    SQL = "SELECT * FROM images WHERE id = %s"
    DATA = (id,)
    try:
        cur = conn.cursor()
        cur.execute(SQL, DATA)
        image = cur.fetchone()  # Just fetch the specific ID we need
        print(f"Fetched Image Postgres: {image[1]}")
        item = ImageModel(id=image[0], name=image[1], width=image[2], height=image[3], url=image[4],
                          url_resize=image[5], date_added=image[6], date_identified=image[7], ai_labels=image[8], ai_text=image[9])
        return item.model_dump()
    except Exception as err:
        print(err)


async def get_all_images_postgres(response_model=List[ImageModel]):
    """
    Fetch all images from the Postgres database.

    Returns:
        List[ImageModel]: A list of images as ImageModel instances.
    """
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM images ORDER BY id DESC")
        images = cur.fetchall()
        formatted_photos = []
        for image in images:
            formatted_photos.append(
                ImageModel(
                    id=image[0], name=image[1], width=image[2], height=image[3], url=image[4], url_resize=image[
                        5], date_added=image[6], date_identified=image[7], ai_labels=image[8], ai_text=image[9]
                )
            )
    except Exception as err:
        print(err)
    finally:
        cur.close()
    return formatted_photos


async def add_image_postgres(name: str, url: str, ai_labels: list, ai_text: list):
    """
    Add an image and its metadata to the Postgres database.

    Args:
        name (str): The name of the image.
        url (str): The S3 URL of the image.
        ai_labels (list): Labels identified by Amazon Rekognition.
        ai_text (list): Text identified by Amazon Rekognition.
    """

    cur = conn.cursor()
    # Note: don't be tempted to use string interpolation on the SQL string ...
    # have never gotten that to accept a List into a text[] or varchar[] Postgres column
    SQL = "INSERT INTO images (name, url, ai_labels, ai_text) VALUES (%s, %s, %s, %s)"
    DATA = (name, url, ai_labels, ai_text)

    # Attempt to write the image metadata to Postgres
    try:
        cur.execute(SQL, DATA)
        conn.commit()
    except Exception as err:
        conn.rollback()
        print(err)

    # Close the connection
    cur.close()


async def delete_image_postgres(id: int):
    """
    Delete an image from the Postgres database.

    Args:
        id (int): The ID of the image to delete.
    """
    cur = conn.cursor()
    SQL = "DELETE FROM images WHERE id = %s"
    DATA = (id,)

    # Attempt to delete the image from Postgres
    try:
        cur.execute(SQL, DATA)
        conn.commit()
    except Exception as err:
        conn.rollback()
        print(err)

    # Close the connection
    cur.close()
