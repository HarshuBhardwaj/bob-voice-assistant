
from contextlib import contextmanager
from io import BytesIO

import pyautogui
import Vision
import Quartz
from Foundation import NSData


class ScreenControl:
    """Capture the screen, recognize text, find it, and click it."""

    def __init__(self):
        self.last_capture_size = None

    @contextmanager
    def capture_screen(self):
        """Capture a screenshot temporarily and close it after use."""
        screenshot = None

        try:
            screenshot = pyautogui.screenshot()
            self.last_capture_size = screenshot.size
            yield screenshot

        finally:
            if screenshot is not None:
                screenshot.close()

    def get_screen_size(self):
        """Return logical screen width and height."""
        return pyautogui.size()

    def read_screen_text(self):
        """Use Apple Vision OCR to read visible screen text."""
        detected_text = []

        with self.capture_screen() as screenshot:
            image_buffer = BytesIO()

            try:
                screenshot.save(image_buffer, format="PNG")
                image_bytes = image_buffer.getvalue()

                image_data = NSData.dataWithBytes_length_(
                    image_bytes,
                    len(image_bytes),
                )

                image_source = Quartz.CGImageSourceCreateWithData(
                    image_data,
                    None,
                )

                if image_source is None:
                    raise RuntimeError(
                        "Could not prepare screenshot image."
                    )

                cg_image = Quartz.CGImageSourceCreateImageAtIndex(
                    image_source,
                    0,
                    None,
                )

                if cg_image is None:
                    raise RuntimeError(
                        "Could not create image for OCR."
                    )

                request = Vision.VNRecognizeTextRequest.alloc().init()

                handler = (
                    Vision.VNImageRequestHandler
                    .alloc()
                    .initWithCGImage_options_(cg_image, None)
                )

                success, error = handler.performRequests_error_(
                    [request],
                    None,
                )

                if not success:
                    raise RuntimeError(
                        f"Apple Vision OCR failed: {error}"
                    )

                screen_width, screen_height = self.get_screen_size()
                image_width, image_height = screenshot.size

                scale_x = screen_width / image_width
                scale_y = screen_height / image_height

                for observation in request.results() or []:
                    candidates = observation.topCandidates_(1)

                    if not candidates:
                        continue

                    candidate = candidates[0]
                    text = candidate.string()
                    confidence = candidate.confidence()
                    box = observation.boundingBox()

                    center_x = (
                        box.origin.x + box.size.width / 2
                    ) * image_width

                    center_y = (
                        1 - box.origin.y - box.size.height / 2
                    ) * image_height

                    x = round(center_x * scale_x)
                    y = round(center_y * scale_y)

                    detected_text.append({
                        "text": text,
                        "confidence": round(float(confidence), 3),
                        "x": x,
                        "y": y,
                    })

            finally:
                image_buffer.close()

        return detected_text

    def find_text(
        self,
        target_text,
        case_sensitive=False,
        exact_match=True,
        min_confidence=0.7,
    ):
        """Find visible text using matching and confidence filters."""
        if not isinstance(target_text, str) or not target_text.strip():
            return []

        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError(
                "min_confidence must be between 0.0 and 1.0"
            )

        target = target_text.strip()
        matches = []

        for item in self.read_screen_text():
            visible_text = item["text"].strip()
            confidence = item["confidence"]

            if confidence < min_confidence:
                continue

            if case_sensitive:
                search_target = target
                search_text = visible_text
            else:
                search_target = target.casefold()
                search_text = visible_text.casefold()

            if exact_match:
                found = search_target == search_text
            else:
                found = search_target in search_text

            if found:
                matches.append(item)

        return matches

    def click_text(
        self,
        target_text,
        mouse_control,
        case_sensitive=False,
        min_confidence=0.7,
    ):
        """Click text only when exactly one reliable match exists."""
        matches = self.find_text(
            target_text,
            case_sensitive=case_sensitive,
            exact_match=True,
            min_confidence=min_confidence,
        )

        if not matches:
            print(f"No reliable match found for: {target_text!r}")
            return False

        if len(matches) > 1:
            print(
                f"Found {len(matches)} exact matches for "
                f"{target_text!r}. Not clicking because the target "
                "is ambiguous."
            )
            return False

        match = matches[0]
        x = match["x"]
        y = match["y"]

        print(
            f"Found {match['text']!r} at ({x}, {y}), "
            f"confidence: {match['confidence']}"
        )

        return mouse_control.click(x=x, y=y)
