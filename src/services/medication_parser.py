import re
from typing import Dict

def extract_specifications(description: str) -> Dict[str, str]:
    specs = {}
    # Regex para dosis compuestas (e.g., 40 MG/10 M)
    dosis_match = re.search(r'(\d+(?:\.\d+)?)\s*(MG|ML|G|MCG|UI)(?:/(\d+(?:\.\d+)?)\s*(MG|ML|G|MCG|UI))?', description.upper())
    if dosis_match:
        dosis = f"{dosis_match.group(1)} {dosis_match.group(2).lower()}"
        if dosis_match.group(3):
            dosis += f"/{dosis_match.group(3)} {dosis_match.group(4).lower()}"
        specs['dosis'] = dosis
    
    # Regex para forma
    forma_match = re.search(r'\b(COMP|CREMA|AMP|GOTAS|JARABE|SOBRES|PDA|POMADA)\b', description.upper())
    if forma_match:
        specs['forma'] = forma_match.group(1).lower()
    
    return specs

# Otras funciones existentes en el archivo (si las tienes, mantenlas)
logger = logging.getLogger(__name__)

class MedicationParser:
    """Enhanced medication name parser with comprehensive specification extraction"""

    def __init__(self):
        # Common medication forms in Spanish
        self.medication_forms = {
            'comprimidos': ' comprimido', 'comprimido': ' comprimido', 'comp': ' comprimido',
            'tabletas': ' tableta', 'tableta': ' tableta', 'tabs': ' tableta', 'tab': ' tableta',
            'cápsulas': ' cápsula', 'cápsula': ' cápsula', 'caps': ' cápsula', 'cap': ' cápsula',
            'ampollas': ' ampolla', 'ampolla': ' ampolla', 'amp': ' ampolla',
            'inyectable': ' inyectable', 'inyectables': ' inyectable', 'iny': ' inyectable',
            'crema': ' crema', 'pomada': ' pomada', 'ungüento': ' ungüento',
            'gotas': ' gotas', 'colirio': ' colirio', 'jarabe': ' jarabe',
            'suspensión': ' suspensión', 'susp': ' suspensión',
            'polvo': ' polvo', 'granulado': ' granulado',
            'sobres': ' sobre', 'sobre': ' sobre', 'envases': ' envase', 'envase': ' envase',
            'frascos': ' frasco', 'frasco': ' frasco', 'tubos': ' tubo', 'tubo': ' tubo'
        }

        # Common dosage units
        self.dosage_units = ['mg', 'g', 'ml', 'mcg', 'ui', 'mg/ml', 'mg/5ml', 'mg/1ml']

        # Common pack sizes
        self.pack_patterns = [
            r'x\s*(\d+)',
            r'(\d+)\s*(?:unidades|un|unds?|comprimidos|comps?|tabs?|cápsulas|caps?)',
            r'(\d+)\s*(?:frascos|frasco|envases|envase|tubos|tubo|cajas|caja)',
        ]

    def parse_medication_name(self, name: str) -> Dict[str, Any]:
        """
        Parse medication name into structured components

        Expected formats:
        - "BRAND (ACTIVE) FORM x PACK"
        - "GENERIC_NAME DOSAGE FORM"
        - "BRAND_NAME DOSAGE UNIT FORM"
        """
        result = {
            'brand': '',
            'active': '',
            'form': '',
            'dose': '',
            'pack': ''
        }

        # Clean the name first
        clean_name = self._clean_medication_name(name)

        # Try pattern: BRAND (ACTIVE) FORM x PACK
        pattern1_match = re.search(
            r'(.+?)\s*\((.+?)\)\s*(.+?)\s*x\s*(\d+)',
            clean_name,
            re.IGNORECASE
        )

        if pattern1_match:
            result['brand'] = pattern1_match.group(1).strip()
            result['active'] = pattern1_match.group(2).strip()
            result['form'] = pattern1_match.group(3).strip()
            result['pack'] = pattern1_match.group(4).strip()
            return result

        # Try pattern: GENERIC_NAME DOSAGE FORM
        pattern2_match = re.search(
            r'(.+?)\s+(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|ui|mg/ml)\s*(.+)',
            clean_name,
            re.IGNORECASE
        )

        if pattern2_match:
            result['active'] = pattern2_match.group(1).strip()
            result['dose'] = f"{pattern2_match.group(2)} {pattern2_match.group(3)}"
            result['form'] = pattern2_match.group(4).strip()
            return result

        # Try pattern: BRAND_NAME DOSAGE UNIT FORM
        pattern3_match = re.search(
            r'(.+?)\s+(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|ui|mg/ml)\s*(.+?)\s*$',
            clean_name,
            re.IGNORECASE
        )

        if pattern3_match:
            result['brand'] = pattern3_match.group(1).strip()
            result['dose'] = f"{pattern3_match.group(2)} {pattern3_match.group(3)}"
            result['form'] = pattern3_match.group(4).strip()
            return result

        # Fallback: extract what we can
        result = self._fallback_parsing(clean_name)

        return result

    def _clean_medication_name(self, name: str) -> str:
        """Clean medication name for better parsing"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', name.strip())

        # Remove common noise words
        noise_words = ['.-', 'comp.', 'mg.', 'ml.', 'ui.', 'und.', 'unds.']
        for word in noise_words:
            cleaned = cleaned.replace(word, '')

        # Fix common typos
        cleaned = cleaned.replace('tazobactam', 'tazobactam')
        cleaned = cleaned.replace('piperacilina', 'piperacilina')

        return cleaned.strip()

    def _fallback_parsing(self, name: str) -> Dict[str, Any]:
        """Fallback parsing when standard patterns don't match"""
        result = {
            'brand': '',
            'active': '',
            'form': '',
            'dose': '',
            'pack': ''
        }

        # Try to identify the first word as brand
        words = name.split()
        if words:
            result['brand'] = words[0]

        # Look for dosage in the name
        for word in words:
            # Check if word contains dosage pattern
            if re.search(r'\d+', word):
                # Check if it's followed by a unit
                for unit in self.dosage_units:
                    if unit in word.lower():
                        result['dose'] = word
                        break

        # Look for form keywords
        for form_spanish, form_english in self.medication_forms.items():
            if form_spanish in name.lower():
                result['form'] = form_english.strip()
                break

        # Look for pack sizes
        for pattern in self.pack_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                result['pack'] = match.group(1)
                break

        return result

    def extract_specifications(self, description: str) -> Dict[str, Any]:
        """Extract specifications from medication description"""
        specs = {}

        # Extract dosage
        dosage = self._extract_dosage(description)
        if dosage:
            specs['dosage'] = dosage

        # Extract form
        form = self._extract_form(description)
        if form:
            specs['form'] = form

        # Extract pack size
        pack = self._extract_pack_size(description)
        if pack:
            specs['pack_size'] = pack

        # Extract concentration if applicable
        concentration = self._extract_concentration(description)
        if concentration:
            specs['concentration'] = concentration

        return specs

    def _extract_dosage(self, description: str) -> Optional[str]:
        """Extract dosage information"""
        # Pattern: NUMBER UNIT
        patterns = [
            r'(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|ui|mg/ml)',
            r'(\d+(?:\.\d+)?)\s*(mg|g|ml|mcg|ui|mg/ml)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            if matches:
                return f"{matches[0][0]} {matches[0][1]}"

        return None

    def _extract_form(self, description: str) -> Optional[str]:
        """Extract medication form"""
        description_lower = description.lower()

        for form_spanish, form_english in self.medication_forms.items():
            if form_spanish in description_lower:
                return form_english.strip()

        return None

    def _extract_pack_size(self, description: str) -> Optional[str]:
        """Extract pack size information"""
        for pattern in self.pack_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_concentration(self, description: str) -> Optional[str]:
        """Extract concentration information"""
        # Pattern: NUMBER/NUMBER UNIT (e.g., 5/5 ml, 200/5 ml)
        patterns = [
            r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*(mg|g|ml)',
            r'(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*(mg|g|ml)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            if matches:
                return f"{matches[0][0]}/{matches[0][1]} {matches[0][2]}"

        return None

    def validate_specifications(self, specs: Dict[str, Any]) -> bool:
        """Validate that extracted specifications make sense"""
        # Basic validation rules
        if 'dosage' in specs and not specs['dosage']:
            return False

        if 'form' in specs and not specs['form']:
            return False

        # Check for conflicting information
        if 'dosage' in specs and 'concentration' in specs:
            # Both shouldn't be present usually
            logger.warning(f"Both dosage and concentration found in specs: {specs}")

        return True
