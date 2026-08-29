from config import settings
from storage.minio import client as minio_client


class CloudRepository:

    def __init__(self):
        self.client = minio_client

    def put_object(
        self,
        data,
        object_name,
        bucket_name=settings.MINIO_BUCKET,
        length=-1,
        part_size=10 * 1024 * 1024,
    ):
        self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=data.file,
            length=length,
            part_size=part_size,
            content_type=data.content_type or "application/octet-stream",
        )


def get_cloud_repository():
    return CloudRepository()
