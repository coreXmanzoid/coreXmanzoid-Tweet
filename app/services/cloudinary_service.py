from app.cloudinary.cloudinary_config import configure_cloudinary
import cloudinary.uploader


class CloudinaryService:

    @staticmethod
    def upload_profile_picture(file, user_id):
        configure_cloudinary()

        result = cloudinary.uploader.upload(
            file,
            folder="profile_pictures",
            public_id=f"user_{user_id}",
            overwrite=True,
            transformation=[
                {"width": 256, "height": 256, "crop": "fill"},
                {"quality": "auto"},
                {"fetch_format": "auto"},
            ],
        )

        return result["secure_url"]
