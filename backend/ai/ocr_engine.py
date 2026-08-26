import re
import cv2
import numpy as np
from paddleocr import PaddleOCR


# ============================================================
# PADDLE OCR
# ============================================================

print("=" * 60)
print("[ocr_engine] Loading PaddleOCR...")

reader = PaddleOCR(
    lang="en",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    enable_mkldnn=False,
    cpu_threads=4
)

print("[ocr_engine] PaddleOCR loaded successfully.")
print("=" * 60)


# ============================================================
# CONFIG
# ============================================================

MIN_OCR_CONFIDENCE = 0.25


# ============================================================
# INDIAN STATE / UT CODES
# ============================================================

INDIAN_STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD",
    "DL", "DN", "GA", "GJ", "HR", "HP", "JK", "JH",
    "KA", "KL", "LA", "LD", "MP", "MH", "MN", "ML",
    "MZ", "NL", "OD", "OR", "PB", "PY", "RJ", "SK",
    "TN", "TS", "TR", "UK", "UP", "WB"
}


# ============================================================
# VEHICLE / COMPANY WORDS
# ============================================================

VEHICLE_WORDS = {
    "YAMAHA",
    "HONDA",
    "TVS",
    "BAJAJ",
    "HERO",
    "SUZUKI",
    "ROYALENFIELD",
    "ROYAL",
    "ENFIELD",
    "KTM",
    "TOYOTA",
    "HYUNDAI",
    "TATA",
    "MAHINDRA",
    "FORD",
    "KIA",
    "NISSAN",
    "VOLKSWAGEN",
    "BMW",
    "AUDI",
    "MERCEDES",
    "MARUTI",
    "JEEP",
    "MG",
    "SKODA",
    "RENAULT",
    "NEXON",
    "ACTIVA"
}


# ============================================================
# CLEAN TEXT
# ============================================================

def clean_plate_text(raw_text: str) -> str:

    if not raw_text:
        return ""

    text = str(raw_text).upper().strip()

    text = text.replace(" ", "")
    text = text.replace("-", "")
    text = text.replace(".", "")
    text = text.replace("_", "")
    text = text.replace("/", "")

    text = re.sub(
        r"[^A-Z0-9]",
        "",
        text
    )

    return text


# ============================================================
# VEHICLE TEXT
# ============================================================

def is_vehicle_text(text: str) -> bool:

    if not text:
        return False

    return text.upper() in VEHICLE_WORDS


# ============================================================
# FULL INDIAN PLATE FORMAT
# ============================================================

def parse_full_plate(text: str):

    if not text:
        return None

    text = clean_plate_text(text)

    pattern = (
        r"^([A-Z]{2})"
        r"(\d{1,2})"
        r"([A-Z]{0,3})"
        r"(\d{1,4})$"
    )

    match = re.fullmatch(
        pattern,
        text
    )

    if not match:
        return None

    state = match.group(1)
    district = match.group(2)
    series = match.group(3)
    number = match.group(4)

    if state not in INDIAN_STATE_CODES:
        return None

    return {
        "state": state,
        "district": district,
        "series": series,
        "number": number
    }


# ============================================================
# PLATE FORMAT CHECK
# ============================================================

def looks_like_plate(text: str) -> bool:

    return parse_full_plate(text) is not None


# ============================================================
# OCR ENGINE
# ============================================================

class OCREngine:

    # ========================================================
    # PREPROCESS
    # ========================================================

    def preprocess_images(self, image):

        processed = []

        if image is None:
            return processed

        h, w = image.shape[:2]

        print(
            f"[ocr_engine] Original crop size: {w}x{h}"
        )

        # ----------------------------------------------------
        # 4X
        # ----------------------------------------------------

        enlarged = cv2.resize(
            image,
            None,
            fx=4,
            fy=4,
            interpolation=cv2.INTER_CUBIC
        )

        processed.append(
            ("original_4x", enlarged)
        )

        # ----------------------------------------------------
        # GRAYSCALE
        # ----------------------------------------------------

        gray = cv2.cvtColor(
            enlarged,
            cv2.COLOR_BGR2GRAY
        )

        gray_bgr = cv2.cvtColor(
            gray,
            cv2.COLOR_GRAY2BGR
        )

        processed.append(
            ("grayscale", gray_bgr)
        )

        # ----------------------------------------------------
        # CLAHE
        # ----------------------------------------------------

        clahe = cv2.createCLAHE(
            clipLimit=2.0,
            tileGridSize=(8, 8)
        )

        clahe_image = clahe.apply(gray)

        clahe_bgr = cv2.cvtColor(
            clahe_image,
            cv2.COLOR_GRAY2BGR
        )

        processed.append(
            ("clahe", clahe_bgr)
        )

        # ----------------------------------------------------
        # OTSU
        # ----------------------------------------------------

        _, otsu = cv2.threshold(
            clahe_image,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        otsu_bgr = cv2.cvtColor(
            otsu,
            cv2.COLOR_GRAY2BGR
        )

        processed.append(
            ("otsu", otsu_bgr)
        )

        # ----------------------------------------------------
        # INVERSE OTSU
        # ----------------------------------------------------

        _, otsu_inverse = cv2.threshold(
            clahe_image,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        otsu_inverse_bgr = cv2.cvtColor(
            otsu_inverse,
            cv2.COLOR_GRAY2BGR
        )

        processed.append(
            ("otsu_inverse", otsu_inverse_bgr)
        )

        # ----------------------------------------------------
        # ADAPTIVE
        # ----------------------------------------------------

        adaptive = cv2.adaptiveThreshold(
            clahe_image,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11
        )

        adaptive_bgr = cv2.cvtColor(
            adaptive,
            cv2.COLOR_GRAY2BGR
        )

        processed.append(
            ("adaptive", adaptive_bgr)
        )

        # ----------------------------------------------------
        # SHARPEN
        # ----------------------------------------------------

        kernel = np.array(
            [
                [0, -1, 0],
                [-1, 5, -1],
                [0, -1, 0]
            ],
            dtype=np.float32
        )

        sharpened = cv2.filter2D(
            enlarged,
            -1,
            kernel
        )

        processed.append(
            ("sharpened", sharpened)
        )

        # ----------------------------------------------------
        # 6X
        # ----------------------------------------------------

        enlarged_6x = cv2.resize(
            image,
            None,
            fx=6,
            fy=6,
            interpolation=cv2.INTER_CUBIC
        )

        processed.append(
            ("original_6x", enlarged_6x)
        )

        return processed

    # ========================================================
    # EXTRACT PADDLE RESULT
    # ========================================================

    def extract_modern_result(self, result):

        extracted = []

        try:

            rec_texts = None
            rec_scores = None

            # Dictionary
            try:
                rec_texts = result["rec_texts"]
                rec_scores = result["rec_scores"]
            except Exception:
                pass

            # Object
            if rec_texts is None:

                try:
                    rec_texts = result.rec_texts
                    rec_scores = result.rec_scores
                except Exception:
                    pass

            if rec_texts is None:
                return extracted

            if rec_scores is None:
                rec_scores = []

            rec_texts = list(rec_texts)
            rec_scores = list(rec_scores)

            for index, raw_text in enumerate(rec_texts):

                try:

                    raw_text = str(raw_text)

                    confidence = (
                        float(rec_scores[index])
                        if index < len(rec_scores)
                        else 0.0
                    )

                    cleaned = clean_plate_text(
                        raw_text
                    )

                    if not cleaned:
                        continue

                    extracted.append(
                        {
                            "text": cleaned,
                            "confidence": confidence,
                            "raw_text": raw_text
                        }
                    )

                except Exception:
                    continue

        except Exception as e:

            print(
                "[ocr_engine] Result extraction error:",
                str(e)
            )

        return extracted

    # ========================================================
    # RUN OCR
    # ========================================================

    def run_ocr(
        self,
        image,
        version_name
    ):

        try:

            print(
                f"[ocr_engine] Running OCR: {version_name}"
            )

            results = reader.predict(
                input=image
            )

            extracted = []

            for result in results:

                current = self.extract_modern_result(
                    result
                )

                for item in current:
                    item["version"] = version_name

                extracted.extend(
                    current
                )

            return extracted

        except Exception as e:

            print(
                f"[ocr_engine] "
                f"{version_name} ERROR:",
                str(e)
            )

            return []

    # ========================================================
    # OCR VOTING
    # ========================================================

    def create_votes(self, candidates):

        votes = {}

        for item in candidates:

            text = item["text"]
            confidence = item["confidence"]

            if not text:
                continue

            if is_vehicle_text(text):
                continue

            if text not in votes:

                votes[text] = {
                    "text": text,
                    "count": 0,
                    "best_confidence": 0.0,
                    "total_confidence": 0.0
                }

            votes[text]["count"] += 1

            votes[text]["total_confidence"] += (
                confidence
            )

            votes[text]["best_confidence"] = max(
                votes[text]["best_confidence"],
                confidence
            )

        return list(
            votes.values()
        )

    # ========================================================
    # FIND STATE
    # ========================================================

    def find_state(self, votes):

        states = [
            item
            for item in votes
            if (
                len(item["text"]) == 2
                and item["text"]
                in INDIAN_STATE_CODES
            )
        ]

        if not states:
            return None

        best = max(
            states,
            key=lambda x: (
                x["count"],
                x["best_confidence"]
            )
        )

        print(
            f"[ocr_engine] State: {best['text']}"
        )

        return best["text"]

    # ========================================================
    # EXTRACT PLATE FRAGMENTS
    # ========================================================

    def extract_fragments(self, text):

        text = clean_plate_text(text)

        fragments = []

        if not text:
            return fragments

        # ----------------------------------------------------
        # Direct complete plate
        # ----------------------------------------------------

        parsed = parse_full_plate(text)

        if parsed:

            fragments.append({
                "type": "full",
                "text": text,
                "state": parsed["state"],
                "district": parsed["district"],
                "series": parsed["series"],
                "number": parsed["number"]
            })

            return fragments

        # ----------------------------------------------------
        # State + district + series
        #
        # CG07C
        # KL65L
        # TN38AB
        # ----------------------------------------------------

        match = re.fullmatch(
            r"([A-Z]{2})(\d{1,2})([A-Z]{1,3})",
            text
        )

        if match:

            state = match.group(1)
            district = match.group(2)
            series = match.group(3)

            if state in INDIAN_STATE_CODES:

                fragments.append({
                    "type": "prefix",
                    "text": text,
                    "state": state,
                    "district": district,
                    "series": series
                })

                return fragments

        # ----------------------------------------------------
        # State + district
        #
        # CG07
        # KL65
        # TN38
        # ----------------------------------------------------

        match = re.fullmatch(
            r"([A-Z]{2})(\d{1,2})",
            text
        )

        if match:

            state = match.group(1)
            district = match.group(2)

            if state in INDIAN_STATE_CODES:

                fragments.append({
                    "type": "district",
                    "text": text,
                    "state": state,
                    "district": district
                })

                return fragments

        # ----------------------------------------------------
        # Number + series
        #
        # 65L
        # 38AB
        # ----------------------------------------------------

        match = re.fullmatch(
            r"(\d{1,2})([A-Z]{1,3})",
            text
        )

        if match:

            fragments.append({
                "type": "district_series",
                "district": match.group(1),
                "series": match.group(2),
                "text": text
            })

            return fragments

        # ----------------------------------------------------
        # Series + number
        #
        # K7276
        # AB1234
        # ABC1234
        # ----------------------------------------------------

        match = re.fullmatch(
            r"([A-Z]{1,3})(\d{1,4})",
            text
        )

        if match:

            fragments.append({
                "type": "series_number",
                "series": match.group(1),
                "number": match.group(2),
                "text": text
            })

            return fragments

        # ----------------------------------------------------
        # Pure number
        # ----------------------------------------------------

        if re.fullmatch(
            r"\d{1,4}",
            text
        ):

            fragments.append({
                "type": "number",
                "number": text,
                "text": text
            })

            return fragments

        # ----------------------------------------------------
        # Pure series
        # ----------------------------------------------------

        if re.fullmatch(
            r"[A-Z]{1,3}",
            text
        ):

            if text not in INDIAN_STATE_CODES:

                fragments.append({
                    "type": "series",
                    "series": text,
                    "text": text
                })

        return fragments

    # ========================================================
    # BUILD PLATE FROM OCR
    # ========================================================

    def build_plate_from_votes(self, votes):

        # ----------------------------------------------------
        # STEP 1
        # Complete plate directly
        # ----------------------------------------------------

        full_candidates = []

        for item in votes:

            fragments = self.extract_fragments(
                item["text"]
            )

            for fragment in fragments:

                if fragment["type"] == "full":

                    full_candidates.append(
                        (
                            item,
                            fragment
                        )
                    )

        if full_candidates:

            best_item, fragment = max(
                full_candidates,
                key=lambda x: (
                    x[0]["count"],
                    x[0]["best_confidence"],
                    len(x[0]["text"])
                )
            )

            return {
                "plate_number": fragment["text"],
                "confidence": best_item[
                    "best_confidence"
                ]
            }

        # ----------------------------------------------------
        # STEP 2
        # Find prefix fragments
        #
        # CG07C
        # KL65L
        # TN38AB
        # ----------------------------------------------------

        prefixes = []

        for item in votes:

            fragments = self.extract_fragments(
                item["text"]
            )

            for fragment in fragments:

                if fragment["type"] == "prefix":

                    prefixes.append(
                        (
                            item,
                            fragment
                        )
                    )

        # ----------------------------------------------------
        # Try prefix + number
        # ----------------------------------------------------

        if prefixes:

            for prefix_item, prefix in sorted(
                prefixes,
                key=lambda x: (
                    x[0]["count"],
                    x[0]["best_confidence"]
                ),
                reverse=True
            ):

                for number_item in votes:

                    fragments = self.extract_fragments(
                        number_item["text"]
                    )

                    for fragment in fragments:

                        if fragment["type"] == "number":

                            number = fragment["number"]

                            plate = (
                                prefix["state"]
                                + prefix["district"]
                                + prefix["series"]
                                + number
                            )

                            if looks_like_plate(plate):

                                confidence = (
                                    prefix_item[
                                        "best_confidence"
                                    ]
                                    + number_item[
                                        "best_confidence"
                                    ]
                                ) / 2

                                return {
                                    "plate_number": plate,
                                    "confidence": confidence
                                }

                        # ------------------------------------
                        # K7276 case
                        #
                        # Prefix = CG07C
                        # Token = K7276
                        #
                        # Final = CG07CK7276
                        # ------------------------------------

                        if fragment["type"] == "series_number":

                            series = fragment["series"]
                            number = fragment["number"]

                            # Prefix already has series.
                            # Add token's series + number.
                            plate = (
                                prefix["state"]
                                + prefix["district"]
                                + prefix["series"]
                                + series
                                + number
                            )

                            if looks_like_plate(plate):

                                confidence = (
                                    prefix_item[
                                        "best_confidence"
                                    ]
                                    + number_item[
                                        "best_confidence"
                                    ]
                                ) / 2

                                return {
                                    "plate_number": plate,
                                    "confidence": confidence
                                }

        # ----------------------------------------------------
        # STEP 3
        # Find state separately
        # ----------------------------------------------------

        state = self.find_state(votes)

        if not state:
            return None

        # ----------------------------------------------------
        # District candidates
        # ----------------------------------------------------

        district_candidates = []

        # ----------------------------------------------------
        # Series candidates
        # ----------------------------------------------------

        series_candidates = []

        # ----------------------------------------------------
        # Number candidates
        # ----------------------------------------------------

        number_candidates = []

        for item in votes:

            text = item["text"]

            if text == state:
                continue

            fragments = self.extract_fragments(
                text
            )

            for fragment in fragments:

                fragment_type = fragment["type"]

                # --------------------------------------------
                # District
                # --------------------------------------------

                if fragment_type == "district":

                    district_candidates.append({
                        "text": fragment["district"],
                        "confidence": item[
                            "best_confidence"
                        ],
                        "count": item["count"]
                    })

                # --------------------------------------------
                # District + series
                # --------------------------------------------

                elif fragment_type == "district_series":

                    district_candidates.append({
                        "text": fragment["district"],
                        "confidence": item[
                            "best_confidence"
                        ],
                        "count": item["count"]
                    })

                    series_candidates.append({
                        "text": fragment["series"],
                        "confidence": item[
                            "best_confidence"
                        ],
                        "count": item["count"]
                    })

                # --------------------------------------------
                # Number
                # --------------------------------------------

                elif fragment_type == "number":

                    number_candidates.append({
                        "text": fragment["number"],
                        "confidence": item[
                            "best_confidence"
                        ],
                        "count": item["count"]
                    })

                # --------------------------------------------
                # Series
                # --------------------------------------------

                elif fragment_type == "series":

                    series_candidates.append({
                        "text": fragment["series"],
                        "confidence": item[
                            "best_confidence"
                        ],
                        "count": item["count"]
                    })

        # ----------------------------------------------------
        # Need district
        # ----------------------------------------------------

        if not district_candidates:

            return None

        # ----------------------------------------------------
        # Need number
        # ----------------------------------------------------

        if not number_candidates:

            return None

        # ----------------------------------------------------
        # Best district
        # ----------------------------------------------------

        district = max(
            district_candidates,
            key=lambda x: (
                x["count"],
                x["confidence"],
                len(x["text"])
            )
        )

        # ----------------------------------------------------
        # Best number
        # ----------------------------------------------------

        registration = max(
            number_candidates,
            key=lambda x: (
                len(x["text"]),
                x["count"],
                x["confidence"]
            )
        )

        district_text = district["text"]
        number_text = registration["text"]

        # ----------------------------------------------------
        # Best series
        # ----------------------------------------------------

        series_text = ""

        if series_candidates:

            series = max(
                series_candidates,
                key=lambda x: (
                    x["count"],
                    x["confidence"],
                    -len(x["text"])
                )
            )

            series_text = series["text"]

        # ----------------------------------------------------
        # BUILD
        # ----------------------------------------------------

        plate = (
            state
            + district_text
            + series_text
            + number_text
        )

        # ----------------------------------------------------
        # VALIDATE
        # ----------------------------------------------------

        if not looks_like_plate(plate):

            return None

        # ----------------------------------------------------
        # CONFIDENCE
        # ----------------------------------------------------

        confidence_values = [
            district["confidence"],
            registration["confidence"]
        ]

        state_confidences = [
            item["best_confidence"]
            for item in votes
            if item["text"] == state
        ]

        if state_confidences:

            confidence_values.append(
                max(state_confidences)
            )

        if series_text:

            confidence_values.extend([
                item["confidence"]
                for item in series_candidates
                if item["text"] == series_text
            ])

        confidence = (
            sum(confidence_values)
            / len(confidence_values)
        )

        return {
            "plate_number": plate,
            "confidence": confidence
        }

    # ========================================================
    # COMBINE PLATE PARTS
    # ========================================================

    def combine_plate_parts(self, candidates):

        print("=" * 60)
        print(
            "[ocr_engine] Trying to combine plate parts..."
        )

        filtered = [
            item
            for item in candidates
            if (
                item["confidence"]
                >= MIN_OCR_CONFIDENCE
                and not is_vehicle_text(
                    item["text"]
                )
            )
        ]

        if not filtered:
            return None

        votes = self.create_votes(
            filtered
        )

        result = self.build_plate_from_votes(
            votes
        )

        if result:

            print(
                f"[ocr_engine] "
                f"BUILT PLATE: "
                f"{result['plate_number']}"
            )

            print(
                f"[ocr_engine] "
                f"Confidence: "
                f"{result['confidence']:.4f}"
            )

        return result

    # ========================================================
    # READ PLATE
    # ========================================================

    def read_plate(self, image):

        print("=" * 60)
        print(
            "[ocr_engine] START PLATE OCR"
        )

        # ----------------------------------------------------
        # Image check
        # ----------------------------------------------------

        if image is None:

            print(
                "[ocr_engine] ERROR: Image is None"
            )

            return {
                "plate_number": "Not Recognized",
                "confidence": 0.0,
                "raw": []
            }

        # ----------------------------------------------------
        # Preprocess
        # ----------------------------------------------------

        processed_images = (
            self.preprocess_images(
                image
            )
        )

        # ----------------------------------------------------
        # Run OCR
        # ----------------------------------------------------

        all_candidates = []

        for (
            version_name,
            processed_image
        ) in processed_images:

            results = self.run_ocr(
                processed_image,
                version_name
            )

            all_candidates.extend(
                results
            )

        # ----------------------------------------------------
        # No OCR result
        # ----------------------------------------------------

        if not all_candidates:

            return {
                "plate_number": "Not Recognized",
                "confidence": 0.0,
                "raw": []
            }

        # ----------------------------------------------------
        # Print results
        # ----------------------------------------------------

        print("=" * 60)
        print(
            "[ocr_engine] ALL OCR RESULTS"
        )

        for candidate in all_candidates:

            print(
                f"TEXT={candidate['text']} "
                f"CONF={candidate['confidence']:.4f} "
                f"VERSION={candidate['version']}"
            )

        # ----------------------------------------------------
        # Filter
        # ----------------------------------------------------

        valid = [
            item
            for item in all_candidates
            if item["confidence"]
            >= MIN_OCR_CONFIDENCE
        ]

        # ----------------------------------------------------
        # Combine
        # ----------------------------------------------------

        combined = self.combine_plate_parts(
            valid
        )

        if combined:

            print("=" * 60)

            print(
                f"[ocr_engine] FINAL PLATE: "
                f"{combined['plate_number']}"
            )

            print(
                f"[ocr_engine] FINAL CONFIDENCE: "
                f"{combined['confidence']:.4f}"
            )

            print("=" * 60)

            return {
                "plate_number": combined[
                    "plate_number"
                ],
                "confidence": round(
                    combined["confidence"],
                    2
                ),
                "raw": all_candidates
            }

        # ----------------------------------------------------
        # Fallback
        # ----------------------------------------------------

        full_plates = []

        for item in valid:

            if looks_like_plate(
                item["text"]
            ):

                full_plates.append(
                    item
                )

        if full_plates:

            best = max(
                full_plates,
                key=lambda x: (
                    len(x["text"]),
                    x["confidence"]
                )
            )

            return {
                "plate_number": best["text"],
                "confidence": round(
                    best["confidence"],
                    2
                ),
                "raw": all_candidates
            }

        # ----------------------------------------------------
        # Failed
        # ----------------------------------------------------

        print(
            "[ocr_engine] "
            "Plate not confidently recognized."
        )

        print("=" * 60)

        return {
            "plate_number": "Not Recognized",
            "confidence": 0.0,
            "raw": all_candidates
        }


# ============================================================
# GLOBAL INSTANCE
# ============================================================

ocr_engine = OCREngine()