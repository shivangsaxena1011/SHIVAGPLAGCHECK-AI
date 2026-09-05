# Third-Party Notices and Licenses

SHIVANG PLAGCHECK AI incorporates algorithmic logic, modules, and utilities from several open-source projects under permissible licenses. We gratefully acknowledge and credit the respective authors and contributors.

---

## 1. Noplag Engine
- **Upstream Repository**: https://github.com/NoplagLabs/noplag-engine
- **Commit SHA**: `aaf7839766460cf387e91b5a730aba8928db47d8`
- **License**: Apache License, Version 2.0
- **Copyright**: Copyright 2024 NoplagLabs
- **Components Integrated**:
  - `fingerprinting/winnowing.py` &rarr; `backend/app/services/plagiarism/exact/winnowing.py`
  - `alignment/seed_extend.py` &rarr; `backend/app/services/plagiarism/exact/alignment.py`
  - `intervals.py` &rarr; `backend/app/services/plagiarism/exact/intervals.py`
  - `chunking/sliding.py` &rarr; `backend/app/services/plagiarism/exact/chunking/sliding.py`
  - `retrieval/` &rarr; `backend/app/services/plagiarism/exact/retrieval/`

### Apache License 2.0 Notice
```
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## 2. Aegis Integrity
- **Upstream Repository**: https://github.com/sunilgentyala/aegis-integrity
- **Commit SHA**: `3813f6826c943e3c805e53241811154ae11e6832`
- **License**: MIT License
- **Copyright**: Copyright (c) 2026 Sunil Gentyala
- **Components Integrated**:
  - `aegis/detectors/semantic.py` &rarr; `backend/app/services/plagiarism/semantic/semantic.py`
  - `aegis/detectors/ai_detector.py` &rarr; `backend/app/services/ai_detection/ai_detector.py`
  - `aegis/detectors/stylometric.py` &rarr; `backend/app/services/ai_detection/stylometric.py`
  - `aegis/detectors/ngram.py` &rarr; `backend/app/services/plagiarism/exact/ngram.py`
  - `aegis/detectors/self_plagiarism.py` &rarr; `backend/app/services/plagiarism/self_plagiarism.py`
  - `aegis/detectors/citation.py` &rarr; `backend/app/services/citations/citation_detector.py`
  - `aegis/detectors/citation_network.py` &rarr; `backend/app/services/citations/citation_network.py`

### MIT License Text
```
MIT License

Copyright (c) 2026 Sunil Gentyala

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 3. RefChecker
- **Upstream Repository**: https://github.com/markrussinovich/refchecker
- **Commit SHA**: `40892ed2081e0af26a4076942fa9e580a164d8c9`
- **License**: MIT License
- **Copyright**: Copyright (c) 2025 RefChecker
- **Components Integrated**:
  - `src/refchecker/utils/doi_utils.py` &rarr; `backend/app/services/reference_checker/utils/doi_utils.py`
  - `src/refchecker/utils/text_utils.py` &rarr; `backend/app/services/reference_checker/utils/text_utils.py`
  - `src/refchecker/checkers/openalex.py` &rarr; `backend/app/services/reference_checker/checkers/openalex.py`
  - `src/refchecker/checkers/crossref.py` &rarr; `backend/app/services/reference_checker/checkers/crossref.py`
  - `src/refchecker/checkers/semantic_scholar.py` &rarr; `backend/app/services/reference_checker/checkers/semantic_scholar.py`

### MIT License Text
```
MIT License

Copyright (c) 2025 RefChecker

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 4. UniqScan Notice
- **Upstream Repository**: https://github.com/hk151109/UniqScan
- **Commit SHA**: `0e8bbbfca8e599734942032f65011ce64c61902b`
- **Notice**: UniqScan was referenced exclusively for architectural inspection and research into multi-layered document scanning workflows. No source code or proprietary assets from UniqScan have been copied or redistributed in this codebase.
