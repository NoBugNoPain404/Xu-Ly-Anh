from __future__ import annotations

import logging
import re
import unicodedata
from datetime import datetime

logger = logging.getLogger("postprocessor")

class Postprocessor:
    _ID_PATTERN = re.compile(r"\d{12}")
    _DATE_PATTERN = re.compile(r"\d{1,2}[\s\/\-\.]\d{1,2}[\s\/\-\.]\d{4}")
    _NATIONALITY_PATTERN = re.compile(r"Vi[eệ]t", re.IGNORECASE)
    _MALE_PATTERN = re.compile(r"\bNam\b", re.IGNORECASE)
    _FEMALE_PATTERN = re.compile(r"N[uưữ]", re.IGNORECASE)
    
    _NAME_NOISE_EXACT = frozenset(
        {"ho", "va", "ten", "họ", "tên", "no", "so", "số", "name", "full"}
    )
    _NAME_NOISE_SUBSTRING = frozenset(
        {"hova", "fuilname", "fullname", "hoten", "hovaten", "họtên"}
    )
    
    _ADDRESS_NOISE_SUBSTRINGS = frozenset(
        {
            "quequanpaceof", "lplaceof", "quequan", "paceof", "onig", 
            "place of origin", "quê quán", "nơi thường trú", "place of residence", 
            "thuongtru", "noithuongtru", "origin", "residence", "noi thurng tru", 
            "noi thuong tru", "placeofn", "residenca", "thurongtru", "noithurongtru",
            "que guan", "queguan", "place of", "placeof", "of origin", "oforigin",
             "/Place" 
        }
    )

    def process(self, raw: dict[str, str]) -> dict[str, str]:
        raw = raw or {}
        
        raw_addr_1 = raw.get("address_line1", "")
        raw_addr_2 = raw.get("address_line2", "")
        combined_address = f"{raw_addr_1} {raw_addr_2}".strip()

        # Đã xóa expiry_date khỏi dictionary này
        cleaned = {
            "id_number": self._extract_id(raw.get("id_number", "")),
            "full_name": self._clean_name(raw.get("full_name", "")),
            "date_of_birth": self._extract_date(raw.get("date_of_birth", "")),
            "gender": self._extract_gender(raw.get("gender", "")),
            "nationality": self._extract_nationality(raw.get("nationality", "")),
            "home_town": self._clean_address(raw.get("home_town", "")),
            "address": self._clean_address(combined_address), 
        }

        for field_name, value in cleaned.items():
            if not value:
                raw_val = combined_address if field_name == "address" else raw.get(field_name, "")
                logger.warning("Empty result for %s. Raw was: %r", field_name, raw_val)

        return cleaned  

    def _normalize(self, text: str) -> str:
        if not text:
            return ""
            
        value = str(text)
        value = unicodedata.normalize('NFD', value)
        value = re.sub(r'[\u0300-\u036f]', '', value)
        value = value.replace('Đ', 'D').replace('đ', 'd')
        value = value.encode('ascii', 'ignore').decode('utf-8')
        
        return value.strip()

    def _extract_id(self, text: str) -> str:
        if text is None: return ""
        normalized = str(text).replace("O", "0").replace("o", "0").replace(" ", "")
        match = self._ID_PATTERN.search(normalized)
        if match:
            return match.group(0)
        return self._normalize(text)

    def _extract_date(self, text: str) -> str:
        if text is None: return ""
        substituted = str(text)
        substitutions = {
            "O": "0", "o": "0", "l": "1", "I": "1", "S": "5", "s": "5", 
            "A": "4", "B": "8", "G": "6", "Z": "2"
        }
        for source, target in substitutions.items():
            substituted = substituted.replace(source, target)

        match = self._DATE_PATTERN.search(substituted)
        if not match: return ""

        normalized = re.sub(r"[\s\-\.]", "/", match.group())
        parts = normalized.split("/")
        if len(parts) != 3: return ""

        day, month, year = parts
        candidate = f"{int(day):02d}/{int(month):02d}/{year}"

        try:
            datetime.strptime(candidate, "%d/%m/%Y")
            return candidate
        except ValueError:
            return ""

    def _extract_gender(self, text: str) -> str:
        if not text: return ""
        value = str(text).upper()
        if self._MALE_PATTERN.search(value): return "Nam"
        
        if "N" in value and "M" not in value: return "Nu"
        return ""

    def _extract_nationality(self, text: str) -> str:
        value = "" if text is None else str(text)
        if self._NATIONALITY_PATTERN.search(value): return "Viet Nam"
        return self._normalize(value)

    def _clean_address(self, text: str) -> str:
        if not text: 
            return ""

        cleaned = str(text).replace("\n", " ").strip()

        cleaned = cleaned.replace("O toO", "O to").replace("O to O", "O to")
        cleaned = re.sub(r'34\s*[Il|\\]\s*1', '341', cleaned) 
        cleaned = re.sub(r'Q\s*lo\s*ngo\s*v', '', cleaned, flags=re.IGNORECASE) 
        cleaned = cleaned.replace("Ng Quyen", "Ngo Quyen") 

        cleaned = re.sub(r'^(nong|ong|hong|phong|g|ng|n|o)\s*', '', cleaned, flags=re.IGNORECASE)

        cleaned = cleaned.replace("Nana", "Nang").replace("Nao", "Ngo")
        cleaned = re.sub(r'\bn[aã]o\s*(\d+)', r'ngo \1', cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(
            r'S[0Oo6]?\s*(\d+)\s*TT',
            r'So \1 TT ',
            cleaned,
            flags=re.IGNORECASE
        )

        cleaned = re.sub(
            r'TT\s*[Oo0]?\s*[Tt][Oo06]+',
            'TT O to',
            cleaned,
            flags=re.IGNORECASE
        )
        
        for noise in self._ADDRESS_NOISE_SUBSTRINGS:
            cleaned = re.sub(re.escape(noise), "", cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(r'[:|;\[\]_&]', ' ', cleaned)
        cleaned = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned)
        cleaned = cleaned.replace(".", ", ")

        cleaned = re.sub(r',\s*,', ',', cleaned) 
        final_text = " ".join(cleaned.split()).strip()
        final_text = final_text.lstrip(", ")
        
        return self._normalize(final_text)

    def _clean_name(self, text: str) -> str:
        if not text: return ""
        cleaned = str(text)
        
        vn_surnames = r'\b(NGUYEN|TRAN|LE|PHAM|HOANG|HUYNH|PHAN|VU|VO|DANG|BUI|DO|HO|NGO|DUONG|LY)(?=[A-Z])'
        cleaned = re.sub(vn_surnames, r'\1 ', cleaned, flags=re.IGNORECASE)

        for noise in self._NAME_NOISE_SUBSTRING:
            cleaned = re.sub(re.escape(noise), " ", cleaned, flags=re.IGNORECASE)

        for noise in self._NAME_NOISE_EXACT:
            cleaned = re.sub(rf"\b{re.escape(noise)}\b", " ", cleaned, flags=re.IGNORECASE)

        cleaned = re.sub(r'[:|;\[\]_&/]', ' ', cleaned).strip()
        
        words = cleaned.split()
        name_words = [w for w in words if any(c.isupper() for c in w)]
        
        if name_words:
            return self._normalize(" ".join(name_words).upper())
        
        return self._normalize(cleaned.upper())