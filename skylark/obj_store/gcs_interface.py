import mimetypes
import os
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Iterator, List

from google.cloud import storage  # pytype: disable=import-error

from skylark.obj_store.object_store_interface import NoSuchObjectException, ObjectStoreInterface, ObjectStoreObject


class GCSObject(ObjectStoreObject):
    def full_path(self):
        return os.path.join(f"gs://{self.bucket}", self.key)


class GCSInterface(ObjectStoreInterface):
    def __init__(self, gcp_region, bucket_name):
        # TODO: infer region?
        self.gcp_region = gcp_region
        self.bucket_name = bucket_name

        # TODO - figure out how paralllelism handled
        self._gcs_client = storage.Client()

        # TODO: set number of threads
        self.pool = ThreadPoolExecutor(max_workers=4)

    def bucket_exists(self):
        try:
            self._gcs_client.get_bucket(self.bucket_name)
            return True
        except Exception:
            return False

    def create_bucket(self, premium_tier=True):
        if not self.bucket_exists():
            bucket = self._gcs_client.bucket(self.bucket_name)
            bucket.storage_class = "STANDARD"
            self._gcs_client.create_bucket(bucket, location=self.gcp_region)
        assert self.bucket_exists()

    def list_objects(self, prefix="") -> Iterator[GCSObject]:
        blobs = self._gcs_client.list_blobs(self.bucket_name, prefix=prefix)
        # TODO: pagination?
        for blob in blobs:
            # blob = bucket.get_blob(blob_name)
            yield GCSObject("gcs", self.bucket_name, blob.name, blob.size, blob.updated)

    def delete_objects(self, keys: List[str]):
        for key in keys:
            self._gcs_client.bucket(self.bucket_name).blob(key).delete()
            assert not self.exists(key)

    def get_obj_metadata(self, obj_name):
        bucket = self._gcs_client.bucket(self.bucket_name)
        blob = bucket.get_blob(obj_name)
        if blob is None:
            raise NoSuchObjectException(
                f"Object {obj_name} does not exist in bucket {self.bucket_name}, or you do not have permission to access it"
            )
        return blob

    def get_obj_size(self, obj_name):
        return self.get_obj_metadata(obj_name).size

    def exists(self, obj_name):
        try:
            self.get_obj_metadata(obj_name)
            return True
        except NoSuchObjectException:
            return False

    # todo: implement range request for download
    def download_object(self, src_object_name, dst_file_path) -> Future:
        src_object_name, dst_file_path = str(src_object_name), str(dst_file_path)
        src_object_name = src_object_name if src_object_name[0] != "/" else src_object_name

        def _download_object_helper(offset, **kwargs):

            bucket = self._gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(src_object_name)
            chunk = blob.download_as_string()

            # write file
            if not os.path.exists(dst_file_path):
                open(dst_file_path, "a").close()
            with open(dst_file_path, "rb+") as f:
                f.seek(offset)
                f.write(chunk)

        return self.pool.submit(_download_object_helper, 0)

    def upload_object(self, src_file_path, dst_object_name, content_type="infer") -> Future:
        src_file_path, dst_object_name = str(src_file_path), str(dst_object_name)
        dst_object_name = dst_object_name if dst_object_name[0] != "/" else dst_object_name
        os.path.getsize(src_file_path)

        if content_type == "infer":
            content_type = mimetypes.guess_type(src_file_path)[0] or "application/octet-stream"

        def _upload_object_helper():
            bucket = self._gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(dst_object_name)
            blob.upload_from_filename(src_file_path)
            return True

        return self.pool.submit(_upload_object_helper)
