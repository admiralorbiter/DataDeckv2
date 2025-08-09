#!/usr/bin/env python3
"""
Media Service - Business logic for media upload, validation, and management.
Handles both individual media items and project galleries (Data Decks).
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from PIL import Image
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from models import Media, Session, db
from models.media import MediaType


class MediaService:
    """Service for handling media uploads, validation, and management."""

    # Configuration
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_IMAGES_PER_PROJECT = 10
    MIN_IMAGES_PER_PROJECT = 1

    # Image processing
    MAX_IMAGE_DIMENSION = 2048  # Max width/height
    THUMBNAIL_SIZE = (300, 300)

    @staticmethod
    def validate_file(file: FileStorage) -> Tuple[bool, str]:
        """
        Validate uploaded file for type, size, and content.

        Args:
            file: The uploaded file object

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file or not file.filename:
            return False, "No file selected"

        # Check file extension
        if not MediaService._allowed_file(file.filename):
            return (
                False,
                f"Invalid file type. Allowed: "
                f"{', '.join(MediaService.ALLOWED_EXTENSIONS)}",
            )

        # Check file size
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)  # Reset for reading

        if size > MediaService.MAX_FILE_SIZE:
            return (
                False,
                f"File too large. Maximum size: "
                f"{MediaService.MAX_FILE_SIZE // (1024*1024)}MB",
            )

        if size == 0:
            return False, "File is empty"

        # Validate image content
        try:
            with Image.open(file.stream) as img:
                img.verify()  # Verify it's a valid image
            file.stream.seek(0)  # Reset stream after verification
        except Exception:
            return False, "Invalid image file"

        return True, ""

    @staticmethod
    def _allowed_file(filename: str) -> bool:
        """Check if filename has allowed extension."""
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in MediaService.ALLOWED_EXTENSIONS
        )

    @staticmethod
    def generate_filename(original_filename: str, student_id: int) -> str:
        """
        Generate secure, unique filename for uploaded media.

        Args:
            original_filename: Original filename from upload
            student_id: ID of uploading student

        Returns:
            Secure filename with timestamp and UUID
        """
        # Get file extension
        ext = ""
        if "." in original_filename:
            ext = "." + secure_filename(original_filename).rsplit(".", 1)[1].lower()

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        return f"student_{student_id}_{timestamp}_{unique_id}{ext}"

    @staticmethod
    def process_image(file_path: str) -> Dict[str, str]:
        """
        Process uploaded image: resize if needed, create thumbnail.

        Args:
            file_path: Path to the uploaded image

        Returns:
            Dictionary with processed file paths
        """
        processed_paths = {"original": file_path}

        try:
            with Image.open(file_path) as img:
                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Resize if image is too large
                if (
                    img.width > MediaService.MAX_IMAGE_DIMENSION
                    or img.height > MediaService.MAX_IMAGE_DIMENSION
                ):
                    img.thumbnail(
                        (
                            MediaService.MAX_IMAGE_DIMENSION,
                            MediaService.MAX_IMAGE_DIMENSION,
                        ),
                        Image.Resampling.LANCZOS,
                    )
                    img.save(file_path, optimize=True, quality=85)

                # Create thumbnail
                thumb_path = file_path.replace(".", "_thumb.")
                thumb_img = img.copy()
                thumb_img.thumbnail(
                    MediaService.THUMBNAIL_SIZE, Image.Resampling.LANCZOS
                )
                thumb_img.save(thumb_path, optimize=True, quality=80)
                processed_paths["thumbnail"] = thumb_path

        except Exception as e:
            # If processing fails, we still have the original
            print(f"Warning: Image processing failed for {file_path}: {e}")

        return processed_paths

    @staticmethod
    def create_single_media(
        session_id: int,
        student_id: int,
        file: FileStorage,
        title: str = "",
        description: str = "",
        tags: Dict[str, str] = None,
    ) -> Optional[Media]:
        """
        Create a single media item from uploaded file.

        Args:
            session_id: ID of the session
            student_id: ID of the uploading student
            file: The uploaded file
            title: Media title (auto-generated if empty)
            description: Media description
            tags: Dictionary of tags (graph_tag, variable_tag, etc.)

        Returns:
            Created Media object or None if failed
        """
        # Validate file
        is_valid, error = MediaService.validate_file(file)
        if not is_valid:
            raise ValueError(error)

        # Generate filename and save file
        filename = MediaService.generate_filename(file.filename, student_id)
        # Note: In a real implementation, you'd save to a configured upload directory
        # For now, we'll just store the filename

        # Auto-generate title if not provided
        if not title:
            title = MediaService._generate_title_from_tags(tags or {})

        # Create media record
        media = Media(
            session_id=session_id,
            student_id=student_id,
            title=title,
            description=description,
            media_type=MediaType.IMAGE,
            image_file=filename,
            is_graph=tags.get("is_graph", False) if tags else False,
            graph_tag=tags.get("graph_tag") if tags else None,
            variable_tag=tags.get("variable_tag") if tags else None,
        )

        db.session.add(media)
        return media

    @staticmethod
    def create_project_gallery(
        session_id: int,
        student_id: int,
        files: List[FileStorage],
        title: str,
        description: str = "",
        tags: Dict[str, str] = None,
    ) -> Optional[List[Media]]:
        """
        Create a project gallery (Data Deck) with multiple images.

        Args:
            session_id: ID of the session
            student_id: ID of the uploading student
            files: List of uploaded files (1-10 images)
            title: Project title
            description: Project description
            tags: Dictionary of tags

        Returns:
            List of created Media objects or None if failed
        """
        # Validate project constraints
        if len(files) < MediaService.MIN_IMAGES_PER_PROJECT:
            raise ValueError(
                f"Project must have at least "
                f"{MediaService.MIN_IMAGES_PER_PROJECT} image"
            )

        if len(files) > MediaService.MAX_IMAGES_PER_PROJECT:
            raise ValueError(
                f"Project cannot have more than "
                f"{MediaService.MAX_IMAGES_PER_PROJECT} images"
            )

        # Validate all files first
        for i, file in enumerate(files):
            is_valid, error = MediaService.validate_file(file)
            if not is_valid:
                raise ValueError(f"File {i+1}: {error}")

        # Generate project group ID
        project_group = str(uuid.uuid4())

        # Create media records for each file
        media_items = []
        for i, file in enumerate(files):
            filename = MediaService.generate_filename(file.filename, student_id)

            # First image is the primary/cover image
            is_primary = i == 0
            item_title = title if is_primary else f"{title} - Image {i+1}"

            media = Media(
                session_id=session_id,
                student_id=student_id,
                title=item_title,
                description=description if is_primary else "",
                media_type=MediaType.IMAGE,
                image_file=filename,
                is_project=True,
                project_group=project_group,
                is_graph=tags.get("is_graph", False) if tags else False,
                graph_tag=tags.get("graph_tag") if tags else None,
                variable_tag=tags.get("variable_tag") if tags else None,
            )

            db.session.add(media)
            media_items.append(media)

        return media_items

    @staticmethod
    def get_student_media(student_id: int, session_id: int = None) -> List[Media]:
        """
        Get all media uploaded by a specific student.

        Args:
            student_id: ID of the student
            session_id: Optional session filter

        Returns:
            List of Media objects
        """
        query = Media.query.filter_by(student_id=student_id)

        if session_id:
            query = query.filter_by(session_id=session_id)

        return query.order_by(Media.uploaded_at.desc()).all()

    @staticmethod
    def get_session_media(
        session_id: int, include_projects: bool = True
    ) -> List[Media]:
        """
        Get all media in a session.

        Args:
            session_id: ID of the session
            include_projects: Whether to include project gallery items

        Returns:
            List of Media objects
        """
        query = Media.query.filter_by(session_id=session_id)

        if not include_projects:
            query = query.filter_by(is_project=False)

        return query.order_by(Media.uploaded_at.desc()).all()

    @staticmethod
    def get_project_gallery(project_group: str) -> List[Media]:
        """
        Get all images in a project gallery.

        Args:
            project_group: Project group UUID

        Returns:
            List of Media objects in the project
        """
        return (
            Media.query.filter_by(project_group=project_group, is_project=True)
            .order_by(Media.uploaded_at.asc())
            .all()
        )

    @staticmethod
    def delete_media(
        media_id: int, requester_id: int, is_teacher: bool = False
    ) -> bool:
        """
        Delete a media item with ownership checks.

        Args:
            media_id: ID of the media to delete
            requester_id: ID of the user requesting deletion
            is_teacher: Whether the requester is a teacher

        Returns:
            True if deleted successfully, False otherwise
        """
        media = Media.query.get(media_id)
        if not media:
            return False

        # Check permissions
        if is_teacher:
            # Teachers can delete any media in their sessions
            session = Session.query.get(media.session_id)
            if not session or session.created_by_id != requester_id:
                return False
        else:
            # Students can only delete their own media
            if media.student_id != requester_id:
                return False

        # If this is part of a project, delete the entire project
        if media.is_project and media.project_group:
            project_media = MediaService.get_project_gallery(media.project_group)
            for item in project_media:
                db.session.delete(item)
                # TODO: Delete actual files from storage
        else:
            db.session.delete(media)
            # TODO: Delete actual file from storage

        return True

    @staticmethod
    def update_media_tags(
        media_id: int, tags: Dict[str, str], requester_id: int, is_teacher: bool = False
    ) -> bool:
        """
        Update media tags and regenerate title.

        Args:
            media_id: ID of the media to update
            tags: New tags dictionary
            requester_id: ID of the user requesting update
            is_teacher: Whether the requester is a teacher

        Returns:
            True if updated successfully, False otherwise
        """
        media = Media.query.get(media_id)
        if not media:
            return False

        # Check permissions (same as delete)
        if is_teacher:
            session = Session.query.get(media.session_id)
            if not session or session.created_by_id != requester_id:
                return False
        else:
            if media.student_id != requester_id:
                return False

        # Update tags
        media.graph_tag = tags.get("graph_tag")
        media.variable_tag = tags.get("variable_tag")
        media.is_graph = tags.get("is_graph", False)

        # Regenerate title
        if not media.is_project:  # Don't auto-update project titles
            media.title = MediaService._generate_title_from_tags(tags)

        return True

    @staticmethod
    def _generate_title_from_tags(tags: Dict[str, str]) -> str:
        """Generate a title from media tags."""
        parts = []

        if tags.get("graph_tag"):
            parts.append(tags["graph_tag"].title())

        if tags.get("variable_tag"):
            parts.append(f"showing {tags['variable_tag']}")

        if tags.get("is_graph"):
            parts.append("Graph")

        if parts:
            return " ".join(parts)

        return f"Data Visualization - {datetime.now().strftime('%Y-%m-%d')}"

    @staticmethod
    def get_upload_stats(student_id: int) -> Dict[str, int]:
        """
        Get upload statistics for a student.

        Args:
            student_id: ID of the student

        Returns:
            Dictionary with upload statistics
        """
        total_uploads = Media.query.filter_by(student_id=student_id).count()
        project_count = (
            Media.query.filter_by(student_id=student_id, is_project=True)
            .distinct(Media.project_group)
            .count()
        )

        single_uploads = (
            total_uploads
            - Media.query.filter_by(student_id=student_id, is_project=True).count()
        )

        return {
            "total_uploads": total_uploads,
            "single_uploads": single_uploads,
            "projects": project_count,
            "total_reactions_received": Media.query.filter_by(student_id=student_id)
            .with_entities(
                db.func.sum(Media.graph_likes + Media.eye_likes + Media.read_likes)
            )
            .scalar()
            or 0,
        }
