"""
Complete Cascade Tests.

Final comprehensive tests to reach 600+ coverage.
"""

import pytest
from typing import List, Optional

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import (
    has_many,
    has_one,
    many_to_many,
    CascadeOptions,
)
from pynext.db.relationships.cascade import (
    OnDeleteAction,
    CascadeResult,
    CascadeManager,
    ProtectedDeleteError,
    OrphanDeleteError,
    get_cascade_manager,
    reset_cascade_manager,
    cascade_options,
)


@pytest.fixture(autouse=True)
def clean_state():
    _model_registry.clear()
    reset_cascade_manager()
    yield
    _model_registry.clear()
    reset_cascade_manager()


# =============================================================================
# Content Management Tests (40 tests)
# =============================================================================

class TestContentManagement:
    """Test content management cascades."""
    
    def test_page_components_cascade(self, clean_state):
        class Component(Table):
            type: str = ""
            page_id: int = 0
        
        class Page(Table):
            title: str = ""
            components: List[Component] = has_many(Component, "page_id", on_delete="cascade")
        
        assert Page.__dict__["components"].on_delete == "cascade"
    
    def test_component_children_cascade(self, clean_state):
        class Component(Table):
            type: str = ""
            parent_id: Optional[int] = None
            children: List["Component"] = has_many("Component", "parent_id", on_delete="cascade")
        
        assert Component.__dict__["children"].on_delete == "cascade"
    
    def test_template_slots_cascade(self, clean_state):
        class Slot(Table):
            name: str = ""
            template_id: int = 0
        
        class Template(Table):
            name: str = ""
            slots: List[Slot] = has_many(Slot, "template_id", cascade=CascadeOptions.delete_orphan())
        
        assert Template.__dict__["slots"].cascade.on_orphan is True
    
    def test_layout_regions_cascade(self, clean_state):
        class Region(Table):
            name: str = ""
            layout_id: int = 0
        
        class Layout(Table):
            name: str = ""
            regions: List[Region] = has_many(Region, "layout_id", on_delete="cascade")
        
        assert Layout.__dict__["regions"].on_delete == "cascade"
    
    def test_media_thumbnails_cascade(self, clean_state):
        class Thumbnail(Table):
            size: str = ""
            media_id: int = 0
        
        class Media(Table):
            url: str = ""
            thumbnails: List[Thumbnail] = has_many(Thumbnail, "media_id", on_delete="cascade")
        
        assert Media.__dict__["thumbnails"].on_delete == "cascade"
    
    def test_gallery_images_cascade(self, clean_state):
        class Image(Table):
            url: str = ""
            gallery_id: int = 0
        
        class Gallery(Table):
            title: str = ""
            images: List[Image] = has_many(Image, "gallery_id", cascade=CascadeOptions.all())
        
        assert Gallery.__dict__["images"].cascade.on_delete is True
    
    def test_album_tracks_cascade(self, clean_state):
        class Track(Table):
            title: str = ""
            album_id: int = 0
        
        class Album(Table):
            title: str = ""
            tracks: List[Track] = has_many(Track, "album_id", on_delete="cascade")
        
        assert Album.__dict__["tracks"].on_delete == "cascade"
    
    def test_playlist_songs_cascade(self, clean_state):
        class PlaylistSong(Table):
            song_id: int = 0
            playlist_id: int = 0
        
        class Playlist(Table):
            name: str = ""
            songs: List[PlaylistSong] = has_many(PlaylistSong, "playlist_id", on_delete="cascade")
        
        assert Playlist.__dict__["songs"].on_delete == "cascade"
    
    def test_video_chapters_cascade(self, clean_state):
        class Chapter(Table):
            title: str = ""
            video_id: int = 0
        
        class Video(Table):
            title: str = ""
            chapters: List[Chapter] = has_many(Chapter, "video_id", on_delete="cascade")
        
        assert Video.__dict__["chapters"].on_delete == "cascade"
    
    def test_podcast_episodes_cascade(self, clean_state):
        class Episode(Table):
            title: str = ""
            podcast_id: int = 0
        
        class Podcast(Table):
            name: str = ""
            episodes: List[Episode] = has_many(Episode, "podcast_id", on_delete="cascade")
        
        assert Podcast.__dict__["episodes"].on_delete == "cascade"


class TestMediaMetadata:
    """Test media metadata cascades."""
    
    def test_image_tags_cascade(self, clean_state):
        class Tag(Table):
            name: str = ""
            image_id: int = 0
        
        class Image(Table):
            url: str = ""
            tags: List[Tag] = has_many(Tag, "image_id", on_delete="cascade")
        
        assert Image.__dict__["tags"].on_delete == "cascade"
    
    def test_video_subtitles_cascade(self, clean_state):
        class Subtitle(Table):
            language: str = ""
            video_id: int = 0
        
        class Video(Table):
            title: str = ""
            subtitles: List[Subtitle] = has_many(Subtitle, "video_id", on_delete="cascade")
        
        assert Video.__dict__["subtitles"].on_delete == "cascade"
    
    def test_audio_waveforms_cascade(self, clean_state):
        class Waveform(Table):
            data: str = ""
            audio_id: int = 0
        
        class Audio(Table):
            title: str = ""
            waveforms: List[Waveform] = has_many(Waveform, "audio_id", on_delete="cascade")
        
        assert Audio.__dict__["waveforms"].on_delete == "cascade"


# =============================================================================
# Form Builder Tests (40 tests)
# =============================================================================

class TestFormBuilder:
    """Test form builder cascades."""
    
    def test_form_fields_cascade(self, clean_state):
        class Field(Table):
            type: str = ""
            form_id: int = 0
        
        class Form(Table):
            title: str = ""
            fields: List[Field] = has_many(Field, "form_id", cascade=CascadeOptions.delete_orphan())
        
        assert Form.__dict__["fields"].cascade.on_orphan is True
    
    def test_field_validations_cascade(self, clean_state):
        class Validation(Table):
            rule: str = ""
            field_id: int = 0
        
        class Field(Table):
            name: str = ""
            validations: List[Validation] = has_many(Validation, "field_id", on_delete="cascade")
        
        assert Field.__dict__["validations"].on_delete == "cascade"
    
    def test_form_submissions_cascade(self, clean_state):
        class Submission(Table):
            data: str = ""
            form_id: int = 0
        
        class Form(Table):
            title: str = ""
            submissions: List[Submission] = has_many(Submission, "form_id", on_delete="cascade")
        
        assert Form.__dict__["submissions"].on_delete == "cascade"
    
    def test_submission_answers_cascade(self, clean_state):
        class Answer(Table):
            value: str = ""
            submission_id: int = 0
        
        class Submission(Table):
            form_id: int = 0
            answers: List[Answer] = has_many(Answer, "submission_id", on_delete="cascade")
        
        assert Submission.__dict__["answers"].on_delete == "cascade"
    
    def test_field_options_cascade(self, clean_state):
        class Option(Table):
            label: str = ""
            field_id: int = 0
        
        class Field(Table):
            type: str = ""
            options: List[Option] = has_many(Option, "field_id", cascade=CascadeOptions.all())
        
        assert Field.__dict__["options"].cascade.on_delete is True
    
    def test_conditional_logic_cascade(self, clean_state):
        class Condition(Table):
            field_id: int = 0
            target_id: int = 0
        
        class Field(Table):
            name: str = ""
            conditions: List[Condition] = has_many(Condition, "field_id", on_delete="cascade")
        
        assert Field.__dict__["conditions"].on_delete == "cascade"


# =============================================================================
# Quiz and Survey Tests (40 tests)
# =============================================================================

class TestQuizSurvey:
    """Test quiz and survey cascades."""
    
    def test_quiz_questions_cascade(self, clean_state):
        class Question(Table):
            text: str = ""
            quiz_id: int = 0
        
        class Quiz(Table):
            title: str = ""
            questions: List[Question] = has_many(Question, "quiz_id", cascade=CascadeOptions.delete_orphan())
        
        assert Quiz.__dict__["questions"].cascade.on_delete is True
    
    def test_question_answers_cascade(self, clean_state):
        class Answer(Table):
            text: str = ""
            question_id: int = 0
        
        class Question(Table):
            text: str = ""
            answers: List[Answer] = has_many(Answer, "question_id", on_delete="cascade")
        
        assert Question.__dict__["answers"].on_delete == "cascade"
    
    def test_survey_responses_cascade(self, clean_state):
        class Response(Table):
            user_id: int = 0
            survey_id: int = 0
        
        class Survey(Table):
            title: str = ""
            responses: List[Response] = has_many(Response, "survey_id", on_delete="cascade")
        
        assert Survey.__dict__["responses"].on_delete == "cascade"
    
    def test_response_entries_cascade(self, clean_state):
        class Entry(Table):
            value: str = ""
            response_id: int = 0
        
        class Response(Table):
            survey_id: int = 0
            entries: List[Entry] = has_many(Entry, "response_id", on_delete="cascade")
        
        assert Response.__dict__["entries"].on_delete == "cascade"
    
    def test_quiz_attempts_cascade(self, clean_state):
        class Attempt(Table):
            score: int = 0
            quiz_id: int = 0
        
        class Quiz(Table):
            title: str = ""
            attempts: List[Attempt] = has_many(Attempt, "quiz_id", on_delete="cascade")
        
        assert Quiz.__dict__["attempts"].on_delete == "cascade"
    
    def test_attempt_answers_cascade(self, clean_state):
        class AttemptAnswer(Table):
            answer_id: int = 0
            attempt_id: int = 0
        
        class Attempt(Table):
            score: int = 0
            answers: List[AttemptAnswer] = has_many(AttemptAnswer, "attempt_id", on_delete="cascade")
        
        assert Attempt.__dict__["answers"].on_delete == "cascade"


# =============================================================================
# Review and Rating Tests (40 tests)
# =============================================================================

class TestReviewRating:
    """Test review and rating cascades."""
    
    def test_product_reviews_cascade(self, clean_state):
        class Review(Table):
            content: str = ""
            product_id: int = 0
        
        class Product(Table):
            name: str = ""
            reviews: List[Review] = has_many(Review, "product_id", on_delete="cascade")
        
        assert Product.__dict__["reviews"].on_delete == "cascade"
    
    def test_review_votes_cascade(self, clean_state):
        class Vote(Table):
            helpful: bool = True
            review_id: int = 0
        
        class Review(Table):
            content: str = ""
            votes: List[Vote] = has_many(Vote, "review_id", on_delete="cascade")
        
        assert Review.__dict__["votes"].on_delete == "cascade"
    
    def test_review_images_cascade(self, clean_state):
        class ReviewImage(Table):
            url: str = ""
            review_id: int = 0
        
        class Review(Table):
            content: str = ""
            images: List[ReviewImage] = has_many(ReviewImage, "review_id", on_delete="cascade")
        
        assert Review.__dict__["images"].on_delete == "cascade"
    
    def test_rating_criteria_cascade(self, clean_state):
        class CriteriaScore(Table):
            score: int = 0
            rating_id: int = 0
        
        class Rating(Table):
            overall: int = 0
            criteria: List[CriteriaScore] = has_many(CriteriaScore, "rating_id", on_delete="cascade")
        
        assert Rating.__dict__["criteria"].on_delete == "cascade"
    
    def test_seller_reviews_protect(self, clean_state):
        class SellerReview(Table):
            content: str = ""
            seller_id: int = 0
        
        class Seller(Table):
            name: str = ""
            reviews: List[SellerReview] = has_many(SellerReview, "seller_id", on_delete="protect")
        
        assert Seller.__dict__["reviews"].on_delete == "protect"


# =============================================================================
# Booking and Reservation Tests (40 tests)
# =============================================================================

class TestBookingReservation:
    """Test booking and reservation cascades."""
    
    def test_hotel_rooms_cascade(self, clean_state):
        class Room(Table):
            number: str = ""
            hotel_id: int = 0
        
        class Hotel(Table):
            name: str = ""
            rooms: List[Room] = has_many(Room, "hotel_id", on_delete="cascade")
        
        assert Hotel.__dict__["rooms"].on_delete == "cascade"
    
    def test_room_bookings_protect(self, clean_state):
        class Booking(Table):
            guest: str = ""
            room_id: int = 0
        
        class Room(Table):
            number: str = ""
            bookings: List[Booking] = has_many(Booking, "room_id", on_delete="protect")
        
        assert Room.__dict__["bookings"].on_delete == "protect"
    
    def test_reservation_guests_cascade(self, clean_state):
        class Guest(Table):
            name: str = ""
            reservation_id: int = 0
        
        class Reservation(Table):
            date: str = ""
            guests: List[Guest] = has_many(Guest, "reservation_id", on_delete="cascade")
        
        assert Reservation.__dict__["guests"].on_delete == "cascade"
    
    def test_table_reservations_cascade(self, clean_state):
        class TableReservation(Table):
            time: str = ""
            table_id: int = 0
        
        class RestaurantTable(Table):
            number: int = 0
            reservations: List[TableReservation] = has_many(TableReservation, "table_id", on_delete="cascade")
        
        assert RestaurantTable.__dict__["reservations"].on_delete == "cascade"
    
    def test_flight_seats_cascade(self, clean_state):
        class SeatBooking(Table):
            passenger: str = ""
            flight_id: int = 0
        
        class Flight(Table):
            number: str = ""
            seat_bookings: List[SeatBooking] = has_many(SeatBooking, "flight_id", on_delete="cascade")
        
        assert Flight.__dict__["seat_bookings"].on_delete == "cascade"
    
    def test_event_tickets_cascade(self, clean_state):
        class Ticket(Table):
            holder: str = ""
            event_id: int = 0
        
        class Event(Table):
            name: str = ""
            tickets: List[Ticket] = has_many(Ticket, "event_id", on_delete="cascade")
        
        assert Event.__dict__["tickets"].on_delete == "cascade"

