import cloudinary
import cloudinary.uploader
import cloudinary.utils
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from whitenoise.storage import CompressedStaticFilesStorage


@deconstructible
class CloudinaryMediaStorage(Storage):
    """Media file storage using Cloudinary — works with Django 5+."""

    def _save(self, name, content):
        name = name.replace('\\', '/')
        cloudinary.uploader.upload(
            content,
            public_id=name.rsplit('.', 1)[0],
            resource_type='auto',
            overwrite=True,
        )
        return name

    def url(self, name):
        name = name.replace('\\', '/')
        url, _ = cloudinary.utils.cloudinary_url(name, resource_type='image')
        return url

    def exists(self, name):
        return False

    def delete(self, name):
        public_id = name.rsplit('.', 1)[0].replace('\\', '/')
        try:
            cloudinary.uploader.destroy(public_id)
        except Exception:
            pass

    def _open(self, name, mode='rb'):
        from io import BytesIO
        import urllib.request
        response = urllib.request.urlopen(self.url(name))
        return BytesIO(response.read())

    def size(self, name):
        return 0


class StaticStorage(CompressedStaticFilesStorage):
    pass
