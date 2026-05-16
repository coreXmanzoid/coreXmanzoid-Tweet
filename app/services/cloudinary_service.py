from app.cloudinary.cloudinary_config import configure_cloudinary
import cloudinary.uploader


class CloudinaryService:

    @staticmethod
    def upload_profile_picture(file, user_id, resolution="256x256"):
        configure_cloudinary()
        try:
            width, height = [int(value) for value in str(resolution).lower().split("x", 1)]
        except (TypeError, ValueError):
            width, height = 256, 256

        result = cloudinary.uploader.upload(
            file,
            folder="profile_pictures",
            public_id=f"user_{user_id}",
            overwrite=True,
            transformation=[
                {"width": width, "height": height, "crop": "fill"},
                {"quality": "auto"},
                {"fetch_format": "auto"},
            ],
        )

        return result["secure_url"]
