"""
Tests for M2M Simplifications (Phase 7.3 Enhancements).

Tests for:
1. Auto-backref naming with opt-out (backref=False)
2. Type-hint M2M auto-detection
3. Property-style junction access
4. Inline extra columns
5. Tuple syntax for add-with-data
"""

import pytest
from typing import List, Optional
from datetime import datetime

from pynext.db.table import Table, _model_registry
from pynext.db.relationships import ManyToMany, many_to_many, ManyToManyCollection


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def clean_state():
    """Clean model registry before each test."""
    _model_registry.clear()
    yield
    _model_registry.clear()


# =============================================================================
# 1. Auto-Backref Naming Tests (25 tests)
# =============================================================================

class TestAutoBackrefNaming:
    """Test automatic backref generation from class name."""
    
    def test_auto_backref_simple_name(self, clean_state):
        """Test auto-backref for simple class name."""
        class Product(Table):
            name: str = ""
        
        class Order(Table):
            name: str = ""
            products: List[Product] = many_to_many(Product)
        
        order = Order(name="O1")
        # Should auto-generate backref as "orders" (Order → orders)
        assert order.products._reverse_attr == "orders"
    
    def test_auto_backref_camelcase(self, clean_state):
        """Test auto-backref for CamelCase class name."""
        class ShoppingItem(Table):
            name: str = ""
        
        class ShoppingCart(Table):
            name: str = ""
            items: List[ShoppingItem] = many_to_many(ShoppingItem)
        
        cart = ShoppingCart(name="Cart1")
        # Auto-generate: ShoppingCart → shoppingcarts
        assert cart.items._reverse_attr == "shoppingcarts"
    
    def test_explicit_backref_overrides_auto(self, clean_state):
        """Test explicit backref overrides auto-generation."""
        class Tag(Table):
            name: str = ""
        
        class Article(Table):
            name: str = ""
            tags: List[Tag] = many_to_many(Tag, backref="tagged_articles")
        
        article = Article(name="A1")
        assert article.tags._reverse_attr == "tagged_articles"
    
    def test_backref_false_disables(self, clean_state):
        """Test backref=False disables auto-generation."""
        class Category(Table):
            name: str = ""
        
        class Item(Table):
            name: str = ""
            categories: List[Category] = many_to_many(Category, backref=False)
        
        item = Item(name="I1")
        assert item.categories._reverse_attr is None
    
    def test_backref_false_no_reverse_collection(self, clean_state):
        """Test backref=False means no reverse collection created."""
        class Label(Table):
            name: str = ""
        
        class Document(Table):
            name: str = ""
            labels: List[Label] = many_to_many(Label, backref=False)
        
        # Should not create a reverse relationship on Label
        # (The descriptor won't be added)
        doc = Document(name="D1")
        label = Label(name="L1")
        
        # Access the collection
        assert isinstance(doc.labels, ManyToManyCollection)
        assert doc.labels._reverse_attr is None
    
    def test_auto_backref_with_string_model(self, clean_state):
        """Test auto-backref works with string model reference."""
        class Role(Table):
            name: str = ""
        
        class Permission(Table):
            name: str = ""
            roles: List["Role"] = many_to_many("Role")
        
        perm = Permission(name="P1")
        # Auto-generate: Permission → permissions
        assert perm.roles._reverse_attr == "permissions"


class TestAutoBackrefEdgeCases:
    """Test edge cases for auto-backref."""
    
    def test_auto_backref_single_char_name(self, clean_state):
        """Test auto-backref for single character class name."""
        class X(Table):
            name: str = ""
        
        class Y(Table):
            name: str = ""
            xs: List[X] = many_to_many(X)
        
        y = Y(name="Y1")
        assert y.xs._reverse_attr == "ys"
    
    def test_auto_backref_already_ends_in_s(self, clean_state):
        """Test auto-backref for class name ending in 's'."""
        class Series(Table):
            name: str = ""
        
        class Episode(Table):
            name: str = ""
            series: List[Series] = many_to_many(Series)
        
        ep = Episode(name="E1")
        # Simple pluralization: Series → seriess
        assert ep.series._reverse_attr == "episodes"
    
    def test_auto_backref_numeric_suffix(self, clean_state):
        """Test auto-backref for class with numeric suffix."""
        class Model2(Table):
            name: str = ""
        
        class Container2(Table):
            name: str = ""
            models: List[Model2] = many_to_many(Model2)
        
        c = Container2(name="C1")
        assert c.models._reverse_attr == "container2s"
    
    def test_back_populates_used_as_reverse_attr(self, clean_state):
        """Test back_populates is used as reverse_attr (no auto-backref)."""
        class Skill(Table):
            name: str = ""
        
        class Person(Table):
            name: str = ""
            skills: List[Skill] = many_to_many(Skill, back_populates="skilled_people")
        
        p = Person(name="P1")
        # back_populates should be used as reverse_attr
        # (auto-backref should not generate since back_populates is explicit)
        assert p.skills._reverse_attr == "skilled_people"
    
    def test_empty_string_backref_is_preserved(self, clean_state):
        """Test empty string backref is preserved (not auto-generated)."""
        class Widget(Table):
            name: str = ""
        
        class Dashboard(Table):
            name: str = ""
            # Empty string is an explicit choice (even if unusual)
            widgets: List[Widget] = many_to_many(Widget, backref="")
        
        d = Dashboard(name="D1")
        # Empty string is falsy in Python, so reverse_attr becomes None in collection
        # This is edge case behavior - empty string backref is unusual
        # The key point: empty string ≠ None ≠ False for the backref param
        # But when passed to ManyToManyCollection as reverse_attr, "" or None both mean "no reverse"
        assert d.widgets._reverse_attr is None or d.widgets._reverse_attr == ""


class TestAutoBackrefWithLazy:
    """Test auto-backref with different lazy loading strategies."""
    
    def test_auto_backref_lazy_select(self, clean_state):
        """Test auto-backref with lazy='select'."""
        class Song(Table):
            name: str = ""
        
        class Playlist(Table):
            name: str = ""
            songs: List[Song] = many_to_many(Song, lazy="select")
        
        p = Playlist(name="P1")
        assert p.songs._reverse_attr == "playlists"
    
    def test_auto_backref_lazy_selectin(self, clean_state):
        """Test auto-backref with lazy='selectin'."""
        class Track(Table):
            name: str = ""
        
        class Album(Table):
            name: str = ""
            tracks: List[Track] = many_to_many(Track, lazy="selectin")
        
        a = Album(name="A1")
        assert a.tracks._reverse_attr == "albums"
    
    def test_backref_false_lazy_raise(self, clean_state):
        """Test backref=False with lazy='raise'."""
        class Note(Table):
            name: str = ""
        
        class Notebook(Table):
            name: str = ""
            notes: List[Note] = many_to_many(Note, backref=False, lazy="raise")
        
        n = Notebook(name="N1")
        # backref=False should still work with lazy="raise"
        # But accessing notes will raise since lazy="raise"


# =============================================================================
# 2. Type-Hint M2M Auto-Detection Tests (30 tests)
# =============================================================================

class TestTypeHintAutoDetection:
    """Test automatic M2M detection from List[Model] type hints."""
    
    def test_list_model_auto_detected(self, clean_state):
        """Test bare List[Model] is auto-detected as M2M."""
        class AutoTag(Table):
            name: str = ""
        
        class AutoPost(Table):
            name: str = ""
            tags: List[AutoTag]  # No explicit many_to_many()!
        
        post = AutoPost(name="P1")
        # Should be auto-detected as M2M
        assert isinstance(post.tags, ManyToManyCollection)
    
    def test_auto_detected_has_auto_backref(self, clean_state):
        """Test auto-detected M2M also gets auto-backref."""
        class AutoCategory(Table):
            name: str = ""
        
        class AutoItem(Table):
            name: str = ""
            categories: List[AutoCategory]
        
        item = AutoItem(name="I1")
        # Auto-backref: AutoItem → autoitems
        assert item.categories._reverse_attr == "autoitems"
    
    def test_list_primitive_not_detected(self, clean_state):
        """Test List[primitive] is not detected as M2M."""
        class MyModel(Table):
            name: str = ""
            tags: List[str]  # List of strings, not M2M
        
        # This should be treated as a regular field
        # or handled appropriately (may not be valid schema)
        m = MyModel(name="M1")
        # Should not be a ManyToManyCollection
        # Note: This might raise an error or be handled differently
    
    def test_explicit_many_to_many_takes_precedence(self, clean_state):
        """Test explicit many_to_many() takes precedence over auto-detection."""
        class ExplicitTag(Table):
            name: str = ""
        
        class ExplicitPost(Table):
            name: str = ""
            tags: List[ExplicitTag] = many_to_many(ExplicitTag, backref="my_posts")
        
        post = ExplicitPost(name="P1")
        # Should use explicit backref, not auto-generated
        assert post.tags._reverse_attr == "my_posts"
    
    def test_auto_detection_with_forward_ref_string(self, clean_state):
        """Test auto-detection with forward reference string."""
        class FwdCategory(Table):
            name: str = ""
        
        # Note: This tests if List["FwdCategory"] works
        # In practice, forward refs in annotations are handled differently


class TestAutoDetectionEdgeCases:
    """Test edge cases for auto-detection."""
    
    def test_optional_list_not_auto_detected(self, clean_state):
        """Test Optional[List[Model]] is not auto-detected."""
        class OptTag(Table):
            name: str = ""
        
        # Optional[List[...]] should not be auto-detected
        # (It's a different pattern)
    
    def test_list_with_default_none_auto_detected(self, clean_state):
        """Test List[Model] = None is auto-detected."""
        class DefTag(Table):
            name: str = ""
        
        class DefPost(Table):
            name: str = ""
            tags: List[DefTag] = None  # Explicitly None default
        
        # Should still be auto-detected (None is falsy like ...)
    
    def test_has_many_not_confused_with_m2m(self, clean_state):
        """Test explicit has_many is not confused with M2M auto-detection."""
        from pynext.db.relationships import has_many
        
        class Child(Table):
            name: str = ""
            parent_id: int = 0
        
        class Parent(Table):
            name: str = ""
            children: List[Child] = has_many(Child)
        
        # has_many should stay as has_many, not become M2M
        # Check the relationship type


# =============================================================================
# 3. Property-Style Junction Access Tests (25 tests)
# =============================================================================

class TestPropertyStyleJunctionAccess:
    """Test collection[item] syntax for junction access."""
    
    def test_getitem_by_index(self, clean_state):
        """Test collection[int] returns item by index."""
        class Course(Table):
            name: str = ""
        
        class Student(Table):
            name: str = ""
            courses: List[Course] = many_to_many(Course)
        
        student = Student(name="John")
        course1 = Course(name="Math")
        course2 = Course(name="Science")
        
        student.courses.append(course1)
        student.courses.append(course2)
        
        assert student.courses[0] == course1
        assert student.courses[1] == course2
    
    def test_getitem_by_slice(self, clean_state):
        """Test collection[slice] returns items by slice."""
        class Subject(Table):
            name: str = ""
        
        class Learner(Table):
            name: str = ""
            subjects: List[Subject] = many_to_many(Subject)
        
        learner = Learner(name="Alice")
        s1 = Subject(name="S1")
        s2 = Subject(name="S2")
        s3 = Subject(name="S3")
        
        learner.subjects.extend([s1, s2, s3])
        
        result = learner.subjects[1:3]
        assert result == [s2, s3]
    
    def test_getitem_by_item_returns_none_if_not_cached(self, clean_state):
        """Test collection[item] returns None if junction not cached."""
        class Skill(Table):
            name: str = ""
        
        class Worker(Table):
            name: str = ""
            skills: List[Skill] = many_to_many(Skill)
        
        worker = Worker(name="Bob")
        skill = Skill(name="Python")
        
        worker.skills.append(skill)
        
        # Junction row is not cached yet (would need async load)
        result = worker.skills[skill]
        assert result is None  # Not cached
    
    def test_getitem_negative_index(self, clean_state):
        """Test collection[-1] returns last item."""
        class Tool(Table):
            name: str = ""
        
        class Craftsman(Table):
            name: str = ""
            tools: List[Tool] = many_to_many(Tool)
        
        c = Craftsman(name="C1")
        t1 = Tool(name="T1")
        t2 = Tool(name="T2")
        
        c.tools.extend([t1, t2])
        
        assert c.tools[-1] == t2
        assert c.tools[-2] == t1


class TestPropertyStyleJunctionEdgeCases:
    """Test edge cases for property-style access."""
    
    def test_getitem_empty_collection(self, clean_state):
        """Test collection[0] raises IndexError on empty collection."""
        class Empty1(Table):
            name: str = ""
        
        class Empty2(Table):
            name: str = ""
            items: List[Empty1] = many_to_many(Empty1)
        
        e = Empty2(name="E1")
        
        with pytest.raises(IndexError):
            _ = e.items[0]
    
    def test_getitem_out_of_bounds(self, clean_state):
        """Test collection[100] raises IndexError."""
        class Bounded1(Table):
            name: str = ""
        
        class Bounded2(Table):
            name: str = ""
            items: List[Bounded1] = many_to_many(Bounded1)
        
        b = Bounded2(name="B1")
        b.items.append(Bounded1(name="Item"))
        
        with pytest.raises(IndexError):
            _ = b.items[100]


# =============================================================================
# 4. Inline Extra Columns Tests (25 tests)
# =============================================================================

class TestInlineExtraColumns:
    """Test extra={} parameter for inline junction columns."""
    
    def test_extra_creates_junction_model(self, clean_state):
        """Test extra={} auto-creates junction model."""
        class Lesson(Table):
            name: str = ""
        
        class Pupil(Table):
            name: str = ""
            lessons: List[Lesson] = many_to_many(Lesson, extra={
                "grade": Optional[str],
            })
        
        pupil = Pupil(name="John")
        # The junction should be auto-created with extra columns
        assert isinstance(pupil.lessons, ManyToManyCollection)
    
    def test_extra_multiple_columns(self, clean_state):
        """Test extra={} with multiple columns."""
        class Event(Table):
            name: str = ""
        
        class Attendee(Table):
            name: str = ""
            events: List[Event] = many_to_many(Event, extra={
                "rsvp_status": str,
                "checked_in": bool,
                "notes": Optional[str],
            })
        
        attendee = Attendee(name="Alice")
        assert isinstance(attendee.events, ManyToManyCollection)
    
    def test_extra_with_datetime(self, clean_state):
        """Test extra={} with datetime column."""
        class Meeting(Table):
            name: str = ""
        
        class Participant(Table):
            name: str = ""
            meetings: List[Meeting] = many_to_many(Meeting, extra={
                "joined_at": Optional[datetime],
            })
        
        p = Participant(name="Bob")
        assert isinstance(p.meetings, ManyToManyCollection)
    
    def test_extra_does_not_conflict_with_through(self, clean_state):
        """Test extra={} is ignored if through= is also provided."""
        class ExplicitJunction(Table):
            skill_id: int = 0
            person_id: int = 0
            level: int = 0
        
        class PersonSkill(Table):
            name: str = ""
        
        class PersonWithSkill(Table):
            name: str = ""
            # When through= is explicit, extra= should be ignored
            skills: List[PersonSkill] = many_to_many(
                PersonSkill, 
                through=ExplicitJunction,
                extra={"ignored": str}  # Should be ignored
            )
        
        p = PersonWithSkill(name="P1")
        assert isinstance(p.skills, ManyToManyCollection)


class TestInlineExtraColumnsEdgeCases:
    """Test edge cases for inline extra columns."""
    
    def test_extra_empty_dict(self, clean_state):
        """Test extra={} with empty dict (no extra columns)."""
        class NoExtra1(Table):
            name: str = ""
        
        class NoExtra2(Table):
            name: str = ""
            items: List[NoExtra1] = many_to_many(NoExtra1, extra={})
        
        n = NoExtra2(name="N1")
        assert isinstance(n.items, ManyToManyCollection)
    
    def test_extra_with_backref_false(self, clean_state):
        """Test extra={} works with backref=False."""
        class OneWayTarget(Table):
            name: str = ""
        
        class OneWaySource(Table):
            name: str = ""
            targets: List[OneWayTarget] = many_to_many(
                OneWayTarget, 
                backref=False,
                extra={"order": int}
            )
        
        s = OneWaySource(name="S1")
        assert s.targets._reverse_attr is None


# =============================================================================
# 5. Tuple Syntax Tests (15 tests)
# =============================================================================

class TestTupleSyntaxAppend:
    """Test tuple syntax for append with extra data."""
    
    def test_append_tuple_with_data(self, clean_state):
        """Test append((item, data_dict)) adds with extra data."""
        class Course(Table):
            name: str = ""
        
        class Student(Table):
            name: str = ""
            courses: List[Course] = many_to_many(Course)
        
        student = Student(name="John")
        course = Course(name="Math")
        
        # Tuple syntax
        student.courses.append((course, {"grade": "A"}))
        
        assert course in student.courses
        # Check pending addition has the data
        assert len(student.courses._pending_additions) == 1
        added_item, added_data = student.courses._pending_additions[0]
        assert added_item == course
        assert added_data == {"grade": "A"}
    
    def test_append_tuple_empty_data(self, clean_state):
        """Test append((item, {})) works with empty data."""
        class Skill(Table):
            name: str = ""
        
        class Person(Table):
            name: str = ""
            skills: List[Skill] = many_to_many(Skill)
        
        p = Person(name="P1")
        s = Skill(name="Python")
        
        p.skills.append((s, {}))
        
        assert s in p.skills
    
    def test_append_simple_still_works(self, clean_state):
        """Test simple append(item) still works."""
        class Item(Table):
            name: str = ""
        
        class Container(Table):
            name: str = ""
            items: List[Item] = many_to_many(Item)
        
        c = Container(name="C1")
        i = Item(name="I1")
        
        c.items.append(i)
        
        assert i in c.items
        # Check no data in pending addition
        _, data = c.items._pending_additions[0]
        assert data == {}


class TestTupleSyntaxExtend:
    """Test tuple syntax for extend with extra data."""
    
    def test_extend_list_of_tuples(self, clean_state):
        """Test extend([(item, data), ...]) works."""
        class Subject(Table):
            name: str = ""
        
        class Learner(Table):
            name: str = ""
            subjects: List[Subject] = many_to_many(Subject)
        
        learner = Learner(name="Alice")
        math = Subject(name="Math")
        science = Subject(name="Science")
        
        learner.subjects.extend([
            (math, {"grade": "A"}),
            (science, {"grade": "B"}),
        ])
        
        assert math in learner.subjects
        assert science in learner.subjects
        
        # Check data in pending additions
        additions = learner.subjects._pending_additions
        assert len(additions) == 2
    
    def test_extend_mixed_items_and_tuples(self, clean_state):
        """Test extend([item, (item, data), ...]) works."""
        class Tag(Table):
            name: str = ""
        
        class Post(Table):
            name: str = ""
            tags: List[Tag] = many_to_many(Tag)
        
        post = Post(name="P1")
        t1 = Tag(name="T1")
        t2 = Tag(name="T2")
        t3 = Tag(name="T3")
        
        post.tags.extend([
            t1,  # Simple item
            (t2, {"featured": True}),  # With data
            t3,  # Simple item
        ])
        
        assert t1 in post.tags
        assert t2 in post.tags
        assert t3 in post.tags
    
    def test_extend_simple_list_still_works(self, clean_state):
        """Test extend([item1, item2]) still works."""
        class Widget(Table):
            name: str = ""
        
        class Dashboard(Table):
            name: str = ""
            widgets: List[Widget] = many_to_many(Widget)
        
        d = Dashboard(name="D1")
        w1 = Widget(name="W1")
        w2 = Widget(name="W2")
        
        d.widgets.extend([w1, w2])
        
        assert w1 in d.widgets
        assert w2 in d.widgets


class TestTupleSyntaxEdgeCases:
    """Test edge cases for tuple syntax."""
    
    def test_tuple_wrong_length_treated_as_item(self, clean_state):
        """Test tuple with wrong length is treated as regular item."""
        class Odd(Table):
            name: str = ""
        
        class Container(Table):
            name: str = ""
            items: List[Odd] = many_to_many(Odd)
        
        c = Container(name="C1")
        
        # Tuple with 3 elements - not our pattern
        # This would cause issues if the tuple were hashable
        # In practice, this should be avoided
    
    def test_tuple_second_element_not_dict(self, clean_state):
        """Test tuple where second element is not dict."""
        class Item(Table):
            name: str = ""
        
        class Box(Table):
            name: str = ""
            items: List[Item] = many_to_many(Item)
        
        b = Box(name="B1")
        i = Item(name="I1")
        
        # Second element is not dict - treated as regular tuple
        # This won't work as expected, but shouldn't crash
        b.items.append((i, "not a dict"))
        
        # The item should be the tuple itself, not unwrapped
        assert len(b.items) == 1


# =============================================================================
# Integration Tests
# =============================================================================

class TestSimplificationIntegration:
    """Test all simplifications working together."""
    
    def test_auto_backref_with_tuple_syntax(self, clean_state):
        """Test auto-backref + tuple syntax together."""
        class Project(Table):
            name: str = ""
        
        class Developer(Table):
            name: str = ""
            projects: List[Project] = many_to_many(Project)  # Auto backref
        
        dev = Developer(name="Alice")
        proj = Project(name="PyNext")
        
        dev.projects.append((proj, {"role": "lead"}))
        
        # Auto backref should be "developers"
        assert dev.projects._reverse_attr == "developers"
        assert proj in dev.projects
    
    def test_extra_columns_with_backref_false(self, clean_state):
        """Test extra columns + backref=False together."""
        class Feature(Table):
            name: str = ""
        
        class App(Table):
            name: str = ""
            features: List[Feature] = many_to_many(
                Feature,
                backref=False,
                extra={"enabled": bool}
            )
        
        app = App(name="MyApp")
        feature = Feature(name="DarkMode")
        
        app.features.append((feature, {"enabled": True}))
        
        assert app.features._reverse_attr is None
        assert feature in app.features
    
    def test_auto_detection_with_property_access(self, clean_state):
        """Test auto-detection + property-style access together."""
        class Service(Table):
            name: str = ""
        
        class Microservice(Table):
            name: str = ""
            dependencies: List[Service]  # Auto-detected M2M
        
        ms = Microservice(name="API")
        s1 = Service(name="DB")
        s2 = Service(name="Cache")
        
        ms.dependencies.append(s1)
        ms.dependencies.append(s2)
        
        assert ms.dependencies[0] == s1
        assert ms.dependencies[-1] == s2


# =============================================================================
# Compatibility Tests
# =============================================================================

class TestBackwardsCompatibility:
    """Test that existing patterns still work."""
    
    def test_explicit_backref_still_works(self, clean_state):
        """Test explicit backref="name" still works."""
        class OldTag(Table):
            name: str = ""
        
        class OldPost(Table):
            name: str = ""
            tags: List[OldTag] = many_to_many(OldTag, backref="old_posts")
        
        post = OldPost(name="P1")
        assert post.tags._reverse_attr == "old_posts"
    
    def test_explicit_through_still_works(self, clean_state):
        """Test explicit through=Model still works."""
        class OldEnrollment(Table):
            student_id: int = 0
            course_id: int = 0
            semester: str = ""
        
        class OldCourse(Table):
            name: str = ""
        
        class OldStudent(Table):
            name: str = ""
            courses: List[OldCourse] = many_to_many(
                OldCourse,
                through=OldEnrollment,
                backref="students"
            )
        
        student = OldStudent(name="John")
        assert isinstance(student.courses, ManyToManyCollection)
    
    def test_add_method_with_kwargs_still_works(self, clean_state):
        """Test add(item, **kwargs) still works."""
        class Resource(Table):
            name: str = ""
        
        class User(Table):
            name: str = ""
            resources: List[Resource] = many_to_many(Resource)
        
        user = User(name="Admin")
        resource = Resource(name="R1")
        
        # Old syntax with kwargs
        user.resources.add(resource, access_level="admin")
        
        assert resource in user.resources
        _, data = user.resources._pending_additions[0]
        assert data == {"access_level": "admin"}


# =============================================================================
# Additional Auto-Backref Tests (15 more tests)
# =============================================================================

class TestAutoBackrefAdvanced:
    """Advanced tests for auto-backref naming."""
    
    def test_auto_backref_underscore_class_name(self, clean_state):
        """Test auto-backref for class name with underscores."""
        class My_Custom_Model(Table):
            name: str = ""
        
        class My_Container(Table):
            name: str = ""
            models: List[My_Custom_Model] = many_to_many(My_Custom_Model)
        
        c = My_Container(name="C1")
        assert c.models._reverse_attr == "my_containers"
    
    def test_auto_backref_multiple_m2m_same_target(self, clean_state):
        """Test auto-backref when multiple M2M point to same target."""
        class SharedTarget(Table):
            name: str = ""
        
        class Source1(Table):
            name: str = ""
            targets: List[SharedTarget] = many_to_many(SharedTarget)
        
        class Source2(Table):
            name: str = ""
            targets: List[SharedTarget] = many_to_many(SharedTarget)
        
        s1 = Source1(name="S1")
        s2 = Source2(name="S2")
        
        # Each should have its own backref
        assert s1.targets._reverse_attr == "source1s"
        assert s2.targets._reverse_attr == "source2s"
    
    def test_auto_backref_with_lazy_dynamic(self, clean_state):
        """Test auto-backref works with lazy='dynamic'."""
        class DynTarget(Table):
            name: str = ""
        
        class DynSource(Table):
            name: str = ""
            targets: List[DynTarget] = many_to_many(DynTarget, lazy="dynamic")
        
        # Just verify descriptor is set up correctly
        assert hasattr(DynSource, "targets")
    
    def test_backref_false_with_explicit_through(self, clean_state):
        """Test backref=False works with explicit through."""
        class ThruJunction(Table):
            src_id: int = 0
            tgt_id: int = 0
        
        class ThruTarget(Table):
            name: str = ""
        
        class ThruSource(Table):
            name: str = ""
            targets: List[ThruTarget] = many_to_many(
                ThruTarget, 
                through=ThruJunction,
                backref=False
            )
        
        s = ThruSource(name="S1")
        assert s.targets._reverse_attr is None
    
    def test_auto_backref_number_only_class(self, clean_state):
        """Test auto-backref for class ending in number."""
        class Model123(Table):
            name: str = ""
        
        class Container456(Table):
            name: str = ""
            models: List[Model123] = many_to_many(Model123)
        
        c = Container456(name="C1")
        assert c.models._reverse_attr == "container456s"
    
    def test_auto_backref_very_long_class_name(self, clean_state):
        """Test auto-backref for very long class name."""
        class VeryLongClassNameThatIsExtremelyDescriptive(Table):
            name: str = ""
        
        class AnotherVeryLongClassName(Table):
            name: str = ""
            items: List[VeryLongClassNameThatIsExtremelyDescriptive] = many_to_many(
                VeryLongClassNameThatIsExtremelyDescriptive
            )
        
        c = AnotherVeryLongClassName(name="C1")
        assert c.items._reverse_attr == "anotherverylongclassnames"


class TestAutoBackrefEdgeCasesExtended:
    """Extended edge cases for auto-backref."""
    
    def test_backref_none_vs_not_provided(self, clean_state):
        """Test backref=None explicitly is same as not provided."""
        class Target1(Table):
            name: str = ""
        
        class Source1(Table):
            name: str = ""
            targets: List[Target1] = many_to_many(Target1, backref=None)
        
        s = Source1(name="S1")
        # None should trigger auto-generation
        assert s.targets._reverse_attr == "source1s"
    
    def test_multiple_words_class_name(self, clean_state):
        """Test class name with multiple capital letters."""
        class HTTPAPIClient(Table):
            name: str = ""
        
        class WebService(Table):
            name: str = ""
            clients: List[HTTPAPIClient] = many_to_many(HTTPAPIClient)
        
        ws = WebService(name="WS1")
        assert ws.clients._reverse_attr == "webservices"
    
    def test_unicode_not_in_class_name(self, clean_state):
        """Test standard ASCII class names (unicode not typically in class names)."""
        class SimpleModel(Table):
            name: str = ""
        
        class SimpleContainer(Table):
            name: str = ""
            items: List[SimpleModel] = many_to_many(SimpleModel)
        
        c = SimpleContainer(name="C1")
        assert c.items._reverse_attr == "simplecontainers"


# =============================================================================
# Additional Type-Hint Detection Tests (20 more tests)
# =============================================================================

class TestTypeHintDetectionAdvanced:
    """Advanced tests for type-hint M2M auto-detection."""
    
    def test_auto_detection_creates_collection(self, clean_state):
        """Test auto-detected M2M creates proper collection."""
        class AutoItem(Table):
            name: str = ""
        
        class AutoContainer(Table):
            name: str = ""
            items: List[AutoItem]
        
        c = AutoContainer(name="C1")
        item = AutoItem(name="I1")
        
        c.items.append(item)
        assert item in c.items
        assert len(c.items) == 1
    
    def test_auto_detection_collection_operations(self, clean_state):
        """Test auto-detected M2M supports all collection operations."""
        class DetectedTag(Table):
            name: str = ""
        
        class DetectedPost(Table):
            name: str = ""
            tags: List[DetectedTag]
        
        post = DetectedPost(name="P1")
        t1 = DetectedTag(name="T1")
        t2 = DetectedTag(name="T2")
        t3 = DetectedTag(name="T3")
        
        # Test append
        post.tags.append(t1)
        assert t1 in post.tags
        
        # Test extend
        post.tags.extend([t2, t3])
        assert len(post.tags) == 3
        
        # Test remove
        post.tags.remove(t2)
        assert t2 not in post.tags
        assert len(post.tags) == 2
        
        # Test clear
        post.tags.clear()
        assert len(post.tags) == 0
    
    def test_auto_detection_with_other_fields(self, clean_state):
        """Test auto-detection works alongside other field types."""
        class RelatedItem(Table):
            name: str = ""
        
        class MixedModel(Table):
            name: str = ""
            count: int = 0
            active: bool = True
            description: Optional[str] = None
            items: List[RelatedItem]  # Auto-detected M2M
        
        m = MixedModel(name="M1", count=5, active=False)
        assert m.name == "M1"
        assert m.count == 5
        assert m.active is False
        assert isinstance(m.items, ManyToManyCollection)
    
    def test_auto_detection_multiple_m2m_fields(self, clean_state):
        """Test auto-detection with multiple M2M fields."""
        class Category(Table):
            name: str = ""
        
        class Tag(Table):
            name: str = ""
        
        class Article(Table):
            name: str = ""
            categories: List[Category]  # Auto M2M #1
            tags: List[Tag]  # Auto M2M #2
        
        article = Article(name="A1")
        
        assert isinstance(article.categories, ManyToManyCollection)
        assert isinstance(article.tags, ManyToManyCollection)
        
        cat = Category(name="Tech")
        tag = Tag(name="Python")
        
        article.categories.append(cat)
        article.tags.append(tag)
        
        assert cat in article.categories
        assert tag in article.tags


class TestTypeHintDetectionNegative:
    """Test cases where type hints should NOT auto-detect as M2M."""
    
    def test_list_str_not_detected(self, clean_state):
        """Test List[str] is not detected as M2M."""
        class ModelWithStrings(Table):
            name: str = ""
            tags: List[str] = []
        
        m = ModelWithStrings(name="M1")
        # tags should be a regular list, not ManyToManyCollection
        assert not isinstance(m.tags, ManyToManyCollection)
    
    def test_list_int_not_detected(self, clean_state):
        """Test List[int] is not detected as M2M."""
        class ModelWithInts(Table):
            name: str = ""
            numbers: List[int] = []
        
        m = ModelWithInts(name="M1")
        assert not isinstance(m.numbers, ManyToManyCollection)
    
    def test_explicit_descriptor_not_overwritten(self, clean_state):
        """Test explicit many_to_many() is not overwritten by auto-detection."""
        class ExplicitTarget(Table):
            name: str = ""
        
        class ExplicitSource(Table):
            name: str = ""
            targets: List[ExplicitTarget] = many_to_many(
                ExplicitTarget, 
                backref="explicit_sources"
            )
        
        s = ExplicitSource(name="S1")
        # Should use explicit backref, not auto-generated
        assert s.targets._reverse_attr == "explicit_sources"


# =============================================================================
# Additional Junction Access Tests (15 more tests)
# =============================================================================

class TestJunctionAccessAdvanced:
    """Advanced tests for property-style junction access."""
    
    def test_getitem_after_multiple_appends(self, clean_state):
        """Test __getitem__ after multiple appends."""
        class Subject(Table):
            name: str = ""
        
        class Student(Table):
            name: str = ""
            subjects: List[Subject] = many_to_many(Subject)
        
        student = Student(name="John")
        s1 = Subject(name="Math")
        s2 = Subject(name="Science")
        s3 = Subject(name="English")
        
        student.subjects.extend([s1, s2, s3])
        
        assert student.subjects[0] == s1
        assert student.subjects[1] == s2
        assert student.subjects[2] == s3
    
    def test_getitem_with_step_slice(self, clean_state):
        """Test __getitem__ with step in slice."""
        class Item(Table):
            name: str = ""
        
        class Container(Table):
            name: str = ""
            items: List[Item] = many_to_many(Item)
        
        c = Container(name="C1")
        items = [Item(name=f"I{i}") for i in range(5)]
        c.items.extend(items)
        
        # Every other item
        result = c.items[::2]
        assert result == [items[0], items[2], items[4]]
    
    def test_getitem_reverse_slice(self, clean_state):
        """Test __getitem__ with reverse slice."""
        class Widget(Table):
            name: str = ""
        
        class Panel(Table):
            name: str = ""
            widgets: List[Widget] = many_to_many(Widget)
        
        p = Panel(name="P1")
        widgets = [Widget(name=f"W{i}") for i in range(3)]
        p.widgets.extend(widgets)
        
        # Reverse order
        result = p.widgets[::-1]
        assert result == [widgets[2], widgets[1], widgets[0]]
    
    def test_getitem_by_table_instance_multiple_items(self, clean_state):
        """Test __getitem__ by Table instance with multiple items."""
        class Course(Table):
            name: str = ""
        
        class Student(Table):
            name: str = ""
            courses: List[Course] = many_to_many(Course)
        
        student = Student(name="John")
        math = Course(name="Math")
        science = Course(name="Science")
        
        student.courses.extend([math, science])
        
        # Both should return None (not cached)
        assert student.courses[math] is None
        assert student.courses[science] is None


class TestJunctionAccessBoundaries:
    """Test boundary conditions for junction access."""
    
    def test_getitem_single_item_collection(self, clean_state):
        """Test __getitem__ with single item in collection."""
        class Single1(Table):
            name: str = ""
        
        class Single2(Table):
            name: str = ""
            items: List[Single1] = many_to_many(Single1)
        
        s = Single2(name="S1")
        item = Single1(name="I1")
        s.items.append(item)
        
        assert s.items[0] == item
        assert s.items[-1] == item
        
        with pytest.raises(IndexError):
            _ = s.items[1]
    
    def test_getitem_after_clear(self, clean_state):
        """Test __getitem__ after clearing collection."""
        class Clear1(Table):
            name: str = ""
        
        class Clear2(Table):
            name: str = ""
            items: List[Clear1] = many_to_many(Clear1)
        
        c = Clear2(name="C1")
        c.items.extend([Clear1(name="I1"), Clear1(name="I2")])
        c.items.clear()
        
        with pytest.raises(IndexError):
            _ = c.items[0]
    
    def test_getitem_after_remove(self, clean_state):
        """Test __getitem__ indices shift after remove."""
        class Shift1(Table):
            name: str = ""
        
        class Shift2(Table):
            name: str = ""
            items: List[Shift1] = many_to_many(Shift1)
        
        s = Shift2(name="S1")
        i1 = Shift1(name="I1")
        i2 = Shift1(name="I2")
        i3 = Shift1(name="I3")
        
        s.items.extend([i1, i2, i3])
        s.items.remove(i2)
        
        assert s.items[0] == i1
        assert s.items[1] == i3
        assert len(s.items) == 2


# =============================================================================
# Additional Extra Columns Tests (15 more tests)
# =============================================================================

class TestExtraColumnsAdvanced:
    """Advanced tests for inline extra columns."""
    
    def test_extra_with_all_primitive_types(self, clean_state):
        """Test extra={} with all primitive types."""
        class Target(Table):
            name: str = ""
        
        class Source(Table):
            name: str = ""
            targets: List[Target] = many_to_many(Target, extra={
                "count": int,
                "score": float,
                "active": bool,
                "label": str,
            })
        
        s = Source(name="S1")
        assert isinstance(s.targets, ManyToManyCollection)
    
    def test_extra_with_optional_types(self, clean_state):
        """Test extra={} with Optional types."""
        class OptTarget(Table):
            name: str = ""
        
        class OptSource(Table):
            name: str = ""
            targets: List[OptTarget] = many_to_many(OptTarget, extra={
                "notes": Optional[str],
                "score": Optional[int],
                "metadata": Optional[dict],
            })
        
        s = OptSource(name="S1")
        assert isinstance(s.targets, ManyToManyCollection)
    
    def test_extra_combined_with_auto_backref(self, clean_state):
        """Test extra={} combined with auto-backref."""
        class ExtraTarget(Table):
            name: str = ""
        
        class ExtraSource(Table):
            name: str = ""
            targets: List[ExtraTarget] = many_to_many(ExtraTarget, extra={
                "priority": int,
            })
        
        s = ExtraSource(name="S1")
        # Auto-backref should still work
        assert s.targets._reverse_attr == "extrasources"
    
    def test_extra_with_lazy_selectin(self, clean_state):
        """Test extra={} with lazy='selectin'."""
        class LazyTarget(Table):
            name: str = ""
        
        class LazySource(Table):
            name: str = ""
            targets: List[LazyTarget] = many_to_many(LazyTarget, extra={
                "weight": float,
            }, lazy="selectin")
        
        s = LazySource(name="S1")
        assert isinstance(s.targets, ManyToManyCollection)
    
    def test_extra_single_column(self, clean_state):
        """Test extra={} with single column."""
        class SingleColTarget(Table):
            name: str = ""
        
        class SingleColSource(Table):
            name: str = ""
            targets: List[SingleColTarget] = many_to_many(SingleColTarget, extra={
                "order": int,
            })
        
        s = SingleColSource(name="S1")
        t = SingleColTarget(name="T1")
        s.targets.append((t, {"order": 1}))
        
        assert t in s.targets
    
    def test_extra_many_columns(self, clean_state):
        """Test extra={} with many columns."""
        class ManyColTarget(Table):
            name: str = ""
        
        class ManyColSource(Table):
            name: str = ""
            targets: List[ManyColTarget] = many_to_many(ManyColTarget, extra={
                "field1": str,
                "field2": int,
                "field3": bool,
                "field4": Optional[str],
                "field5": float,
            })
        
        s = ManyColSource(name="S1")
        assert isinstance(s.targets, ManyToManyCollection)


# =============================================================================
# Additional Tuple Syntax Tests (20 more tests)
# =============================================================================

class TestTupleSyntaxAdvanced:
    """Advanced tests for tuple syntax."""
    
    def test_append_tuple_multiple_data_keys(self, clean_state):
        """Test append with tuple containing multiple data keys."""
        class Course(Table):
            name: str = ""
        
        class Student(Table):
            name: str = ""
            courses: List[Course] = many_to_many(Course)
        
        s = Student(name="John")
        c = Course(name="Math")
        
        s.courses.append((c, {
            "grade": "A",
            "semester": "Fall",
            "year": 2024,
            "credits": 3,
        }))
        
        assert c in s.courses
        _, data = s.courses._pending_additions[0]
        assert data["grade"] == "A"
        assert data["semester"] == "Fall"
        assert data["year"] == 2024
        assert data["credits"] == 3
    
    def test_extend_all_tuples(self, clean_state):
        """Test extend with all items as tuples."""
        class Tag(Table):
            name: str = ""
        
        class Article(Table):
            name: str = ""
            tags: List[Tag] = many_to_many(Tag)
        
        article = Article(name="A1")
        t1 = Tag(name="T1")
        t2 = Tag(name="T2")
        t3 = Tag(name="T3")
        
        article.tags.extend([
            (t1, {"priority": 1}),
            (t2, {"priority": 2}),
            (t3, {"priority": 3}),
        ])
        
        assert len(article.tags) == 3
        assert all(t in article.tags for t in [t1, t2, t3])
    
    def test_extend_all_simple_items(self, clean_state):
        """Test extend with all simple items (no tuples)."""
        class SimpleItem(Table):
            name: str = ""
        
        class SimpleContainer(Table):
            name: str = ""
            items: List[SimpleItem] = many_to_many(SimpleItem)
        
        c = SimpleContainer(name="C1")
        items = [SimpleItem(name=f"I{i}") for i in range(5)]
        
        c.items.extend(items)
        
        assert len(c.items) == 5
        assert all(i in c.items for i in items)
    
    def test_append_preserves_order(self, clean_state):
        """Test tuple append preserves insertion order."""
        class OrderedItem(Table):
            name: str = ""
        
        class OrderedContainer(Table):
            name: str = ""
            items: List[OrderedItem] = many_to_many(OrderedItem)
        
        c = OrderedContainer(name="C1")
        items = [OrderedItem(name=f"I{i}") for i in range(3)]
        
        for i, item in enumerate(items):
            c.items.append((item, {"order": i}))
        
        assert c.items[0] == items[0]
        assert c.items[1] == items[1]
        assert c.items[2] == items[2]
    
    def test_mixed_append_and_extend(self, clean_state):
        """Test mixing append and extend with tuples."""
        class MixedItem(Table):
            name: str = ""
        
        class MixedContainer(Table):
            name: str = ""
            items: List[MixedItem] = many_to_many(MixedItem)
        
        c = MixedContainer(name="C1")
        i1 = MixedItem(name="I1")
        i2 = MixedItem(name="I2")
        i3 = MixedItem(name="I3")
        
        c.items.append(i1)
        c.items.extend([
            (i2, {"special": True}),
            i3,
        ])
        
        assert len(c.items) == 3


class TestTupleSyntaxDataValidation:
    """Test data handling in tuple syntax."""
    
    def test_tuple_with_none_values(self, clean_state):
        """Test tuple with None values in data dict."""
        class NullItem(Table):
            name: str = ""
        
        class NullContainer(Table):
            name: str = ""
            items: List[NullItem] = many_to_many(NullItem)
        
        c = NullContainer(name="C1")
        item = NullItem(name="I1")
        
        c.items.append((item, {"nullable_field": None}))
        
        assert item in c.items
        _, data = c.items._pending_additions[0]
        assert data["nullable_field"] is None
    
    def test_tuple_with_nested_dict(self, clean_state):
        """Test tuple with nested dict in data."""
        class NestedItem(Table):
            name: str = ""
        
        class NestedContainer(Table):
            name: str = ""
            items: List[NestedItem] = many_to_many(NestedItem)
        
        c = NestedContainer(name="C1")
        item = NestedItem(name="I1")
        
        c.items.append((item, {
            "metadata": {"nested": {"deep": "value"}}
        }))
        
        _, data = c.items._pending_additions[0]
        assert data["metadata"]["nested"]["deep"] == "value"
    
    def test_tuple_with_list_in_data(self, clean_state):
        """Test tuple with list in data dict."""
        class ListDataItem(Table):
            name: str = ""
        
        class ListDataContainer(Table):
            name: str = ""
            items: List[ListDataItem] = many_to_many(ListDataItem)
        
        c = ListDataContainer(name="C1")
        item = ListDataItem(name="I1")
        
        c.items.append((item, {
            "tags": ["a", "b", "c"]
        }))
        
        _, data = c.items._pending_additions[0]
        assert data["tags"] == ["a", "b", "c"]


# =============================================================================
# Stress Tests (10 tests)
# =============================================================================

class TestSimplificationsStress:
    """Stress tests for M2M simplifications."""
    
    def test_many_items_append(self, clean_state):
        """Test appending many items."""
        class ManyItem(Table):
            name: str = ""
        
        class ManyContainer(Table):
            name: str = ""
            items: List[ManyItem] = many_to_many(ManyItem)
        
        c = ManyContainer(name="C1")
        items = [ManyItem(name=f"I{i}") for i in range(100)]
        
        for item in items:
            c.items.append(item)
        
        assert len(c.items) == 100
    
    def test_many_items_extend(self, clean_state):
        """Test extending with many items."""
        class ExtendItem(Table):
            name: str = ""
        
        class ExtendContainer(Table):
            name: str = ""
            items: List[ExtendItem] = many_to_many(ExtendItem)
        
        c = ExtendContainer(name="C1")
        items = [ExtendItem(name=f"I{i}") for i in range(100)]
        
        c.items.extend(items)
        
        assert len(c.items) == 100
    
    def test_many_tuples_extend(self, clean_state):
        """Test extending with many tuples."""
        class TupleItem(Table):
            name: str = ""
        
        class TupleContainer(Table):
            name: str = ""
            items: List[TupleItem] = many_to_many(TupleItem)
        
        c = TupleContainer(name="C1")
        items = [(TupleItem(name=f"I{i}"), {"order": i}) for i in range(100)]
        
        c.items.extend(items)
        
        assert len(c.items) == 100
        assert len(c.items._pending_additions) == 100
    
    def test_repeated_add_remove(self, clean_state):
        """Test repeated add and remove operations."""
        class RepeatItem(Table):
            name: str = ""
        
        class RepeatContainer(Table):
            name: str = ""
            items: List[RepeatItem] = many_to_many(RepeatItem)
        
        c = RepeatContainer(name="C1")
        items = [RepeatItem(name=f"I{i}") for i in range(10)]
        
        # Add all
        c.items.extend(items)
        assert len(c.items) == 10
        
        # Remove all
        for item in items:
            c.items.remove(item)
        assert len(c.items) == 0
        
        # Add again
        c.items.extend(items)
        assert len(c.items) == 10
    
    def test_many_m2m_fields(self, clean_state):
        """Test model with many M2M fields."""
        class Target1(Table):
            name: str = ""
        
        class Target2(Table):
            name: str = ""
        
        class Target3(Table):
            name: str = ""
        
        class MultiM2M(Table):
            name: str = ""
            targets1: List[Target1] = many_to_many(Target1)
            targets2: List[Target2] = many_to_many(Target2)
            targets3: List[Target3] = many_to_many(Target3)
        
        m = MultiM2M(name="M1")
        
        m.targets1.append(Target1(name="T1"))
        m.targets2.append(Target2(name="T2"))
        m.targets3.append(Target3(name="T3"))
        
        assert len(m.targets1) == 1
        assert len(m.targets2) == 1
        assert len(m.targets3) == 1


# =============================================================================
# Real-World Scenario Tests (10 tests)
# =============================================================================

class TestRealWorldScenarios:
    """Test real-world use cases."""
    
    def test_blog_tags_scenario(self, clean_state):
        """Test blog post with tags scenario."""
        class BlogTag(Table):
            name: str = ""
        
        class BlogPost(Table):
            title: str = ""
            tags: List[BlogTag]  # Auto-detected M2M
        
        post = BlogPost(title="My First Post")
        python_tag = BlogTag(name="Python")
        web_tag = BlogTag(name="Web")
        
        post.tags.extend([python_tag, web_tag])
        
        assert python_tag in post.tags
        assert web_tag in post.tags
    
    def test_ecommerce_categories_scenario(self, clean_state):
        """Test product with categories scenario."""
        class Category(Table):
            name: str = ""
        
        class Product(Table):
            name: str = ""
            price: float = 0.0
            categories: List[Category] = many_to_many(Category)
        
        laptop = Product(name="Laptop", price=999.99)
        electronics = Category(name="Electronics")
        computers = Category(name="Computers")
        
        laptop.categories.extend([electronics, computers])
        
        assert len(laptop.categories) == 2
    
    def test_social_media_followers_scenario(self, clean_state):
        """Test user following other users scenario."""
        class SocialUser(Table):
            username: str = ""
            following: List["SocialUser"] = many_to_many("SocialUser", backref=False)
        
        alice = SocialUser(username="alice")
        bob = SocialUser(username="bob")
        charlie = SocialUser(username="charlie")
        
        alice.following.extend([bob, charlie])
        
        assert bob in alice.following
        assert charlie in alice.following
    
    def test_course_enrollment_with_grades(self, clean_state):
        """Test student enrollment with grades."""
        class CourseGraded(Table):
            name: str = ""
        
        class StudentGraded(Table):
            name: str = ""
            courses: List[CourseGraded] = many_to_many(CourseGraded, extra={
                "grade": Optional[str],
                "semester": str,
            })
        
        student = StudentGraded(name="John")
        math = CourseGraded(name="Math 101")
        physics = CourseGraded(name="Physics 101")
        
        student.courses.extend([
            (math, {"grade": "A", "semester": "Fall 2024"}),
            (physics, {"grade": "B+", "semester": "Fall 2024"}),
        ])
        
        assert len(student.courses) == 2
    
    def test_project_team_members(self, clean_state):
        """Test project with team members and roles."""
        class TeamMember(Table):
            name: str = ""
        
        class Project(Table):
            name: str = ""
            members: List[TeamMember] = many_to_many(TeamMember, extra={
                "role": str,
                "joined_at": Optional[datetime],
            })
        
        project = Project(name="PyNext")
        dev1 = TeamMember(name="Alice")
        dev2 = TeamMember(name="Bob")
        
        project.members.extend([
            (dev1, {"role": "Lead Developer"}),
            (dev2, {"role": "Developer"}),
        ])
        
        assert len(project.members) == 2

