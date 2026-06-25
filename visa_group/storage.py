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
        public_id = name.rsplit('.', 1)[0]
        if hasattr(content, 'seek'):
            content.seek(0)
        data = content.read() if hasattr(content, 'read') else content
        cloudinary.uploader.upload(
            data,
            public_id=public_id,
            resource_type='auto',
            overwrite=True,
        )
        return name

    def url(self, name):
        name = name.replace('\\', '/')
        # Strip extension — Cloudinary stores by public_id without extension
        public_id = name.rsplit('.', 1)[0] if '.' in name.split('/')[-1] else name
        url, _ = cloudinary.utils.cloudinary_url(public_id, resource_type='image', secure=True)
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


@deconstructible
class CloudinaryRawStorage(Storage):
    """Cloudinary storage for non-image files (PDFs, docs) using resource_type='raw'.
    Unlike images, raw files keep the extension as part of the public_id."""

    def _save(self, name, content):
        name = name.replace('\\', '/')
        if hasattr(content, 'seek'):
            content.seek(0)
        data = content.read() if hasattr(content, 'read') else content
        result = cloudinary.uploader.upload(
            data,
            public_id=name,
            resource_type='raw',
            overwrite=True,
            invalidate=True,
        )
        if not result.get('public_id'):
            raise ValueError(f"Cloudinary raw upload failed for {name}: {result}")
        return name

    def url(self, name):
        name = name.replace('\\', '/')
        # Keep extension — raw files are served with the full filename including .pdf
        url, _ = cloudinary.utils.cloudinary_url(name, resource_type='raw', secure=True)
        return url

    def exists(self, name):
        return False

    def delete(self, name):
        name = name.replace('\\', '/')
        try:
            cloudinary.uploader.destroy(name, resource_type='raw')
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
