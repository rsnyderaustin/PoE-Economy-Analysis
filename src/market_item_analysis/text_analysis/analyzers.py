import re


def extract_from_brackets(match):
    parts = match.group(1).split('|')
    return parts[-1] if len(parts) > 1 else parts[0]


class TextAnalyzer:

    def __init__(self, s: str):
        self.s = self._preprocess(s)

    @staticmethod
    def _preprocess(s):
        return re.sub(r'[–—−-]', '-', s).strip()

    def sanitize(self):
        brackets_pattern = r'\[(.*?)\]'
        result = re.sub(brackets_pattern, extract_from_brackets, self.s)
        result = result.strip().lower().replace(' ', '_')
        return result

    def extract_values_from_brackets(self) -> list[str]:


class ModTextAnalyzer(TextAnalyzer):

    def __init__(self, s: str):
        super().__init__(s)

    def extract_values(self) -> list[float]:
        matches = re.findall(r'-?\d+(?:\.\d+)?(?:\s*[–-]\s*-?\d+(?:\.\d+)?)?', self.s)
        result = []
        for match in matches:
            clean = re.sub(r'[–—−-]', '-', match).strip()

            if '-' in clean[1:]:  # if there's a dash not at the start, it's a range
                left_str, right_str = clean.split('-', 1)
                left = float(left_str) if '.' in left_str else int(left_str)
                right = float(right_str) if '.' in right_str else int(right_str)
                result.append((left, right))
            else:
                val = float(clean) if '.' in clean else int(clean)
                result.append(val)
        return result

    def sanitize(self):
        # Replace any #-# with #_to_#
        mod_text = s.strip().lower()
        result = re.sub(
            r'(-?\d+(?:\.\d+)?)\s*[–—−-]\s*(-?\d+(?:\.\d+)?)',
            r'\1_to_\2',
            mod_text
        )
        result = re.sub(r'\d+', 'n', result)
        result = result.replace('.n', '').replace('%', 'p')

        # Replace all non-alphabet characters with an underscore
        result = re.sub(r'[^a-zA-Z]', '_', result)
        # Filter multiple underscores into a singular underscore
        result = re.sub(r'_+', '_', result)

        brackets_pattern = r'\[(.*?)\]'
        result = re.sub(brackets_pattern, extract_from_brackets, result)

        result = result.strip(' _')

        print(f"Sanitized {mod_text} -> {result}")

        return result
