from PySide6.QtCore import QVariantAnimation, QEasingCurve, QPoint, QTimer, Signal, QObject


class AnimationManager(QObject):
    animation_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def scale_to(self, widget, target_scale, duration_ms=500):
        base_w, base_h = widget.gif_size
        base_w = max(1, base_w)
        base_h = max(1, base_h)
        start_w = widget.width()
        target_w = max(1, int(base_w * target_scale))

        anim = QVariantAnimation(widget)
        anim.setDuration(duration_ms)
        anim.setStartValue(start_w)
        anim.setEndValue(target_w)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        orig_center = widget.frameGeometry().center()

        def on_value_changed(w):
            h = int(w * base_h / base_w)
            center = orig_center
            widget.resize(w, h)
            widget.move(center.x() - w // 2, center.y() - h // 2)

        anim.valueChanged.connect(on_value_changed)
        anim.finished.connect(self.animation_finished.emit)
        anim.start()
        return anim

    def shake(self, widget, duration_ms=8000, fps=25):
        interval = 1000 // fps
        steps = duration_ms // interval
        amplitude = 15
        original_pos = widget.pos()
        step = 0

        timer = QTimer(widget)
        timer.setInterval(interval)

        def tick():
            nonlocal step
            if step >= steps:
                timer.stop()
                widget.move(original_pos)
                self.animation_finished.emit()
                return
            offset = amplitude * ((steps - step) / steps)
            direction = -1 if (step % 2 == 0) else 1
            widget.move(original_pos.x() + int(offset * direction), original_pos.y())
            step += 1

        timer.timeout.connect(tick)
        widget._shake_original_pos = original_pos
        widget._shake_timer = timer
        timer.start()
        return timer

    def stop_shake(self, widget):
        timer = getattr(widget, "_shake_timer", None)
        if timer:
            timer.stop()
        if hasattr(widget, "_shake_original_pos"):
            widget.move(widget._shake_original_pos)

    @staticmethod
    def stop_scale(widget):
        pass
