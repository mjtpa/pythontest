from kivy.metrics import dp, sp
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.list import OneLineListItem
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition, FadeTransition, CardTransition, \
    SwapTransition
from kivy.clock import Clock, mainthread
from kivy.core.audio import SoundLoader
from kivy.properties import (
    ObjectProperty, NumericProperty, BooleanProperty, ListProperty, StringProperty
)
import arabic_reshaper
from bidi.algorithm import get_display
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.list import OneLineAvatarIconListItem, ILeftBodyTouch, IRightBodyTouch
from kivymd.uix.slider import MDSlider
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.toolbar.toolbar import ActionTopAppBarButton
from kivymd.uix.navigationdrawer import MDNavigationLayout, MDNavigationDrawer
from kivymd.uix.filemanager import MDFileManager
from mutagen import File
from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.mp4 import MP4
from mutagen.asf import ASF
from mutagen.aiff import AIFF
from mutagen.wave import WAVE
from mutagen.oggopus import OggOpus
import traceback
import os
import json
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.image import Image, AsyncImage
from kivy.core.window import Window
from kivy.utils import platform
from kivy.animation import Animation
from kivy.uix.progressbar import ProgressBar
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Line, Ellipse
from kivy.uix.relativelayout import RelativeLayout

# Patch: Set default radius for ActionTopAppBarButton to avoid None error
ActionTopAppBarButton.radius = [dp(24)]
# Patch: Set default radius for MDIconButton to avoid None error
MDIconButton.radius = [dp(24)]

# Custom FontSelectionItem with _left_container for MDDialog compatibility
Builder.load_string('''
<FontSelectionItem>:
    # Add empty _left_container to satisfy MDDialog requirements
    BoxLayout:
        id: _left_container
        size_hint_x: None
        width: 0
''')


class FontSelectionItem(OneLineListItem):
    """Custom list item for font selection that includes _left_container for MDDialog compatibility"""
    pass


Builder.load_string('''
<MusicPlayer>:
    orientation: 'vertical'
    theme_name: "Blue"
    current_font: "D:\\python\\PythonProject1\\fonts\\DroidArabicNaskhRegular.ttf"
    MDNavigationLayout:
        ScreenManager:
            id: screen_manager
            MainScreen:
                name: 'main'
                MDBoxLayout:
                    orientation: 'vertical'
                    MDTopAppBar:
                        id: top_app_bar
                        title: "Favorites" if root.is_favorites_visible else "Music Player"
                        left_action_items:
                            [["menu", lambda x: nav_drawer.set_state("open")]] if not root.is_favorites_visible else \
                            [["arrow-left", lambda x: root.back_to_main()]]
                        elevation: dp(10)
                        specific_text_color: root.get_text_color()
                        right_action_items:
                            [["heart", lambda x: root.show_favorites()]] + \
                            [["magnify", lambda x: root.toggle_search()]] + \
                            ([["close", lambda x: root.toggle_search()]] if root.is_search_visible else [])
                        md_bg_color: root.get_primary_color()
                        shadow_offset: [0, dp(0)]
                        shadow_softness: dp(12)
                        shadow_color: [0, 0, 0, 0.3]
                    BoxLayout:
                        size_hint_y: None
                        height: dp(40) if root.is_search_visible else 0
                        padding: dp(10)
                        MDTextField:
                            id: search_field
                            hint_text: "Search for a song..."
                            size_hint_x: 0.9
                            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                            opacity: 1 if root.is_search_visible else 0
                            on_text: root.search_tracks(self.text)
                            line_color_focus: root.get_primary_color()
                            icon_right: "magnify"
                            icon_right_color: root.get_primary_color()
                    ScrollView:
                        size_hint_y: 1
                        MDGridLayout:
                            id: playlist_list
                            cols: 1
                            size_hint_y: None
                            height: self.minimum_height
                            padding: dp(10)
                            spacing: dp(10)
                            adaptive_height: True
                            canvas.before:
                                Color:
                                    rgba: root.get_bg_color()
                                Rectangle:
                                    pos: self.pos
                                    size: self.size
                    MDCard:
                        id: bottom_bar
                        orientation: 'vertical'
                        size_hint_y: None
                        height: dp(100)
                        padding: 0  # No padding
                        spacing: 0  # No spacing
                        elevation: dp(12)
                        radius: [dp(24), dp(24), 0, 0]
                        md_bg_color: root.get_primary_color()
                        shadow_offset: [0, -dp(2)]
                        shadow_softness: dp(12)
                        shadow_color: [0, 0, 0, 0.3]
                        # Add touch events for swipe up gesture
                        on_touch_down: root.bottom_bar_touch_down(*args)
                        on_touch_up: root.bottom_bar_touch_up(*args)
                        # Progress bar at the very top - now full width
                        MDProgressBar:
                            id: seek_slider_main
                            min: 0
                            max: 100
                            value: 0
                            color: root.get_text_color()
                            size_hint_y: None
                            height: dp(2)  # Very thin progress bar
                            size_hint_x: 1  # Full width
                            pos_hint: {'center_x': 0.5}  # Center horizontally
                        MDLabel:
                            id: current_track_name
                            text: 'No Track Playing'
                            halign: 'center'
                            theme_text_color: "Custom"
                            text_color: root.get_text_color()
                            font_style: 'Subtitle1'
                            bold: True
                            font_name: root.current_font
                            padding: dp(10), dp(10)
                        BoxLayout:
                            orientation: 'horizontal'
                            size_hint_y: None
                            height: dp(50)
                            spacing: dp(10)
                            padding: dp(10), 0, dp(10), dp(10)
                            MDIconButton:
                                icon: 'play' if not root.is_playing else 'pause'
                                theme_text_color: "Custom"
                                text_color: root.get_text_color()
                                on_release: root.toggle_play_only()
                                md_bg_color: [1, 1, 1, 0.1]
                                size_hint_x: None
                                width: dp(48)
                                radius: [dp(24),]
                            BoxLayout:
                                orientation: 'horizontal'
                                size_hint_x: 0.7
                                spacing: dp(2)
                                MDLabel:
                                    id: current_time_main
                                    text: '00:00'
                                    theme_text_color: "Custom"
                                    text_color: root.get_text_color()
                                    font_size: sp(12)
                                    size_hint_x: None
                                    width: dp(40)
                                    halign: 'right'
                                MDLabel:
                                    text: '/'
                                    theme_text_color: "Custom"
                                    text_color: root.get_text_color()
                                    font_size: sp(12)
                                    size_hint_x: None
                                    width: dp(10)
                                    halign: 'center'
                                MDLabel:
                                    id: total_time_main
                                    text: '00:00'
                                    theme_text_color: "Custom"
                                    text_color: root.get_text_color()
                                    font_size: sp(12)
                                    size_hint_x: None
                                    width: dp(40)
                                    halign: 'left'
                            AsyncImage:
                                id: bottom_bar_album_cover
                                source: "default_album_cover.gif"
                                size_hint: None, None
                                size: dp(40), dp(40)
                                radius: [dp(20),]
            NowPlayingScreen:
                name: 'now_playing'
                on_touch_down: self.on_touch_down(args[1])
                on_touch_up: self.on_touch_up(args[1])
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: dp(20)
                    spacing: dp(10)
                    md_bg_color: root.get_bg_color()
                    MDTopAppBar:
                        title: "Now Playing"
                        left_action_items: [["arrow-left", lambda x: root.back_to_main()]]
                        elevation: dp(10)
                        md_bg_color: root.get_primary_color()
                        specific_text_color: root.get_text_color()
                    RelativeLayout:
                        size_hint_y: None
                        height: dp(350)
                        CircularProgressBar:
                            id: circular_progress
                            size_hint: (None, None)
                            size: dp(250), dp(250)
                            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                            color: root.get_primary_color()
                        Image:
                            id: album_cover
                            source: "default_album_cover.gif"
                            anim_delay: 0.1
                            size_hint: (None, None)
                            size: dp(220), dp(220)
                            pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                            canvas.before:
                                Color:
                                    rgba: 1, 1, 1, 1
                                Ellipse:
                                    size: self.size
                                    pos: self.pos
                            canvas.after:
                                Color:
                                    rgba: 0, 0, 0, 0.1
                                Line:
                                    width: dp(2)
                                    circle: [self.center_x, self.center_y, self.width/2 + dp(2)]
                    MDBoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: dp(40)
                        MDLabel:
                            id: now_playing_track_name
                            text: 'No Track Playing'
                            halign: 'center'
                            theme_text_color: "Custom"
                            text_color: root.get_text_color()
                            font_style: 'Subtitle1'
                            font_name: root.current_font
                    MDSlider:
                        id: seek_slider_now_playing
                        min: 0
                        max: 100
                        value: 0
                        color: [0.15, 0.15, 0.15, 1]
                        thumb_color_active: [0.15, 0.15, 0.15, 1]
                        thumb_color_inactive: [0.15, 0.15, 0.15, 1]
                        hint: False
                        on_value: root.on_seek(self.value)
                        on_touch_down: root.start_seek(*args)
                        on_touch_up: root.end_seek(*args)
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: dp(20)
                        MDLabel:
                            id: current_time_now_playing
                            text: '00:00'
                            theme_text_color: "Custom"
                            text_color: root.get_text_color()
                            size_hint_x: None
                            width: dp(50)
                        Widget:
                            size_hint_x: 1
                        MDLabel:
                            id: total_time_now_playing
                            text: '00:00'
                            theme_text_color: "Custom"
                            text_color: root.get_text_color()
                            size_hint_x: None
                            width: dp(50)
                            halign: 'right'
                    BoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: dp(48)
                        spacing: dp(10)
                        padding: dp(20)
                        MDIconButton:
                            icon: 'shuffle' if not root.shuffle else 'shuffle-disabled'
                            theme_text_color: "Custom"
                            text_color: root.get_primary_color() if root.shuffle else root.get_text_color()
                            user_font_size: sp(24)
                            on_release: root.toggle_shuffle()
                            md_bg_color: [1, 1, 1, 0.1] if root.shuffle else [0, 0, 0, 0]
                            radius: [dp(24),]
                            elevation: 1 if root.shuffle else 0
                        MDIconButton:
                            icon: 'skip-previous'
                            theme_text_color: "Custom"
                            text_color: root.get_text_color()
                            user_font_size: sp(24)
                            on_release: root.prev_track()
                            md_bg_color: [1, 1, 1, 0.1]
                            radius: [dp(24),]
                            elevation: 1
                        MDIconButton:
                            icon: 'play' if not root.is_playing else 'pause'
                            theme_text_color: "Custom"
                            text_color: root.get_text_color()
                            user_font_size: sp(36)
                            on_release: root.toggle_play()
                            md_bg_color: root.get_primary_color()
                            radius: [dp(24),]
                            elevation: 2
                            size_hint: None, None
                            size: dp(56), dp(56)
                        MDIconButton:
                            icon: 'skip-next'
                            theme_text_color: "Custom"
                            text_color: root.get_text_color()
                            user_font_size: sp(24)
                            on_release: root.next_track()
                            md_bg_color: [1, 1, 1, 0.1]
                            radius: [dp(24),]
                            elevation: 1
                        MDIconButton:
                            icon: 'repeat' if not root.repeat else 'repeat-once'
                            theme_text_color: "Custom"
                            text_color: root.get_primary_color() if root.repeat else root.get_text_color()
                            user_font_size: sp(24)
                            on_release: root.toggle_repeat()
                            md_bg_color: [1, 1, 1, 0.1] if root.repeat else [0, 0, 0, 0]
                            radius: [dp(24),]
                            elevation: 1 if root.repeat else 0
        MDNavigationDrawer:
            id: nav_drawer
            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(10)
                md_bg_color: root.get_bg_color()
                MDLabel:
                    text: "Settings"
                    font_style: 'H5'
                    theme_text_color: "Custom"
                    text_color: root.get_text_color()
                    size_hint_y: None
                    height: self.texture_size[1]
                MDSeparator:
                    height: dp(1)
                MDRaisedButton:
                    text: "Add Music"
                    theme_text_color: "Custom"
                    text_color: root.get_text_color()
                    md_bg_color: root.get_button_bg_color()
                    on_release: root.show_file_chooser()
                MDSeparator:
                    height: dp(1)
                MDRaisedButton:
                    text: "Select Music Folder"
                    theme_text_color: "Custom"
                    text_color: root.get_text_color()
                    md_bg_color: root.get_button_bg_color()
                    on_release: root.show_folder_chooser()
                MDSeparator:
                    height: dp(1)
                MDRaisedButton:
                    text: "Toggle Theme"
                    theme_text_color: "Custom"
                    text_color: root.get_text_color()
                    md_bg_color: root.get_button_bg_color()
                    on_release: root.toggle_theme()
                MDSeparator:
                    height: dp(1)
                MDRaisedButton:
                    text: "Change Font"
                    theme_text_color: "Custom"
                    text_color: root.get_text_color()
                    md_bg_color: root.get_button_bg_color()
                    on_release: root.show_font_selection_dialog()
                # Display current font name
                MDLabel:
                    text: "Current Font: " + root.get_current_font_name()
                    font_style: "Caption"
                    theme_text_color: "Custom"
                    text_color: root.get_text_color()
                    halign: "center"
                MDSeparator:
                    height: dp(1)
                MDRaisedButton:
                    text: "Exit"
                    theme_text_color: "Custom"
                    text_color: root.get_error_color()
                    md_bg_color: root.get_button_bg_color()
                    on_release: app.stop()
''')


class LeftContainer(ILeftBodyTouch, MDLabel):
    pass


class RightContainer(IRightBodyTouch, MDIconButton):
    pass


class MainScreen(Screen):
    pass


class NowPlayingScreen(Screen):
    touch_start_x = NumericProperty(0)

    def on_touch_down(self, touch):
        # First let the touch propagate to children
        if super(NowPlayingScreen, self).on_touch_down(touch):
            return True
        # Then handle our own logic if the touch wasn't consumed
        if self.collide_point(*touch.pos):
            self.touch_start_x = touch.x
        return False

    def on_touch_up(self, touch):
        # First let the touch propagate to children
        if super(NowPlayingScreen, self).on_touch_up(touch):
            return True
        # Then handle our own logic if the touch wasn't consumed
        if self.collide_point(*touch.pos):
            delta = touch.x - self.touch_start_x
            if abs(delta) > dp(50):  # Minimum swipe threshold
                root_app = MDApp.get_running_app().root
                if delta > 0:
                    root_app.prev_track()
                    root_app.show_swipe_notification("right")
                else:
                    root_app.next_track()
                    root_app.show_swipe_notification("left")
        return False


class CircularProgressBar(ProgressBar):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Reduce thickness to make appearance lighter
        self.thickness = dp(5)
        self.cap_precision = 10
        self.value = 0

    def draw(self):
        with self.canvas:
            self.canvas.clear()
            # Draw background circle (320 degrees from 20 to 340) with higher transparency to make it weaker
            # This leaves an open gap on the right side (40° centered at 0°)
            Color(rgba=(0.8, 0.8, 0.8, 0.15))
            Line(circle=(self.center_x, self.center_y, self.width / 2 - self.thickness / 2, 20, 340),
                 width=self.thickness)
            # Draw progress arc (starting from 20 degrees)
            Color(rgba=self.color)
            end_angle = 20 + (self.value / 100) * 320
            Line(circle=(self.center_x, self.center_y, self.width / 2 - self.thickness / 2, 20, end_angle),
                 width=self.thickness, cap='round')


class LongPressSongItem(OneLineAvatarIconListItem):
    long_press_duration = 1.0  # Duration of long press in seconds
    _lp_event = None
    file_path = StringProperty("")  # Store song path

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._lp_event = Clock.schedule_once(self.trigger_long_press, self.long_press_duration)
        return super(LongPressSongItem, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._lp_event:
            self._lp_event.cancel()
            self._lp_event = None
        return super(LongPressSongItem, self).on_touch_up(touch)

    def trigger_long_press(self, dt):
        # Search upward through parent hierarchy for handle_long_press
        parent = self.parent
        while parent:
            if hasattr(parent, 'handle_long_press'):
                parent.handle_long_press(self)
                break
            parent = parent.parent


class AlbumGridItem(ButtonBehavior, AsyncImage):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(150), dp(150))
        self.radius = [dp(20), ]
        self.elevation = 2
        self.bind(on_release=self.on_press)

    def on_press(self, *args):
        anim = Animation(scale=0.95, duration=0.1) + Animation(scale=1.0, duration=0.1)
        anim.start(self)


class MusicPlayer(BoxLayout):
    playlist = ListProperty()
    favorites = ListProperty()
    current_index = NumericProperty(-1)
    is_playing = BooleanProperty(False)
    sound = ObjectProperty(None)
    seek_scheduled = BooleanProperty(False)
    user_seeking = BooleanProperty(False)
    theme_name = StringProperty("Blue")
    current_font = StringProperty("Roboto")
    is_search_visible = BooleanProperty(False)
    is_favorites_visible = BooleanProperty(False)
    current_pos = NumericProperty(0)
    shuffle = BooleanProperty(False)
    repeat = BooleanProperty(False)
    _bottom_bar_touch_start = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Load saved theme and font if they exist
        self.load_theme()
        self.load_font_preference()
        Clock.schedule_once(self.set_transition, 0)
        Clock.schedule_interval(self.update_progress, 0.1)
        Window.bind(size=self.adjust_layout)
        self._bottom_bar_touch_time = 0
        self._bottom_bar_touch_pos = (0, 0)

        # تحديث الإعدادات المدعومة - توسيع قائمة الصيغ المدعومة
        self.supported_formats = [
            # Common formats
            '.mp3',  # MPEG Layer-3
            '.wav',  # Waveform Audio File
            '.ogg',  # Ogg Vorbis
            '.flac',  # Free Lossless Audio Codec
            '.m4a',  # MPEG-4 Audio
            '.aac',  # Advanced Audio Coding
            '.wma',  # Windows Media Audio
            '.aiff',  # Audio Interchange File Format
            '.alac',  # Apple Lossless Audio Codec
            '.opus',  # Opus Audio Format

            # Additional formats
            '.mp2',  # MPEG Layer-2
            '.mp4',  # MPEG-4 Audio Container
            '.ape',  # Monkey's Audio
            '.mpc',  # Musepack
            '.ac3',  # Dolby Digital
            '.amr',  # Adaptive Multi-Rate
            '.au',  # Sun Audio
            '.mid',  # MIDI
            '.midi',  # MIDI
            '.ra',  # Real Audio
            '.rm',  # Real Media
            '.tta',  # True Audio
            '.dts',  # Digital Theater Systems
            '.spx',  # Speex
            '.gsm',  # GSM
            '.3gp',  # 3GPP container with audio
            '.webm',  # WebM Audio
            '.mka',  # Matroska Audio
            '.dsf',  # DSD Audio
            '.dff',  # DSD Audio
            '.caf',  # Core Audio Format (Apple)
            '.aif',  # Audio Interchange File Format (alternative extension)
            '.aifc'  # Audio Interchange File Format Compressed
        ]
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            ext=self.supported_formats
        )
        self.playlist = self.load_playlist()
        self.favorites = self.load_favorites()
        self.update_playlist_ui()
        Window.bind(on_request_close=self.on_request_close)

        # Set up Android notification action handling
        from kivy.utils import platform
        if platform == 'android':
            self.setup_android_notification_handlers()

    def set_transition(self, dt):
        self.ids.screen_manager.transition = SlideTransition(direction='up')

    def set_screen_transition(self, transition_type='slide', direction='up', duration=0.3):
        """Update screen transition type."""
        transitions = {
            'slide': SlideTransition,
            'fade': FadeTransition,
            'card': CardTransition,
            'swap': SwapTransition
        }
        if transition_type in transitions:
            if transition_type in ['slide', 'card']:
                self.ids.screen_manager.transition = transitions[transition_type](direction=direction,
                                                                                  duration=duration)
            else:
                self.ids.screen_manager.transition = transitions[transition_type](duration=duration)

    def adjust_layout(self, instance, size):
        """Adjust layout based on window size changes"""
        width, height = size

        # تعديل ارتفاع الشريط السفلي ليكون 15% من ارتفاع الشاشة على الأقل 40 dp
        if hasattr(self.ids, 'bottom_bar'):
            new_height = max(dp(40), int(height * 0.15))
            self.ids.bottom_bar.height = new_height

        # Adjust other UI elements based on screen size
        if hasattr(self.ids, 'playlist_list'):
            # Adjust spacing for playlist items
            self.ids.playlist_list.spacing = dp(5) if height < 800 else dp(10)

        # Adjust font sizes for better readability on smaller screens
        if height < 800:
            if hasattr(self.ids, 'current_track_name'):
                self.ids.current_track_name.font_style = 'Body1'
                self.ids.current_track_name.font_size = sp(10)

        # Adjust progress bar height
        if hasattr(self.ids, 'seek_slider_main'):
            self.ids.seek_slider_main.height = dp(1) if height < 800 else dp(4)

        # Adjust album cover size in bottom bar
        if hasattr(self.ids, 'bottom_bar_album_cover'):
            self.ids.bottom_bar_album_cover.size = (dp(32), dp(32)) if height < 800 else (dp(48), dp(48))

    def update_playlist_ui(self):
        """Reconstruct playlist UI items with updated font and proper Arabic text processing."""
        self.ids.playlist_list.clear_widgets()
        playlist_to_display = self.favorites if self.is_favorites_visible else self.playlist
        for index, path in enumerate(playlist_to_display):
            # Create callback functions to avoid closure issues
            def make_play_callback(idx):
                return lambda x: self.play_track_by_index(idx)

            def make_favorite_callback(p):
                return lambda x: self.toggle_favorite(p)

            # Use get_song_title for extracting and processing Arabic text
            song_title = self.get_song_title(path)
            item = LongPressSongItem(
                text=f"{index + 1}. {song_title}",
                theme_text_color="Custom",
                file_path=path,
                on_release=make_play_callback(index)
            )
            # Force update font for Arabic display
            item.font_name = self.current_font
            # Update inner label font for proper Arabic text display
            if hasattr(item, "ids") and "_lbl_primary" in item.ids:
                item.ids._lbl_primary.font_name = self.current_font

            if index == self.current_index:
                item.text_color = [0, 1, 0, 1]
            else:
                item.text_color = self.get_text_color()
            cover_image = AsyncImage(
                source=self.get_album_cover(path),
                size_hint=(None, None),
                size=(dp(40), dp(40)),
                pos_hint={'center_y': 0.5}
            )
            item.add_widget(cover_image)
            favorite_btn = RightContainer(
                icon="heart" if path in self.favorites else "heart-outline",
                on_release=make_favorite_callback(path),
                theme_text_color="Custom",
                text_color=[1, 0, 0, 1] if path in self.favorites else self.get_text_color()  # Red for favorites
            )
            item.add_widget(favorite_btn)
            self.ids.playlist_list.add_widget(item)

    def show_delete_confirmation(self, path):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        def delete_track(permanently=False):
            if path in self.playlist:
                self.playlist.remove(path)
                self.save_playlist()
            if path in self.favorites:
                self.favorites.remove(path)
                self.save_favorites()
            if permanently:
                try:
                    os.remove(path)
                    print(f"Track permanently deleted: {path}")
                except Exception as e:
                    print(f"Error deleting file: {e}")
            self.update_playlist_ui()
            dialog.dismiss()

        dialog = MDDialog(
            title="Confirm Deletion",
            text=f"Do you want to remove '{os.path.basename(path)}'?",
            buttons=[
                MDFlatButton(
                    text="Cancel",
                    theme_text_color="Custom",
                    text_color=self.get_error_color(),
                    on_release=lambda x: dialog.dismiss()
                ),
                MDFlatButton(
                    text="Remove from Playlist",
                    theme_text_color="Custom",
                    text_color=self.get_primary_color(),
                    on_release=lambda x: delete_track(permanently=False)
                ),
                MDFlatButton(
                    text="Delete Permanently",
                    theme_text_color="Custom",
                    text_color=self.get_error_color(),
                    on_release=lambda x: delete_track(permanently=True)
                )
            ]
        )
        dialog.open()

    def get_album_cover(self, path):
        """
        Get album cover for playlist items.
        Extracts cover art from various audio formats and returns the path to the extracted image.
        If no cover art is found, returns the path to the default album cover.
        """
        try:
            file_ext = os.path.splitext(path)[1].lower()
            cover_data = None
            
            # Extract cover art based on file type
            if file_ext == '.mp3':
                try:
                    audio = ID3(path)
                    for key in audio.keys():
                        if key.startswith('APIC:'):
                            cover_data = audio[key].data
                            break
                except Exception as e:
                    print(f"Error extracting MP3 cover: {e}")
                    
            elif file_ext == '.flac':
                try:
                    audio = FLAC(path)
                    if audio.pictures:
                        cover_data = audio.pictures[0].data
                except Exception as e:
                    print(f"Error extracting FLAC cover: {e}")
                    
            elif file_ext in ['.m4a', '.mp4', '.aac']:
                try:
                    audio = MP4(path)
                    if 'covr' in audio:
                        cover_data = audio['covr'][0]
                except Exception as e:
                    print(f"Error extracting MP4 cover: {e}")
                    
            elif file_ext in ['.ogg', '.opus']:
                try:
                    if file_ext == '.ogg':
                        audio = OggVorbis(path)
                    else:
                        audio = OggOpus(path)
                        
                    if 'metadata_block_picture' in audio:
                        import base64
                        import struct
                        picture_data = base64.b64decode(audio['metadata_block_picture'][0])
                        # Skip the header to get the image data
                        offset = 8
                        mime_length = struct.unpack('>I', picture_data[offset:offset + 4])[0]
                        offset += 4 + mime_length
                        desc_length = struct.unpack('>I', picture_data[offset:offset + 4])[0]
                        offset += 4 + desc_length
                        # Skip width, height, color depth, colors used
                        offset += 16
                        data_length = struct.unpack('>I', picture_data[offset:offset + 4])[0]
                        offset += 4
                        cover_data = picture_data[offset:offset + data_length]
                except Exception as e:
                    print(f"Error extracting Ogg/Opus cover: {e}")
                    
            elif file_ext in ['.wma', '.asf']:
                try:
                    audio = ASF(path)
                    for attr in audio.get('WM/Picture', []):
                        cover_data = attr.value
                        break
                except Exception as e:
                    print(f"Error extracting WMA/ASF cover: {e}")

            # Save cover art if found
            if cover_data:
                # Create a unique filename based on the path to avoid conflicts
                import hashlib
                filename = f"cover_{hashlib.md5(path.encode()).hexdigest()}.jpg"
                cover_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
                
                with open(cover_path, "wb") as cover_file:
                    cover_file.write(cover_data)
                return cover_path
            else:
                return "default_album_cover.gif"
        except Exception as e:
            print(f"Error getting album cover: {e}")
            return "default_album_cover.gif"

    def show_now_playing(self):
        if self.current_index != -1:
            self.set_screen_transition('card', 'up')
            self.ids.screen_manager.current = 'now_playing'
            self.update_now_playing_ui()

    def update_now_playing_ui(self):
        if self.current_index != -1:
            track_path = self.playlist[self.current_index]
            self.ids.now_playing_track_name.text = os.path.basename(track_path)
            self.ids.seek_slider_now_playing.max = self.sound.length if self.sound else 100
            self.ids.total_time_now_playing.text = self.format_time(self.sound.length) if self.sound else '00:00'
            self.update_album_cover(track_path)

    def update_album_cover(self, path):
        """
        Extract album cover from various audio formats and update UI elements.
        If no cover art is found, uses the default album cover.
        If a custom cover is found, it will be resized in the Now Playing screen.
        """
        try:
            cover_path = self.get_album_cover(path)
            
            # Update UI with the cover image
            if cover_path != "default_album_cover.gif":
                # We have an actual cover image - resize it in Now Playing screen
                self.ids.album_cover.source = cover_path
                self.ids.album_cover.anim_delay = -1  # Disable animation for image files
                self.ids.album_cover.size = (dp(180), dp(180))  # Smaller size for custom covers
                
                # Bottom bar album cover remains the same size
                self.ids.bottom_bar_album_cover.source = cover_path
                self.ids.bottom_bar_album_cover.anim_delay = -1
            else:
                # Use default animated GIF at original size
                self.ids.album_cover.source = "default_album_cover.gif"
                self.ids.album_cover.anim_delay = 0.1  # Enable animation for GIF
                self.ids.album_cover.size = (dp(220), dp(220))  # Original size for default cover
                
                self.ids.bottom_bar_album_cover.source = "default_album_cover.gif"
                self.ids.bottom_bar_album_cover.anim_delay = 0.1
                
        except Exception as e:
            print(f"Error updating album cover: {e}")
            traceback.print_exc()
            # Fallback to default cover at original size
            self.ids.album_cover.source = "default_album_cover.gif"
            self.ids.album_cover.anim_delay = 0.1
            self.ids.album_cover.size = (dp(220), dp(220))
            self.ids.bottom_bar_album_cover.source = "default_album_cover.gif"
            self.ids.bottom_bar_album_cover.anim_delay = 0.1

    def back_to_main(self):
        # If favorites view is active, simply disable it and update UI.
        if self.is_favorites_visible:
            self.is_favorites_visible = False
            self.ids.top_app_bar.title = "Music Player"
            self.update_playlist_ui()
        else:
            # Otherwise, if we're in a different screen (for instance now_playing)
            self.set_screen_transition('card', 'down')
            self.ids.screen_manager.current = 'main'

    def exit_manager(self, *args):
        self.file_manager.close()

    def show_file_chooser(self):
        self.file_manager.selector = 'file'
        self.file_manager.show('/')

    def show_folder_chooser(self):
        self.file_manager.selector = 'folder'
        self.file_manager.show('/')

    def select_path(self, path):
        self.exit_manager()
        if os.path.isdir(path):
            self.add_folder_to_playlist(path)
        elif os.path.isfile(path):
            self.add_to_playlist([path])

    def add_to_playlist(self, selection):
        if selection:
            for path in selection:
                if path not in self.playlist:
                    self.playlist.append(path)
            self.save_playlist()
            self.update_playlist_ui()

    def add_folder_to_playlist(self, folder_path):
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.supported_formats):
                    file_path = os.path.join(root, file)
                    if file_path not in self.playlist:
                        self.playlist.append(file_path)
        self.save_playlist()
        self.update_playlist_ui()

    def save_playlist(self):
        with open("playlist.json", "w") as file:
            json.dump(self.playlist, file)

    def load_playlist(self):
        if os.path.exists("playlist.json"):
            with open("playlist.json", "r") as file:
                return json.load(file)
        return []

    def save_favorites(self):
        with open("favorites.json", "w") as file:
            json.dump(self.favorites, file)

    def load_favorites(self):
        if os.path.exists("favorites.json"):
            with open("favorites.json", "r") as file:
                return json.load(file)
        return []

    def toggle_favorite(self, path):
        if path in self.favorites:
            self.favorites.remove(path)
        else:
            self.favorites.append(path)
        self.save_favorites()
        self.update_playlist_ui()

    def play_track_by_index(self, index):
        playlist_to_play = self.favorites if self.is_favorites_visible else self.playlist
        if 0 <= index < len(playlist_to_play):
            self.current_index = index
            self.play_track(playlist_to_play[index])
            self.update_playlist_ui()

    def play_track(self, path):
        if self.sound:
            self.sound.stop()
            self.sound.unload()
        try:
            self.sound = SoundLoader.load(path)
            if self.sound:
                self.sound.play()
                self.is_playing = True
                # Use song title from metadata for display
                song_title = self.get_song_title(path)
                self.ids.current_track_name.text = song_title
                self.ids.now_playing_track_name.text = song_title
                self.update_metadata(path)
                self.update_album_cover(path)

                # Update media notification for the new track
                from kivy.utils import platform
                if platform == 'android':
                    self.update_media_notification()
            else:
                self.show_format_error_dialog(path)
        except Exception as e:
            print(f"Error playing track: {e}")
            traceback.print_exc()
            self.show_format_error_dialog(path)

    def update_metadata(self, path):
        """Extract metadata from various audio formats"""
        try:
            file_ext = os.path.splitext(path)[1].lower()
            duration = 0

            # Extract metadata based on file type
            if file_ext == '.mp3':
                audio = MP3(path)
                duration = audio.info.length
            elif file_ext == '.flac':
                audio = FLAC(path)
                duration = audio.info.length
            elif file_ext == '.ogg':
                audio = OggVorbis(path)
                duration = audio.info.length
            elif file_ext == '.opus':
                audio = OggOpus(path)
                duration = audio.info.length
            elif file_ext in ['.m4a', '.mp4', '.aac']:
                audio = MP4(path)
                duration = audio.info.length
            elif file_ext in ['.wma', '.asf']:
                audio = ASF(path)
                duration = audio.info.length
            elif file_ext in ['.wav']:
                try:
                    audio = WAVE(path)
                    duration = audio.info.length
                except:
                    # Fallback for some WAV files
                    if self.sound:
                        duration = self.sound.length
            elif file_ext in ['.aiff', '.aif', '.aifc']:
                try:
                    audio = AIFF(path)
                    duration = audio.info.length
                except:
                    # Fallback
                    if self.sound:
                        duration = self.sound.length
            else:
                # For other formats, try to get duration from SoundLoader
                if self.sound:
                    duration = self.sound.length

            # Update UI with duration
            self.ids.total_time_main.text = self.format_time(duration)
            self.ids.total_time_now_playing.text = self.format_time(duration)
            self.ids.seek_slider_main.max = 100  # Always use percentage for progress bar
            self.ids.seek_slider_now_playing.max = duration if duration > 0 else 100

        except Exception as e:
            print(f"Error extracting metadata: {e}")
            traceback.print_exc()
            # Fallback to SoundLoader's duration if available
            if self.sound and self.sound.length > 0:
                duration = self.sound.length
                self.ids.total_time_main.text = self.format_time(duration)
                self.ids.total_time_now_playing.text = self.format_time(duration)
                self.ids.seek_slider_main.max = 100
                self.ids.seek_slider_now_playing.max = duration

    def toggle_play(self):
        """Toggle play/pause and open Now Playing screen."""
        self.toggle_play_only()
        # Show now playing screen when toggling play from UI
        if self.sound and self.is_playing:
            self.show_now_playing()

    def toggle_play_only(self):
        """Toggle play/pause without opening Now Playing screen."""
        if self.sound:
            if self.is_playing:
                self.current_pos = self.sound.get_pos()
                self.sound.stop()
                self.is_playing = False
            else:
                self.sound.play()
                self.sound.seek(self.current_pos)
                self.is_playing = True

            # Update media notification after changing playback state
            from kivy.utils import platform
            if platform == 'android':
                self.update_media_notification()

    def next_track(self):
        playlist_to_play = self.favorites if self.is_favorites_visible else self.playlist
        if playlist_to_play:
            if self.shuffle:
                import random
                self.current_index = random.randint(0, len(playlist_to_play) - 1)
            else:
                self.current_index = (self.current_index + 1) % len(playlist_to_play)
            self.play_track(playlist_to_play[self.current_index])
            self.update_playlist_ui()

            # Update media notification after changing track
            from kivy.utils import platform
            if platform == 'android':
                self.update_media_notification()

            # Update media notification after changing track
            from kivy.utils import platform
            if platform == 'android':
                self.update_media_notification()

    def prev_track(self):
        playlist_to_play = self.favorites if self.is_favorites_visible else self.playlist
        if playlist_to_play:
            if self.shuffle:
                import random
                self.current_index = random.randint(0, len(playlist_to_play) - 1)
            else:
                self.current_index = (self.current_index - 1) % len(playlist_to_play)
            self.play_track(playlist_to_play[self.current_index])
            self.update_playlist_ui()

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        print(f"Shuffle is now {'ON' if self.shuffle else 'OFF'}")

    def toggle_repeat(self):
        self.repeat = not self.repeat
        print(f"Repeat is now {'ON' if self.repeat else 'OFF'}")

    def update_progress(self, dt):
        if self.sound and self.sound.state == 'play' and not self.user_seeking:
            current_pos = self.sound.get_pos()
            if current_pos >= 0:
                # Update progress bar instead of slider
                self.ids.seek_slider_main.value = (
                                                          current_pos / self.sound.length) * 100 if self.sound.length > 0 else 0
                self.ids.current_time_main.text = self.format_time(current_pos)
                self.ids.circular_progress.value = (current_pos / self.sound.length) * 100
                self.ids.circular_progress.draw()
                if self.ids.screen_manager.current == 'now_playing':
                    self.ids.seek_slider_now_playing.value = current_pos
                    self.ids.current_time_now_playing.text = self.format_time(current_pos)

                # Check if track has finished
                if current_pos >= self.sound.length - 0.5:
                    self.on_track_finish()

    def start_seek(self, *args):
        instance = args[0]
        touch = args[1]
        if instance.collide_point(*touch.pos):
            self.user_seeking = True
            return True
        return False

    def end_seek(self, *args):
        instance = args[0]
        touch = args[1]
        if instance.collide_point(*touch.pos) and self.user_seeking and self.sound:
            try:
                new_val = instance.value
                self.sound.seek(new_val)
                self.ids.current_time_main.text = self.format_time(new_val)
                if self.ids.screen_manager.current == 'now_playing':
                    self.ids.current_time_now_playing.text = self.format_time(new_val)
            except Exception as e:
                print(f"Error seeking position: {e}")
            finally:
                self.user_seeking = False
            return True
        return False

    def on_seek(self, value):
        # Only seek when user is actively seeking
        if self.user_seeking and self.sound:
            try:
                self.sound.seek(value)
                self.ids.current_time_main.text = self.format_time(value)
                if self.ids.screen_manager.current == 'now_playing':
                    self.ids.current_time_now_playing.text = self.format_time(value)
            except Exception as e:
                print(f"Error seeking (on_value): {e}")

    def format_time(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        return f"{int(minutes):02}:{int(seconds):02}"

    def get_text_color(self):
        # Improved text contrast for better readability
        app = MDApp.get_running_app()
        if app.theme_cls.theme_style == "Dark":
            return [1, 1, 1, 1]
        else:
            return [0.13, 0.13, 0.13, 1]

    def get_bg_color(self):
        # Refined background colors with better contrast
        app = MDApp.get_running_app()
        if app.theme_cls.theme_style == "Dark":
            return [0.12, 0.12, 0.12, 1]
        else:
            return [0.95, 0.95, 0.95, 1]

    def get_card_bg_color(self):
        # Card backgrounds with subtle elevation effect
        app = MDApp.get_running_app()
        if app.theme_cls.theme_style == "Dark":
            return [0.18, 0.18, 0.18, 1]
        else:
            return [1, 1, 1, 1]

    def get_button_bg_color(self):
        # Button backgrounds with better contrast
        app = MDApp.get_running_app()
        if app.theme_cls.theme_style == "Dark":
            return [0.25, 0.25, 0.25, 1]
        else:
            return [0.9, 0.9, 0.9, 1]

    def get_primary_color(self):
        app = MDApp.get_running_app()
        return app.theme_cls.primary_color

    def get_error_color(self):
        app = MDApp.get_running_app()
        return app.theme_cls.error_color

    def toggle_theme(self):
        """Show a dialog to select a theme instead of cycling through them."""
        self.show_theme_selection_dialog()

    def show_theme_selection_dialog(self):
        """Display a dialog with theme options for selection."""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.list import OneLineAvatarIconListItem
        from kivymd.uix.button import MDFlatButton

        # Available themes with their display names and color codes
        themes = [
            {"name": "DeepPurple", "display": "Deep Purple", "color": [0.4, 0.2, 0.6, 1]},
            {"name": "Teal", "display": "Teal", "color": [0, 0.6, 0.6, 1]},
            {"name": "Indigo", "display": "Indigo", "color": [0.25, 0.31, 0.71, 1]},
            {"name": "BlueGray", "display": "Blue Gray", "color": [0.38, 0.49, 0.55, 1]},
            {"name": "Orange", "display": "Orange", "color": [1, 0.6, 0, 1]},
            {"name": "Red", "display": "Red", "color": [0.9, 0.2, 0.2, 1]},
            {"name": "Pink", "display": "Pink", "color": [0.91, 0.12, 0.39, 1]},
            {"name": "Purple", "display": "Purple", "color": [0.55, 0.14, 0.59, 1]},
            {"name": "Blue", "display": "Blue", "color": [0.13, 0.59, 0.95, 1]},
            {"name": "LightBlue", "display": "Light Blue", "color": [0.01, 0.66, 0.96, 1]},
            {"name": "Cyan", "display": "Cyan", "color": [0, 0.74, 0.83, 1]},
            {"name": "Green", "display": "Green", "color": [0.3, 0.69, 0.31, 1]},
            {"name": "LightGreen", "display": "Light Green", "color": [0.55, 0.76, 0.29, 1]},
            {"name": "Lime", "display": "Lime", "color": [0.8, 0.86, 0.22, 1]},
            {"name": "Yellow", "display": "Yellow", "color": [1, 0.92, 0.23, 1]},
            {"name": "Amber", "display": "Amber", "color": [1, 0.76, 0.03, 1]},
            {"name": "Brown", "display": "Brown", "color": [0.47, 0.33, 0.28, 1]},
            {"name": "Gray", "display": "Gray", "color": [0.62, 0.62, 0.62, 1]}
        ]

        class ThemeItem(OneLineAvatarIconListItem):
            divider = None

            def __init__(self, theme_data, **kwargs):
                super().__init__(**kwargs)
                self.theme_data = theme_data
                self.text = theme_data["display"]

                # Add a color circle to show the theme color
                from kivymd.uix.behaviors import CircularRippleBehavior
                from kivy.uix.behaviors import ButtonBehavior
                from kivy.uix.widget import Widget
                from kivy.graphics import Color, Ellipse

                class ColorCircle(CircularRippleBehavior, ButtonBehavior, Widget):
                    def __init__(self, **kwargs):
                        self.theme_color = kwargs.pop('color', [1, 1, 1, 1])
                        super().__init__(**kwargs)
                        self.size_hint = (None, None)
                        self.size = (dp(30), dp(30))
                        # Schedule drawing after initialization is complete
                        Clock.schedule_once(self.draw_circle, 0)

                    def draw_circle(self, *args):
                        self.canvas.before.clear()
                        with self.canvas.before:
                            Color(*self.theme_color)
                            Ellipse(pos=self.pos, size=self.size)

                    def on_size(self, *args):
                        self.draw_circle()

                    def on_pos(self, *args):
                        self.draw_circle()

                color_circle = ColorCircle(color=theme_data["color"])
                self.add_widget(color_circle)

        # Create theme items
        theme_items = []
        for theme in themes:
            def make_select_callback(theme_name):
                return lambda x: self.apply_theme(theme_name)

            item = ThemeItem(
                theme_data=theme,
                on_release=make_select_callback(theme["name"])
            )
            theme_items.append(item)

        dialog = MDDialog(
            title="Select Theme",
            type="simple",
            items=theme_items,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=self.get_primary_color(),
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )

        # Store dialog reference to prevent garbage collection
        self._theme_dialog = dialog
        dialog.open()

    def save_theme(self):
        """Save the current theme setting to a JSON file."""
        try:
            with open("theme.json", "w", encoding="utf-8") as file:
                json.dump({"theme_name": self.theme_name}, file)
            print(f"Theme saved: {self.theme_name}")
        except Exception as e:
            print(f"Error saving theme: {e}")

    def save_font_preference(self):
        """Save the current font preference to a JSON file."""
        try:
            with open("font_preference.json", "w", encoding="utf-8") as file:
                json.dump({"font_path": self.current_font}, file)
            print(f"Font preference saved: {self.current_font}")
        except Exception as e:
            print(f"Error saving font preference: {e}")

    def load_font_preference(self):
        """Load the font preference from a JSON file if it exists."""
        default_font = "Roboto"
        if os.path.exists("font_preference.json"):
            try:
                with open("font_preference.json", "r", encoding="utf-8") as file:
                    data = json.load(file)
                font_path = data.get("font_path", self.current_font)
                # Verify that the font file exists; if not, use the default font.
                if os.path.exists(font_path):
                    self.current_font = font_path
                    print(f"Font preference loaded: {self.current_font}")
                else:
                    print(f"Font file not found: {font_path}, using default font")
                    self.current_font = default_font
            except Exception as e:
                print(f"Error loading font preference: {e}")
                self.current_font = default_font
        else:
            # If no preference file exists, verify the current_font value.
            if not os.path.exists(self.current_font) and self.current_font != default_font:
                print(f"Font file {self.current_font} not found; setting default font")
                self.current_font = default_font

    def load_theme(self):
        """Load the theme setting from a JSON file if it exists and update UI."""
        if os.path.exists("theme.json"):
            try:
                with open("theme.json", "r", encoding="utf-8") as file:
                    data = json.load(file)
                self.theme_name = data.get("theme_name", self.theme_name)
                app = MDApp.get_running_app()
                if app:
                    app.theme_cls.primary_palette = self.theme_name
                # Ensure the updated theme applies to all UI components (e.g., bottom bar)
                self.update_theme()
                print(f"Theme loaded: {self.theme_name}")
            except Exception as e:
                print(f"Error loading theme: {e}")

    def apply_theme(self, theme_name):
        """Apply the selected theme, update UI and save the setting."""
        self.theme_name = theme_name
        app = MDApp.get_running_app()
        app.theme_cls.primary_palette = self.theme_name
        self.update_theme()
        # Save the theme
        self.save_theme()

        # Dismiss the dialog if it exists
        if hasattr(self, '_theme_dialog') and self._theme_dialog:
            self._theme_dialog.dismiss()
            self._theme_dialog = None

    def update_theme(self):
        app = MDApp.get_running_app()
        app.theme_cls.primary_palette = self.theme_name
        # Update font for all text elements to support Arabic
        if hasattr(self.ids, 'current_track_name'):
            self.ids.current_track_name.font_name = self.current_font
            self.ids.current_track_name.text_color = self.get_text_color()
        if hasattr(self.ids, 'now_playing_track_name'):
            self.ids.now_playing_track_name.font_name = self.current_font
            self.ids.now_playing_track_name.text_color = self.get_text_color()
        for child in self.ids.playlist_list.children:
            child.text_color = self.get_text_color()
            # Apply font to list items if they have text property
            if hasattr(child, 'font_name'):
                child.font_name = self.current_font
        self.ids.seek_slider_main.color = self.get_primary_color()
        self.ids.nav_drawer.md_bg_color = self.get_bg_color()
        self.ids.bottom_bar.md_bg_color = self.get_primary_color()

    def toggle_search(self):
        self.is_search_visible = not self.is_search_visible
        self.ids.top_app_bar.right_action_items = [
            ["heart", lambda x: self.show_favorites()],
            ["magnify", lambda x: self.toggle_search()],
            *([["close", lambda x: self.toggle_search()]] if self.is_search_visible else [])
        ]

    def search_tracks(self, query):
        """Filter and display tracks based on the search query using updated Arabic text display."""
        self.ids.playlist_list.clear_widgets()
        if query.strip():
            filtered_playlist = [path for path in self.playlist if query.lower() in self.get_song_title(path).lower()]
        else:
            filtered_playlist = self.playlist

        for index, path in enumerate(filtered_playlist):
            def make_play_callback(idx):
                return lambda x: self.play_track_by_index(idx)

            def make_favorite_callback(p):
                return lambda x: self.toggle_favorite(p)

            def make_delete_callback(p):
                return lambda x: self.show_delete_confirmation(p)

            song_title = self.get_song_title(path)
            item = OneLineAvatarIconListItem(
                text=f"{index + 1}. {song_title}",
                theme_text_color="Custom",
                on_release=make_play_callback(index)
            )
            # Set font to current_font for proper Arabic text display
            item.font_name = self.current_font
            # Update inner label font for proper Arabic text display
            if hasattr(item, "ids") and "_lbl_primary" in item.ids:
                item.ids._lbl_primary.font_name = self.current_font

            if index == self.current_index:
                item.text_color = [0, 1, 0, 1]
            else:
                item.text_color = self.get_text_color()
            item.add_widget(LeftContainer(text=str(index + 1)))
            favorite_btn = RightContainer(
                icon="heart" if path in self.favorites else "heart-outline",
                on_release=make_favorite_callback(path),
                theme_text_color="Custom",
                text_color=[1, 0, 0, 1] if path in self.favorites else self.get_text_color()
            )
            item.add_widget(favorite_btn)
            delete_btn = RightContainer(
                icon="trash-can",
                on_release=make_delete_callback(path)
            )
            # Shift delete button to the left
            delete_btn.pos_hint = {'center_x': 0.3}
            item.add_widget(delete_btn)
            self.ids.playlist_list.add_widget(item)

    def show_favorites(self):
        self.is_favorites_visible = not self.is_favorites_visible
        self.ids.top_app_bar.title = "Favorites" if self.is_favorites_visible else "Music Player"
        self.update_playlist_ui()

    def show_format_error_dialog(self, path):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton
        dialog = MDDialog(
            title="Format Error",
            text=f"The file '{os.path.basename(path)}' is not supported.",
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=self.get_primary_color(),
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def on_track_finish(self):
        if self.repeat:
            self.play_track_by_index(self.current_index)
        else:
            self.next_track()

    def on_request_close(self, *args, **kwargs):
        # Returning False allows the application to close gracefully.
        return False

    def setup_android_notification_handlers(self):
        """Set up handlers for Android notification actions."""
        from kivy.utils import platform
        if platform != 'android':
            print("Android notification handlers not set up: not running on Android.")
            return
        try:
            # Import jnius safely
            try:
                from jnius import autoclass
            except ImportError:
                print("pyjnius module not found; Android functionality disabled.")
                return

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity

            # Register a broadcast receiver to handle notification actions
            try:
                from android.broadcast import BroadcastReceiver
            except ImportError:
                print("android.broadcast module not found; skipping Android broadcast receiver setup.")
                return

            class MusicControlReceiver(BroadcastReceiver):
                def __init__(self, music_player):
                    super(MusicControlReceiver, self).__init__()
                    self.music_player = music_player

                def onReceive(self, context, intent):
                    action = intent.getAction()
                    if action == "ACTION_PLAY_PAUSE":
                        self.music_player.toggle_play_only()
                    elif action == "ACTION_NEXT":
                        self.music_player.next_track()
                    elif action == "ACTION_PREVIOUS":
                        self.music_player.prev_track()

            # Create and register the receiver
            self.receiver = MusicControlReceiver(self)
            self.receiver.register()

            print("Android notification handlers set up successfully")
        except Exception as e:
            print(f"Error setting up Android notification handlers: {e}")
            import traceback
            traceback.print_exc()

    def bottom_bar_touch_down(self, instance, touch):
        """Handle touch down event on bottom bar for swipe up gesture and taps."""
        if instance.collide_point(*touch.pos):
            self._bottom_bar_touch_start = touch.y
            # Store the touch position and time for tap detection
            self._bottom_bar_touch_pos = touch.pos
            self._bottom_bar_touch_time = Clock.get_time()
            return True
        return False

    def bottom_bar_touch_up(self, instance, touch):
        """Handle touch up event on bottom bar for swipe up gesture and taps."""
        if instance.collide_point(*touch.pos):
            # Check if the touch is on or near the play/pause button area
            for child in instance.children:
                if isinstance(child, BoxLayout):  # Find the BoxLayout containing the play button
                    for subchild in child.children:
                        if isinstance(subchild, MDIconButton) and subchild.icon in ['play', 'pause']:
                            # Create a larger hit area around the button
                            button_x, button_y = subchild.pos
                            button_width, button_height = subchild.size
                            # Extend the hit area by 20dp in each direction
                            extended_area = [
                                button_x - dp(20),
                                button_y - dp(20),
                                button_width + dp(40),
                                button_height + dp(40)
                            ]
                            # Check if touch is within the extended area
                            if (extended_area[0] <= touch.pos[0] <= extended_area[0] + extended_area[2] and
                                    extended_area[1] <= touch.pos[1] <= extended_area[1] + extended_area[3]):
                                # If touch is in extended button area, don't open Now Playing
                                return True

            # Calculate time difference to distinguish between tap and swipe
            time_diff = Clock.get_time() - self._bottom_bar_touch_time
            delta_y = touch.y - self._bottom_bar_touch_start

            # If it's a quick tap (less than 0.3 seconds) with minimal movement
            if time_diff < 0.3 and abs(delta_y) < dp(10):
                self.show_now_playing()
                return True

            # If there's an upward swipe of sufficient distance
            elif delta_y < -dp(50):  # Negative for upward swipe
                self.show_now_playing()
                return True

            return True
        return False

    def on_bottom_bar_click(self, instance):
        """Handle direct clicks on the bottom bar."""
        # Check if the click is on the album cover or track name
        if hasattr(instance, 'id'):
            if instance.id in ['bottom_bar_album_cover', 'current_track_name']:
                self.show_now_playing()
            else:
                # For other parts of the bottom bar, just toggle play
                self.toggle_play_only()

    def show_swipe_notification(self, direction):
        pass

    def show_background_playback_status(self):
        pass

    def update_media_notification(self):
        """
        Update or create a media control notification in Android.
        This method uses pyjnius to access Android's Notification APIs.
        """
        from kivy.utils import platform
        if platform != 'android':
            return

        try:
            # Import jnius safely
            try:
                from jnius import autoclass, cast
            except ImportError:
                print("pyjnius module not found; cannot update media notification.")
                return

            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Intent = autoclass('android.content.Intent')
            PendingIntent = autoclass('android.app.PendingIntent')
            NotificationManagerCompat = autoclass('androidx.core.app.NotificationManagerCompat')
            NotificationCompatBuilder = autoclass('androidx.core.app.NotificationCompat$Builder')
            Context = autoclass('android.content.Context')
            NotificationChannel = autoclass('android.app.NotificationChannel')
            NotificationManager = autoclass('android.app.NotificationManager')
            Build = autoclass('android.os.Build')

            # Get the current activity
            activity = PythonActivity.mActivity

            # Create notification channel for Android O and above
            if Build.VERSION.SDK_INT >= Build.VERSION_CODES.O:
                channel_id = "music_player_channel"
                channel_name = "Music Player Controls"
                channel_description = "Media controls for Music Player"
                importance = NotificationManager.IMPORTANCE_LOW  # Low importance to avoid sound

                channel = NotificationChannel(channel_id, channel_name, importance)
                channel.setDescription(channel_description)

                # Register the channel with the system
                notification_manager = activity.getSystemService(Context.NOTIFICATION_SERVICE)
                notification_manager.createNotificationChannel(channel)
            else:
                # For older Android versions
                channel_id = "music_player_channel"

            # Create intents for media control actions
            # Play/Pause intent
            playIntent = Intent(activity, PythonActivity)
            playIntent.setAction("ACTION_PLAY_PAUSE")
            playPendingIntent = PendingIntent.getActivity(
                activity, 0, playIntent, PendingIntent.FLAG_UPDATE_CURRENT
            )

            # Next track intent
            nextIntent = Intent(activity, PythonActivity)
            nextIntent.setAction("ACTION_NEXT")
            nextPendingIntent = PendingIntent.getActivity(
                activity, 1, nextIntent, PendingIntent.FLAG_UPDATE_CURRENT
            )

            # Previous track intent
            prevIntent = Intent(activity, PythonActivity)
            prevIntent.setAction("ACTION_PREVIOUS")
            prevPendingIntent = PendingIntent.getActivity(
                activity, 2, prevIntent, PendingIntent.FLAG_UPDATE_CURRENT
            )

            # Create the notification
            builder = NotificationCompatBuilder(activity, channel_id)
            builder.setSmallIcon(activity.getApplicationInfo().icon)

            # Set notification content based on current track
            current_song = "No Track" if self.current_index == -1 else self.get_song_title(
                self.favorites[self.current_index] if self.is_favorites_visible else self.playlist[self.current_index]
            )
            builder.setContentTitle("Music Player")
            builder.setContentText("Now Playing: " + current_song)
            builder.setOngoing(self.is_playing)  # Persistent notification while playing

            # Add media control buttons
            builder.addAction(0, "Previous", prevPendingIntent)
            if self.is_playing:
                builder.addAction(0, "Pause", playPendingIntent)
            else:
                builder.addAction(0, "Play", playPendingIntent)
            builder.addAction(0, "Next", nextPendingIntent)

            # Set notification style for media controls
            MediaStyle = autoclass('androidx.media.app.NotificationCompat$MediaStyle')
            style = MediaStyle()
            style.setShowActionsInCompactView(0, 1, 2)  # Show all three actions in compact view
            builder.setStyle(style)

            # Display the notification
            notificationManager = NotificationManagerCompat.from_(activity)
            notification_id = 1001  # Unique ID for this notification
            notificationManager.notify(notification_id, builder.build())

        except Exception as e:
            print(f"Error updating media notification: {e}")
            import traceback
            traceback.print_exc()

    def stop_background_playback(self):
        if self.sound:
            self.sound.stop()
        self.is_playing = False

        # Clear notification when stopping playback
        from kivy.utils import platform
        if platform == 'android':
            try:
                try:
                    from jnius import autoclass
                except ImportError:
                    print("pyjnius module not found; cannot clear notification.")
                    return

                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Context = autoclass('android.content.Context')
                NotificationManagerCompat = autoclass('androidx.core.app.NotificationManagerCompat')

                activity = PythonActivity.mActivity
                notificationManager = NotificationManagerCompat.from_(activity)
                notificationManager.cancel(1001)  # Use the same ID as in update_media_notification
            except Exception as e:
                print(f"Error clearing notification: {e}")

    def update_album_grid(self):
        self.ids.album_grid.clear_widgets()
        for album in self.albums:
            item = AlbumGridItem(
                source=album['cover'],
                on_release=lambda x, a=album: self.show_album_details(a)
            )
            self.ids.album_grid.add_widget(item)

    def get_song_title(self, path):
        """Extract the song title using mutagen's interface and fix Arabic text by reshaping and reordering.
        Falls back to ID3 tags for MP3 or to the filename if no metadata is available.
        """
        result = None
        try:
            # Try to get title from easy interface (works for many formats)
            audio = File(path, easy=True)
            if audio and audio.get('title'):
                title_data = audio.get('title')
                if isinstance(title_data, list) and title_data[0]:
                    result = title_data[0]
                elif isinstance(title_data, str):
                    result = title_data
        except Exception as e:
            print(f"Error extracting title from easy interface for {path}: {e}")

        # For MP3 files, try using ID3 if no title was found from easy interface
        if not result and os.path.splitext(path)[1].lower() == '.mp3':
            try:
                id3 = ID3(path)
                title_tag = id3.get('TIT2')
                if title_tag and title_tag.text:
                    result = title_tag.text[0]
            except Exception as e:
                print(f"Error reading ID3 tags for {path}: {e}")

        # Fallback: Use filename if no title was successfully extracted
        if not result:
            result = os.path.basename(path)

        # Ensure the result is a Unicode string
        if not isinstance(result, str):
            try:
                result = result.decode('utf-8', errors='replace')
            except Exception as decode_err:
                print(f"Decoding error for title in {path}: {decode_err}")
                result = str(result)

        # Always apply Arabic reshaping and correct bidirectional ordering
        try:
            reshaped_text = arabic_reshaper.reshape(result)
            display_text = get_display(reshaped_text)
        except Exception as e:
            print(f"Error reshaping Arabic text for {path}: {e}")
            display_text = result

        return display_text

    def get_system_fonts(self):
        """Extract available fonts from the custom fonts directory only."""
        import os
        fonts = {}
        custom_fonts_dir = r"D:\python\PythonProject1\fonts"
        if os.path.isdir(custom_fonts_dir):
            for root_dir, dirs, files in os.walk(custom_fonts_dir):
                for file in files:
                    if file.lower().endswith(('.ttf', '.otf')):
                        font_name = os.path.splitext(file)[0]
                        full_path = os.path.join(root_dir, file)
                        fonts[font_name] = full_path
        # Return sorted list by font name
        return sorted(fonts.items(), key=lambda x: x[0])

    def get_current_font_name(self):
        """Get the name of the current font file without the full path."""
        import os
        return os.path.basename(self.current_font)

    def show_font_selection_dialog(self):
        """Display font selection dialog using system installed fonts."""
        from kivymd.uix.dialog import MDDialog
        self.system_fonts = self.get_system_fonts()
        font_items = []
        for font_name, font_path in self.system_fonts:
            # Use FontSelectionItem instead of OneLineListItem to avoid KeyError in MDDialog
            item = FontSelectionItem(
                text=font_name,
                on_release=lambda x, fn=font_path: self.apply_font(fn)
            )
            font_items.append(item)

        self._font_dialog = MDDialog(
            title="Select Font",
            type="simple",
            items=font_items,
            buttons=[
                # Cancel button to close dialog
                MDFlatButton(
                    text="CANCEL",
                    theme_text_color="Custom",
                    text_color=self.get_primary_color(),
                    on_release=lambda x: self._font_dialog.dismiss()
                )
            ]
        )
        self._font_dialog.open()

    def apply_font(self, font_path):
        """Apply selected font to the interface and store the font file path in current_font property."""
        # Verify font existence before applying
        if os.path.exists(font_path):
            self.current_font = font_path
        else:
            print(f"Font file {font_path} not found, using default font")
            self.current_font = "Roboto"
        app = MDApp.get_running_app()
        # Update main track name label
        if hasattr(self, 'ids'):
            if 'current_track_name' in self.ids:
                self.ids.current_track_name.font_name = self.current_font
            # Update Now Playing screen track name
            if 'now_playing_track_name' in self.ids:
                self.ids.now_playing_track_name.font_name = self.current_font
        self._font_dialog.dismiss()
        # Save font preference
        self.save_font_preference()
        # Update theme to refresh text widgets across the interface
        self.update_theme()
        # Update playlist UI to apply font to all song items
        self.update_playlist_ui()
        print(f"Font applied: {self.current_font}")

    def handle_long_press(self, song_item):
        """Handle long press on song item by showing options dialog.
        Ensures Arabic text is displayed correctly in the dialog.
        """

        def delete_action(instance):
            self.show_delete_confirmation(song_item.file_path)
            dialog.dismiss()

        def toggle_favorite_action(instance):
            self.toggle_favorite(song_item.file_path)
            dialog.dismiss()

        def details_action(instance):
            self.show_song_details(song_item.file_path)
            dialog.dismiss()

        dialog = MDDialog(
            title="Song Options",
            text=f"Options for: {os.path.basename(song_item.file_path)}",
            buttons=[
                MDFlatButton(
                    text="Delete",
                    theme_text_color="Custom",
                    text_color=self.get_error_color(),
                    on_release=delete_action
                ),
                MDFlatButton(
                    text="Toggle Favorite",
                    theme_text_color="Custom",
                    text_color=self.get_primary_color(),
                    on_release=toggle_favorite_action
                ),
                MDFlatButton(
                    text="Details",
                    theme_text_color="Custom",
                    text_color=self.get_primary_color(),
                    on_release=details_action
                )
            ]
        )
        dialog.open()

    def show_song_details(self, path):
        """Show song details in a dialog.
        Ensures Arabic text is displayed correctly in the dialog.
        """
        try:
            audio = MP3(path)
            # Use the get_song_title method for consistent title extraction
            title = self.get_song_title(path)

            # Try to get ID3 tags if available
            try:
                tags = ID3(path)
                # Process artist and album names for Arabic text
                artist_raw = str(tags.get('TPE1', 'Unknown Artist'))
                album_raw = str(tags.get('TALB', 'Unknown Album'))

                # Reshape and reorder Arabic text
                artist = get_display(arabic_reshaper.reshape(artist_raw))
                album = get_display(arabic_reshaper.reshape(album_raw))
            except:
                artist = 'Unknown Artist'
                album = 'Unknown Album'

            info = f"Title: {title}\n" \
                   f"Artist: {artist}\n" \
                   f"Album: {album}\n" \
                   f"Duration: {self.format_time(audio.info.length)}\n" \
                   f"Bitrate: {int(audio.info.bitrate / 1000)} kbps\n" \
                   f"Sample Rate: {audio.info.sample_rate} Hz"

            if path in self.favorites:
                info += "\n\nThis song is in your favorites ❤️"
        except Exception as e:
            info = f"Error getting details: {str(e)}"

        dialog = MDDialog(
            title="Song Details",
            text=info,
            buttons=[
                MDFlatButton(
                    text="OK",
                    theme_text_color="Custom",
                    text_color=self.get_primary_color(),
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    @mainthread
    def update(self, dt):
        if self.sound and self.sound.state == 'play':
            current_time = self.sound.get_pos()
            self.ids.seek_slider_now_playing.value = current_time


class MusicPlayerApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Modern color palette with DeepPurple primary and Amber accent
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.material_style = "M3"

    def build(self):
        return MusicPlayer()

from kivy.core.window import Window

Window.size = (360, 640)

if __name__ == '__main__':
    MusicPlayerApp().run()
