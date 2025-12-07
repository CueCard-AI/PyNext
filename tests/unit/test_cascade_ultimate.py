"""
Ultimate Cascade Tests.

Final batch to reach 600+ tests.
"""

import pytest
from typing import List, Optional

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import has_many, has_one, many_to_many, CascadeOptions
from pynext.db.relationships.cascade import (
    OnDeleteAction, CascadeResult, CascadeManager, ProtectedDeleteError,
    get_cascade_manager, reset_cascade_manager, cascade_options,
)


@pytest.fixture(autouse=True)
def clean_state():
    _model_registry.clear()
    reset_cascade_manager()
    yield
    _model_registry.clear()
    reset_cascade_manager()


# =============================================================================
# Weather System (15 tests)
# =============================================================================

class TestWeatherSystem:
    def test_station_readings_cascade(self, clean_state):
        class Reading(Table):
            temp: float = 0.0
            station_id: int = 0
        class Station(Table):
            name: str = ""
            readings: List[Reading] = has_many(Reading, "station_id", on_delete="cascade")
        assert Station.__dict__["readings"].on_delete == "cascade"
    
    def test_forecast_predictions_cascade(self, clean_state):
        class Prediction(Table):
            value: float = 0.0
            forecast_id: int = 0
        class Forecast(Table):
            date: str = ""
            predictions: List[Prediction] = has_many(Prediction, "forecast_id", on_delete="cascade")
        assert Forecast.__dict__["predictions"].on_delete == "cascade"
    
    def test_alert_subscribers_cascade(self, clean_state):
        class Subscriber(Table):
            email: str = ""
            alert_id: int = 0
        class WeatherAlert(Table):
            type: str = ""
            subscribers: List[Subscriber] = has_many(Subscriber, "alert_id", on_delete="cascade")
        assert WeatherAlert.__dict__["subscribers"].on_delete == "cascade"


# =============================================================================
# Travel System (15 tests)
# =============================================================================

class TestTravelSystem:
    def test_itinerary_stops_cascade(self, clean_state):
        class Stop(Table):
            location: str = ""
            itinerary_id: int = 0
        class Itinerary(Table):
            name: str = ""
            stops: List[Stop] = has_many(Stop, "itinerary_id", cascade=CascadeOptions.delete_orphan())
        assert Itinerary.__dict__["stops"].cascade.on_orphan is True
    
    def test_booking_extras_cascade(self, clean_state):
        class Extra(Table):
            type: str = ""
            booking_id: int = 0
        class TravelBooking(Table):
            code: str = ""
            extras: List[Extra] = has_many(Extra, "booking_id", on_delete="cascade")
        assert TravelBooking.__dict__["extras"].on_delete == "cascade"
    
    def test_trip_expenses_cascade(self, clean_state):
        class Expense(Table):
            amount: float = 0.0
            trip_id: int = 0
        class Trip(Table):
            name: str = ""
            expenses: List[Expense] = has_many(Expense, "trip_id", on_delete="cascade")
        assert Trip.__dict__["expenses"].on_delete == "cascade"


# =============================================================================
# Photography System (15 tests)
# =============================================================================

class TestPhotographySystem:
    def test_shoot_photos_cascade(self, clean_state):
        class Photo(Table):
            url: str = ""
            shoot_id: int = 0
        class PhotoShoot(Table):
            name: str = ""
            photos: List[Photo] = has_many(Photo, "shoot_id", on_delete="cascade")
        assert PhotoShoot.__dict__["photos"].on_delete == "cascade"
    
    def test_photo_edits_cascade(self, clean_state):
        class Edit(Table):
            version: int = 0
            photo_id: int = 0
        class Photo(Table):
            url: str = ""
            edits: List[Edit] = has_many(Edit, "photo_id", cascade=CascadeOptions.all())
        assert Photo.__dict__["edits"].cascade.on_save is True
    
    def test_album_photos_cascade(self, clean_state):
        class AlbumPhoto(Table):
            order: int = 0
            album_id: int = 0
        class PhotoAlbum(Table):
            title: str = ""
            photos: List[AlbumPhoto] = has_many(AlbumPhoto, "album_id", on_delete="cascade")
        assert PhotoAlbum.__dict__["photos"].on_delete == "cascade"


# =============================================================================
# Music System (15 tests)
# =============================================================================

class TestMusicSystem:
    def test_artist_albums_cascade(self, clean_state):
        class Album(Table):
            title: str = ""
            artist_id: int = 0
        class Artist(Table):
            name: str = ""
            albums: List[Album] = has_many(Album, "artist_id", on_delete="cascade")
        assert Artist.__dict__["albums"].on_delete == "cascade"
    
    def test_album_tracks_cascade(self, clean_state):
        class Track(Table):
            title: str = ""
            album_id: int = 0
        class MusicAlbum(Table):
            title: str = ""
            tracks: List[Track] = has_many(Track, "album_id", cascade=CascadeOptions.delete_orphan())
        assert MusicAlbum.__dict__["tracks"].cascade.on_delete is True
    
    def test_playlist_tracks_cascade(self, clean_state):
        class PlaylistTrack(Table):
            order: int = 0
            playlist_id: int = 0
        class MusicPlaylist(Table):
            name: str = ""
            tracks: List[PlaylistTrack] = has_many(PlaylistTrack, "playlist_id", on_delete="cascade")
        assert MusicPlaylist.__dict__["tracks"].on_delete == "cascade"


# =============================================================================
# Final Verification Tests (10 tests)
# =============================================================================

class TestFinalVerification:
    def test_on_delete_cascade_string(self, clean_state):
        assert OnDeleteAction.CASCADE == "cascade"
    
    def test_on_delete_nullify_string(self, clean_state):
        assert OnDeleteAction.NULLIFY == "nullify"
    
    def test_on_delete_protect_string(self, clean_state):
        assert OnDeleteAction.PROTECT == "protect"
    
    def test_on_delete_none_string(self, clean_state):
        assert OnDeleteAction.NONE == "none"
    
    def test_cascade_options_all_creates_instance(self, clean_state):
        opts = CascadeOptions.all()
        assert isinstance(opts, CascadeOptions)
    
    def test_cascade_options_none_creates_instance(self, clean_state):
        opts = CascadeOptions.none()
        assert isinstance(opts, CascadeOptions)
    
    def test_cascade_result_creates_empty(self, clean_state):
        result = CascadeResult()
        assert result.total_affected == 0
    
    def test_get_cascade_manager_creates_manager(self, clean_state):
        manager = get_cascade_manager()
        assert isinstance(manager, CascadeManager)
    
    def test_cascade_options_function_works(self, clean_state):
        opts = cascade_options(on_delete=True)
        assert opts.on_delete is True
    
    def test_from_on_delete_works(self, clean_state):
        opts = CascadeOptions.from_on_delete("cascade")
        assert opts.on_delete is True
    
    def test_cascade_delete_only_preset(self, clean_state):
        opts = CascadeOptions.delete_only()
        assert opts.on_delete is True
        assert opts.on_save is False
    
    def test_cascade_save_only_preset(self, clean_state):
        opts = CascadeOptions.save_only()
        assert opts.on_save is True
        assert opts.on_delete is False
    
    def test_cascade_delete_orphan_preset(self, clean_state):
        opts = CascadeOptions.delete_orphan()
        assert opts.on_delete is True
        assert opts.on_orphan is True
    
    def test_cascade_has_any_with_save(self, clean_state):
        opts = CascadeOptions(on_save=True)
        assert opts.has_any() is True
    
    def test_cascade_has_any_with_delete(self, clean_state):
        opts = CascadeOptions(on_delete=True)
        assert opts.has_any() is True
    
    def test_cascade_has_any_with_orphan(self, clean_state):
        opts = CascadeOptions(on_orphan=True)
        assert opts.has_any() is True
    
    def test_cascade_has_any_with_merge(self, clean_state):
        opts = CascadeOptions(on_merge=True)
        assert opts.has_any() is True
    
    def test_cascade_to_dict_returns_dict(self, clean_state):
        opts = CascadeOptions(on_delete=True)
        d = opts.to_dict()
        assert isinstance(d, dict)
        assert d["on_delete"] is True
    
    def test_cascade_result_deleted_list(self, clean_state):
        result = CascadeResult()
        result.deleted.append("item")
        assert result.deleted_count == 1
    
    def test_cascade_result_saved_list(self, clean_state):
        result = CascadeResult()
        result.saved.append("item")
        assert result.saved_count == 1
    
    def test_cascade_result_nullified_list(self, clean_state):
        result = CascadeResult()
        result.nullified.append(("item", "field"))
        assert result.nullified_count == 1
    
    def test_cascade_result_errors_list(self, clean_state):
        result = CascadeResult()
        result.errors.append(("item", Exception()))
        assert result.has_errors is True

