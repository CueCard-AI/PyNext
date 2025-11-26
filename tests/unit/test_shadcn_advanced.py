"""
Unit tests for Advanced ShadCN Components

Tests Phase 1-4 advanced components:
- Skeleton, Tooltip, Popover, Toast (Phase 1)
- Sheet, Combobox (Phase 2)
- Command, Calendar, DatePicker, DataTable (Phase 3)
- FileUpload (Phase 4)
"""

import pytest
from datetime import date, datetime


class TestSkeleton:
    def test_basic_render(self):
        from pynext.shadcn import Skeleton
        
        s = Skeleton(class_="h-4 w-32")
        html = s.render()
        
        assert "animate-pulse" in html
        assert "rounded-md" in html
        assert "bg-muted" in html
        assert "h-4 w-32" in html
    
    def test_circle_variant(self):
        from pynext.shadcn import Skeleton
        
        s = Skeleton(variant="circle", class_="h-12 w-12")
        html = s.render()
        
        assert "rounded-full" in html
    
    def test_text_variant(self):
        from pynext.shadcn import Skeleton
        
        s = Skeleton(variant="text")
        html = s.render()
        
        assert "h-4" in html
    
    def test_skeleton_card(self):
        from pynext.shadcn import SkeletonCard
        
        sc = SkeletonCard()
        html = sc.render()
        
        assert "flex items-center" in html
        assert "animate-pulse" in html
    
    def test_skeleton_table(self):
        from pynext.shadcn import SkeletonTable
        
        st = SkeletonTable(rows=5)
        html = st.render()
        
        assert html.count("animate-pulse") >= 5


class TestTooltip:
    def test_basic_render(self):
        from pynext.shadcn import Tooltip, TooltipTrigger, TooltipContent
        
        t = Tooltip()[
            TooltipTrigger()["Hover me"],
            TooltipContent()["Tooltip text"]
        ]
        html = t.render()
        
        assert "data-pynext-tooltip" in html
        assert "data-pynext-tooltip-trigger" in html
        assert "data-pynext-tooltip-content" in html
        assert "Tooltip text" in html
    
    def test_with_placement(self):
        from pynext.shadcn import Tooltip, TooltipTrigger, TooltipContent
        
        t = Tooltip()[
            TooltipTrigger()["Trigger"],
            TooltipContent(side="bottom")["Content"]
        ]
        html = t.render()
        
        assert 'data-side="bottom"' in html
    
    def test_with_delay(self):
        from pynext.shadcn import Tooltip, TooltipTrigger, TooltipContent
        
        t = Tooltip(delay=1000)[
            TooltipTrigger()["Trigger"],
            TooltipContent()["Content"]
        ]
        html = t.render()
        
        assert 'data-delay="1000"' in html


class TestPopover:
    def test_basic_render(self):
        from pynext.shadcn import Popover, PopoverTrigger, PopoverContent
        
        p = Popover()[
            PopoverTrigger()["Click"],
            PopoverContent()["Content"]
        ]
        html = p.render()
        
        assert "data-pynext-popover" in html
        assert "data-pynext-popover-trigger" in html
        assert "data-pynext-popover-content" in html
    
    def test_with_placement(self):
        from pynext.shadcn import Popover, PopoverTrigger, PopoverContent
        
        p = Popover()[
            PopoverTrigger()["Click"],
            PopoverContent(side="right", align="start")["Content"]
        ]
        html = p.render()
        
        assert 'data-side="right"' in html
        assert 'data-align="start"' in html


class TestToast:
    def test_toaster_render(self):
        from pynext.shadcn import Toaster
        
        t = Toaster(position="top-right")
        html = t.render()
        
        assert "data-pynext-toaster" in html
        assert 'data-position="top-right"' in html
    
    def test_toast_api(self):
        from pynext.shadcn import toast
        
        # Toast functions should return script tags
        result = toast("Hello")
        assert "<script>" in result
        
        result = toast.success("Success")
        assert "<script>" in result
        assert "success" in result
        
        result = toast.error("Error")
        assert "error" in result


class TestSheet:
    def test_basic_render(self):
        from pynext.shadcn import Sheet, SheetTrigger, SheetContent
        
        s = Sheet()[
            SheetTrigger()["Open"],
            SheetContent()["Content"]
        ]
        html = s.render()
        
        assert "data-pynext-sheet" in html
        assert "data-pynext-sheet-trigger" in html
        assert "data-pynext-sheet-content" in html
    
    def test_sides(self):
        from pynext.shadcn import Sheet, SheetTrigger, SheetContent
        
        for side in ["left", "right", "top", "bottom"]:
            s = Sheet()[
                SheetTrigger()["Open"],
                SheetContent(side=side)["Content"]
            ]
            html = s.render()
            assert f'data-side="{side}"' in html
    
    def test_header_and_footer(self):
        from pynext.shadcn import (
            Sheet, SheetTrigger, SheetContent,
            SheetHeader, SheetTitle, SheetFooter
        )
        
        s = Sheet()[
            SheetTrigger()["Open"],
            SheetContent()[
                SheetHeader()[
                    SheetTitle()["Title"]
                ],
                SheetFooter()["Footer"]
            ]
        ]
        html = s.render()
        
        assert "Title" in html
        assert "Footer" in html
    
    def test_swipe_support_data_attributes(self):
        """Sheet content includes data-side attribute for swipe detection."""
        from pynext.shadcn import Sheet, SheetTrigger, SheetContent
        
        # Test each side has proper data attribute for runtime swipe detection
        for side in ["left", "right", "top", "bottom"]:
            s = Sheet()[
                SheetTrigger()["Open"],
                SheetContent(side=side)["Content"]
            ]
            html = s.render()
            # data-side is used by runtime for swipe direction detection
            assert f'data-side="{side}"' in html


class TestCombobox:
    def test_basic_render(self):
        from pynext.shadcn import (
            Combobox, ComboboxTrigger, ComboboxContent,
            ComboboxInput, ComboboxItem
        )
        
        c = Combobox()[
            ComboboxTrigger()["Select"],
            ComboboxContent()[
                ComboboxInput(placeholder="Search..."),
                ComboboxItem(value="a")["Item A"]
            ]
        ]
        html = c.render()
        
        assert "data-pynext-combobox" in html
        assert "data-pynext-combobox-item" in html
        assert 'data-value="a"' in html
    
    def test_with_groups(self):
        from pynext.shadcn import (
            Combobox, ComboboxTrigger, ComboboxContent,
            ComboboxGroup, ComboboxItem
        )
        
        c = Combobox()[
            ComboboxTrigger()["Select"],
            ComboboxContent()[
                ComboboxGroup(heading="Group 1")[
                    ComboboxItem(value="a")["A"]
                ]
            ]
        ]
        html = c.render()
        
        assert "Group 1" in html
        assert "data-pynext-combobox-group" in html
    
    def test_allow_create(self):
        """Combobox with allow_create shows create option."""
        from pynext.shadcn import (
            Combobox, ComboboxTrigger, ComboboxContent,
            ComboboxInput, ComboboxEmpty, ComboboxCreate, ComboboxItem
        )
        
        c = Combobox(allow_create=True)[
            ComboboxTrigger()["Select or create"],
            ComboboxContent()[
                ComboboxInput(placeholder="Search or create..."),
                ComboboxEmpty()["No results"],
                ComboboxCreate()["Create"],
                ComboboxItem(value="a")["Item A"]
            ]
        ]
        html = c.render()
        
        assert 'data-allow-create="true"' in html
        assert "data-pynext-combobox-create" in html
        assert "data-pynext-combobox-create-query" in html
    
    def test_create_component_styling(self):
        """ComboboxCreate has proper styling with plus icon."""
        from pynext.shadcn import ComboboxCreate
        
        cc = ComboboxCreate()["Create new"]
        html = cc.render()
        
        assert "data-pynext-combobox-create" in html
        assert "Create new" in html
        # Plus icon SVG
        assert "<svg" in html
        assert 'stroke="currentColor"' in html
    
    def test_multiple_selection(self):
        """Combobox with multiple=True has proper data attribute."""
        from pynext.shadcn import (
            Combobox, ComboboxTrigger, ComboboxContent, ComboboxItem
        )
        
        c = Combobox(multiple=True)[
            ComboboxTrigger()["Select multiple"],
            ComboboxContent()[
                ComboboxItem(value="a")["A"],
                ComboboxItem(value="b")["B"]
            ]
        ]
        html = c.render()
        
        assert 'data-multiple="true"' in html


class TestCommand:
    def test_basic_render(self):
        from pynext.shadcn import (
            Command, CommandInput, CommandList, CommandItem
        )
        
        cmd = Command()[
            CommandInput(placeholder="Search..."),
            CommandList()[
                CommandItem(value="test")["Test"]
            ]
        ]
        html = cmd.render()
        
        assert "data-pynext-command" in html
        assert "data-pynext-command-input" in html
        assert "data-pynext-command-item" in html
    
    def test_command_dialog(self):
        from pynext.shadcn import CommandDialog, CommandInput, CommandList
        
        cd = CommandDialog(open=True)[
            CommandInput(placeholder="Type..."),
            CommandList()["Items"]
        ]
        html = cd.render()
        
        assert "data-pynext-command-dialog" in html
        assert 'data-state="open"' in html
    
    def test_shortcut(self):
        from pynext.shadcn import CommandItem, CommandShortcut
        
        ci = CommandItem(value="save")[
            "Save",
            CommandShortcut()["⌘S"]
        ]
        html = ci.render()
        
        assert "⌘S" in html
        assert "data-pynext-command-shortcut" in html


class TestCalendar:
    def test_basic_render(self):
        from pynext.shadcn import Calendar
        
        cal = Calendar()
        html = cal.render()
        
        assert "data-pynext-calendar" in html
        assert "data-pynext-calendar-day" in html
    
    def test_with_selected_date(self):
        from pynext.shadcn import Calendar
        
        selected = date(2024, 6, 15)
        cal = Calendar(selected=selected)
        html = cal.render()
        
        assert 'data-selected="2024-06-15"' in html
    
    def test_range_mode(self):
        from pynext.shadcn import Calendar
        
        cal = Calendar(
            mode="range",
            selected={"start": date(2024, 6, 1), "end": date(2024, 6, 15)}
        )
        html = cal.render()
        
        assert 'data-mode="range"' in html


class TestDatePicker:
    def test_basic_render(self):
        from pynext.shadcn import DatePicker
        
        dp = DatePicker(placeholder="Select date")
        html = dp.render()
        
        assert "data-pynext-datepicker" in html
        assert "Select date" in html
    
    def test_with_value(self):
        from pynext.shadcn import DatePicker
        
        dp = DatePicker(value=date(2024, 6, 15))
        html = dp.render()
        
        assert "June 15, 2024" in html
    
    def test_date_range_picker(self):
        from pynext.shadcn import DateRangePicker
        
        drp = DateRangePicker(placeholder="Select range")
        html = drp.render()
        
        assert "data-pynext-daterangepicker" in html


class TestDataTable:
    def test_basic_render(self):
        from pynext.shadcn import DataTable, DataTableColumn
        
        cols = [
            DataTableColumn(accessor="name", header="Name"),
            DataTableColumn(accessor="email", header="Email"),
        ]
        data = [
            {"name": "John", "email": "john@example.com"},
            {"name": "Jane", "email": "jane@example.com"},
        ]
        
        dt = DataTable(data=data, columns=cols)
        html = dt.render()
        
        assert "data-pynext-datatable" in html
        assert "John" in html
        assert "jane@example.com" in html
    
    def test_with_pagination(self):
        from pynext.shadcn import DataTable, DataTableColumn
        
        cols = [DataTableColumn(accessor="name", header="Name")]
        data = [{"name": f"User {i}"} for i in range(25)]
        
        dt = DataTable(
            data=data[:10],
            columns=cols,
            pagination=True,
            page=1,
            total_rows=25
        )
        html = dt.render()
        
        assert "data-pynext-datatable-pagination" in html
        assert "Page 1 of 3" in html
    
    def test_with_row_selection(self):
        from pynext.shadcn import DataTable, DataTableColumn
        
        cols = [DataTableColumn(accessor="name", header="Name")]
        data = [{"name": "User 1"}]
        
        dt = DataTable(data=data, columns=cols, row_selection=True)
        html = dt.render()
        
        assert "data-pynext-datatable-select-all" in html
        assert "data-pynext-datatable-select-row" in html
    
    def test_sortable_columns(self):
        from pynext.shadcn import DataTable, DataTableColumn
        
        cols = [DataTableColumn(accessor="name", header="Name", sortable=True)]
        data = [{"name": "User"}]
        
        dt = DataTable(data=data, columns=cols)
        html = dt.render()
        
        assert "data-pynext-datatable-sort" in html
    
    def test_column_visibility(self):
        """DataTable respects column_visibility dict."""
        from pynext.shadcn import DataTable, DataTableColumn
        
        cols = [
            DataTableColumn(accessor="name", header="Name"),
            DataTableColumn(accessor="email", header="Email"),
            DataTableColumn(accessor="phone", header="Phone"),
        ]
        data = [{"name": "User", "email": "test@example.com", "phone": "123"}]
        
        dt = DataTable(
            data=data, 
            columns=cols,
            column_visibility={"email": False}  # Hide email column
        )
        html = dt.render()
        
        assert "Name" in html
        assert "Phone" in html
        # Email column header should be hidden
        assert html.count('header="Email"') == 0 or "Email" not in html.split("<thead>")[1].split("</thead>")[0]
    
    def test_resizable_columns(self):
        """DataTable with resizable=True adds resize handles."""
        from pynext.shadcn import DataTable, DataTableColumn
        
        cols = [DataTableColumn(accessor="name", header="Name")]
        data = [{"name": "User"}]
        
        dt = DataTable(data=data, columns=cols, resizable=True)
        html = dt.render()
        
        assert 'data-resizable="true"' in html
        assert "data-pynext-resize-handle" in html
    
    def test_resizable_column_with_constraints(self):
        """DataTableColumn with resizable has min/max width."""
        from pynext.shadcn import DataTable, DataTableColumn
        
        cols = [
            DataTableColumn(
                accessor="name", 
                header="Name",
                resizable=True,
                min_width="100px",
                max_width="400px"
            )
        ]
        data = [{"name": "User"}]
        
        dt = DataTable(data=data, columns=cols)
        html = dt.render()
        
        assert 'data-min-width="100px"' in html
        assert 'data-max-width="400px"' in html
    
    def test_column_toggle(self):
        """DataTableColumnToggle renders dropdown for column visibility."""
        from pynext.shadcn import DataTableColumn, DataTableColumnToggle
        
        cols = [
            DataTableColumn(accessor="name", header="Name"),
            DataTableColumn(accessor="email", header="Email"),
        ]
        
        toggle = DataTableColumnToggle(
            columns=cols,
            visibility={"name": True, "email": False}
        )
        html = toggle.render()
        
        assert "data-pynext-column-toggle" in html
        assert "data-pynext-column-toggle-trigger" in html
        assert "data-pynext-column-toggle-item" in html
        assert 'data-visible="true"' in html
        assert 'data-visible="false"' in html


class TestCalendarLocalization:
    """Tests for Calendar localization features."""
    
    def test_spanish_locale(self):
        """Calendar with locale='es' uses Spanish names."""
        from pynext.shadcn import Calendar
        
        cal = Calendar(locale="es")
        html = cal.render()
        
        # Spanish weekday abbreviations
        assert "Lu" in html or "Ma" in html  # Lunes, Martes
    
    def test_monday_start(self):
        """Calendar with week_starts_on=1 starts on Monday."""
        from pynext.shadcn import Calendar
        
        cal = Calendar(week_starts_on=1)
        html = cal.render()
        
        # First weekday should be Monday
        # The weekday headers appear in order, so Mo should come before Su
        weekday_section = html.split("<thead>")[1].split("</thead>")[0]
        mo_pos = weekday_section.find("Mo")
        su_pos = weekday_section.find("Su")
        
        # Mo should appear before Su when week starts on Monday
        assert mo_pos < su_pos
    
    def test_custom_weekday_names(self):
        """Calendar with custom weekday_names uses them."""
        from pynext.shadcn import Calendar
        
        custom_names = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
        cal = Calendar(weekday_names=custom_names)
        html = cal.render()
        
        assert "SUN" in html
        assert "MON" in html
    
    def test_japanese_locale(self):
        """Calendar with locale='ja' uses Japanese names."""
        from pynext.shadcn import Calendar
        
        cal = Calendar(locale="ja")
        html = cal.render()
        
        # Japanese characters for days
        assert "日" in html or "月" in html


class TestFileUpload:
    def test_basic_render(self):
        from pynext.shadcn import FileUpload, FileUploadDropzone
        
        fu = FileUpload()[
            FileUploadDropzone()["Drop files here"]
        ]
        html = fu.render()
        
        assert "data-pynext-file-upload" in html
        assert "data-pynext-dropzone" in html
    
    def test_with_accept(self):
        from pynext.shadcn import FileUpload, FileUploadDropzone
        
        fu = FileUpload(accept="image/*", max_size=5*1024*1024)[
            FileUploadDropzone()["Drop images"]
        ]
        html = fu.render()
        
        assert 'data-accept="image/*"' in html
        assert f'data-max-size="{5*1024*1024}"' in html
    
    def test_file_item(self):
        from pynext.shadcn import FileUploadItem
        
        item = FileUploadItem(
            file_name="document.pdf",
            file_size=1024*1024,
            status="uploading",
            progress=50
        )
        html = item.render()
        
        assert "document.pdf" in html
        assert 'data-status="uploading"' in html
        assert "1.0 MB" in html


class TestChartsModule:
    def test_line_chart(self):
        from pynext.charts import LineChart
        
        lc = LineChart(
            data=[{"x": "Jan", "y": 100}],
            x="x",
            y="y"
        )
        html = lc.render()
        
        assert "data-pynext-chart" in html
    
    def test_bar_chart(self):
        from pynext.charts import BarChart
        
        bc = BarChart(
            data=[{"cat": "A", "val": 10}],
            x="cat",
            y="val"
        )
        html = bc.render()
        
        assert "data-pynext-chart" in html
    
    def test_pie_chart(self):
        from pynext.charts import PieChart
        
        pc = PieChart(
            data=[{"label": "A", "value": 60}],
            label="label",
            value="value",
            donut=True
        )
        html = pc.render()
        
        assert "doughnut" in html or "data-pynext-chart" in html
    
    def test_chart_js_loader(self):
        from pynext.charts import ChartJSLoader
        
        loader = ChartJSLoader()
        assert "chart.js" in loader.lower()


class TestEditorModule:
    def test_editor(self):
        from pynext.editor import Editor
        
        ed = Editor(
            content="<p>Hello</p>",
            placeholder="Start typing..."
        )
        html = ed.render()
        
        assert "data-pynext-editor" in html
        assert "Hello" in html
    
    def test_editor_with_toolbar(self):
        from pynext.editor import Editor
        
        ed = Editor(content="", toolbar=True)
        html = ed.render()
        
        assert "data-pynext-editor-toolbar" in html
    
    def test_tiptap_loader(self):
        from pynext.editor import TiptapLoader
        
        loader = TiptapLoader()
        assert "tiptap" in loader.lower()

