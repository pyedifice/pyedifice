from __future__ import annotations

import typing as tp

from edifice.qt import QT_VERSION

if QT_VERSION == "PyQt6" and not tp.TYPE_CHECKING:
    from PyQt6 import QtCore
    from PyQt6.QtCore import QUrl
    from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
    from PyQt6.QtMultimediaWidgets import QVideoWidget
else:
    from PySide6 import QtCore
    from PySide6.QtCore import QUrl
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
    from PySide6.QtMultimediaWidgets import QVideoWidget

from edifice import Element, QtWidgetElement
from edifice.engine import CommandType, PropsDict, _WidgetTree
from edifice.utilities import CURRENT_PLATFORM, Platform

if tp.TYPE_CHECKING:
    from collections.abc import Callable


def _seconds_position(on_position_changed: Callable[[float], None]) -> Callable[[int], None]:
    def _inner(position: int) -> None:
        on_position_changed(position / 1000.0)

    return _inner


class Video(QtWidgetElement[QVideoWidget]):
    """
    Video widget.

    Render a video widget that allows to show the user a video file with audio.
    It also allows to control pausing, stoppinh, playback position, and volume level.

    - Underlying Qt Widget:
      `QVideoWidget <https://doc.qt.io/qtforpython-6/PySide6/QtMultimediaWidgets/QVideoWidget.html>`_
    - Undelying Qt Multimedia Objects:
      `QAudioOutput <https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QAudioOutput.html>`_
      `QMediaPlayer <https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QMediaPlayer.html>`_

    Args:
        src:
            Path to the video file to be displayed.
        paused:
            Whether the video playback should be temporarily stopped.
        stopped:
            Similar to :code:`paused` but the playback position is resetted to the start.
        volume:
            Intensity of the audio, where 0 is a silent video playback and 100 is a playback
            with the maximum current system's volume.
        position:
            Timestamp, in seconds, to start the playback from.
        aspect_ratio_mode:
            The aspect ratio mode of the image.
            An `AspectRatioMode <https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.AspectRatioMode>`_
            to specify how the video should scale.
        on_position_changed:
            Callback for when the playback timestamp of the playback changes.
            It is important to not modify a state used in :code:`position` as that will cause the playback to stagger.
        on_duration_changed:
            Callback for when the total video playback duration changes.
        on_play_changed:
            Callback for when the playback is stopped or resumed.
    """
    def __init__(
        self,
        src: str,
        *,
        paused: bool = False,
        stop: bool = False,
        volume: int = 100,
        position: float | None = None,
        aspect_ratio_mode: QtCore.Qt.AspectRatioMode = QtCore.Qt.AspectRatioMode.KeepAspectRatio,
        on_position_changed: Callable[[float], None] | None = None,
        on_duration_changed: Callable[[float], None] | None = None,
        on_play_changed: Callable[[bool], None] | None = None,
        **kwargs: tp.Any,
    ) -> None:
        super().__init__(**kwargs)
        self._register_props(
            {
                "src": src,
                "aspect_ratio_mode": aspect_ratio_mode,
                "stop": stop,
                "paused": paused,
                "volume": volume,
                "position": position,
                "on_position_changed": on_position_changed,
                "on_play_changed": on_play_changed,
            },
        )
        self.underlying: QVideoWidget | None = None
        self.player: QMediaPlayer | None = None
        self.audio_output: QAudioOutput | None = None
        self.playing: bool = not stop
        self.paused: bool = paused
        self.volume = volume
        self.position = position
        self.on_position_changed = on_position_changed
        self.on_duration_changed = on_duration_changed
        self.on_play_changed = on_play_changed
        self.aspect_ratio_mode = aspect_ratio_mode

    def _initialize(self) -> None:
        self.underlying = QVideoWidget()

        # Avoids Windows openning an annoying second blank window while loading the video.
        if CURRENT_PLATFORM == Platform.Windows:
            self.underlying.setFullScreen(True)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.underlying.setObjectName(str(id(self)) + "-video")
        self.underlying.setAspectRatioMode(self.aspect_ratio_mode)
        self.player.setObjectName(str(id(self)) + "-player")
        self.audio_output.setObjectName(str(id(self)) + "-audio")
        self.player.setVideoOutput(self.underlying)
        self.player.setAudioOutput(self.audio_output)
        self.player.setSource(QUrl.fromLocalFile(str(self.props.src)))
        self.audio_output.setVolume(self.volume / 100)
        if self.position is not None:
            milliseconds_position = int(self.position * 1000)
            self.player.setPosition(milliseconds_position)

        if self.on_position_changed is not None:
            self.position_changed_handler = _seconds_position(self.on_position_changed)
            self.player.positionChanged.connect(self.position_changed_handler)
        else:
            self.position_changed_handler = None

        if self.on_duration_changed is not None:
            self.duration_changed_handler = _seconds_position(self.on_duration_changed)
            self.player.durationChanged.connect(self.duration_changed_handler)
        else:
            self.duration_changed_handler = None

        if self.on_play_changed is not None:
            self.player.playingChanged.connect(self.on_play_changed)

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        newprops: PropsDict,
    ) -> list[CommandType]:
        if self.underlying is None or self.player is None:
            self._initialize()
        assert self.underlying is not None
        assert self.player is not None

        def update_play_state(is_playing: bool) -> None:
            self.playing = is_playing

        def update_pause_state(is_paused: bool) -> None:
            self.paused = is_paused

        def play_stop_video() -> None:
            if self.player is None:
                return
            if self.playing:
                self.player.play()
                if self.paused:
                    self.player.pause()
            else:
                self.player.stop()

        def set_volume(volume: int) -> None:
            if self.audio_output is not None:
                self.audio_output.setVolume(volume / 100)

        def set_position(position: float | None) -> None:
            if self.player is not None and position is not None:
                milliseconds_position = int(position * 1000)
                self.player.setPosition(milliseconds_position)

        def set_on_position_changed(on_position_changed: Callable[[float], None] | None) -> None:
            if self.player is None:
                return
            self.on_position_changed = on_position_changed
            if self.position_changed_handler is not None:
                self.player.positionChanged.disconnect(self.position_changed_handler)
            if on_position_changed is not None:
                self.position_changed_handler = _seconds_position(on_position_changed)
                self.player.positionChanged.connect(self.position_changed_handler)

        def set_on_duration_changed(on_duration_changed: Callable[[float], None] | None) -> None:
            if self.player is None:
                return
            self.on_duration_changed = on_duration_changed
            if self.duration_changed_handler is not None:
                self.player.durationChanged.disconnect(self.duration_changed_handler)
            if on_duration_changed is not None:
                self.duration_changed_handler = _seconds_position(on_duration_changed)
                self.player.durationChanged.connect(self.duration_changed_handler)

        def set_on_play_changed(on_play_changed: Callable[[bool], None] | None) -> None:
            if self.player is None:
                return
            if self.on_play_changed is not None:
                self.player.playingChanged.disconnect(self.on_play_changed)
            self.on_play_changed = on_play_changed
            if self.on_play_changed is not None:
                self.player.playingChanged.connect(self.on_play_changed)

        def set_aspect_ratio_mode(aspect_ratio_mode: QtCore.Qt.AspectRatioMode) -> None:
            if self.underlying is None:
                return
            self.underlying.setAspectRatioMode(aspect_ratio_mode)

        commands = super()._qt_update_commands_super(widget_trees, newprops, self.underlying, None)
        if "src" in newprops:
            commands.append(CommandType(self.player.setSource, QUrl.fromLocalFile(str(newprops.src))))
            commands.append(CommandType(self.underlying.show))
            commands.append(CommandType(play_stop_video))
        if "aspect_ratio_mode" in newprops:
            commands.append(CommandType(set_aspect_ratio_mode, newprops.aspect_ratio_mode))
        if "stop" in newprops:
            commands.append(CommandType(update_play_state, not newprops.stop))
            commands.append(CommandType(self.player.stop) if newprops.stop else CommandType(self.player.play))
        if "paused" in newprops:
            commands.append(CommandType(update_pause_state, newprops.paused))
            if newprops.paused:
                commands.append(CommandType(self.player.pause))
            elif not newprops.paused and self.playing:
                commands.append(CommandType(self.player.play))
        if "volume" in newprops:
            commands.append(CommandType(set_volume, newprops.volume))
        if "position" in newprops:
            commands.append(CommandType(set_position, newprops.position))
        if "on_position_changed" in newprops:
            commands.append(CommandType(set_on_position_changed, newprops.on_position_changed))
        if "on_duration_changed" in newprops:
            commands.append(CommandType(set_on_duration_changed, newprops.on_duration_changed))
        if "on_play_changed" in newprops:
            commands.append(CommandType(set_on_play_changed, newprops.on_play_changed))
        return commands
