# 기여 가이드

terms.kr에 관심 가져주셔서 감사합니다! 이 프로젝트는 AI/ML 분야의 용어를 한국어로 표준화하여, 개발자와 연구자들이 일관된 번역을 사용할 수 있도록 돕습니다.

## 프로젝트 소개

terms.kr는 인공지능과 머신러닝 분야의 영문 용어에 대한 한국어 번역을 표준화하는 오픈소스 사전입니다. 다양한 맥락에서 사용되는 용어들을 체계적으로 정리하고, 동일한 용어가 여러 의미로 사용될 때 각각의 정의를 명확히 구분합니다.

## 용어 데이터 구조

모든 용어 데이터는 `data/` 디렉토리에 JSON 형식으로 저장됩니다. 각 파일은 다음과 같은 구조를 따릅니다:

```json
[
  {
    "term": "영문 용어",
    "meanings": [
      {
        "korean": "한국어 번역",
        "definition": "용어의 정의",
        "examples": [
          {
            "en": "English example sentence.",
            "ko": "영어 예시의 한국어 번역.",
            "source": "https://출처-URL (선택)"
          },
          "기존 형식의 한국어 예시도 허용됩니다."
        ],
        "synonyms": ["동의어1", "동의어2"]
      }
    ]
  }
]
```

### 필수 필드
- `term`: 영문 용어
- `meanings`: 의미 배열 (최소 1개 이상)
  - `korean`: 한국어 번역
  - `definition`: 용어의 정의

### 선택 필드
- `examples`: 사용 예시 배열 (아래 두 형식 모두 지원)
  - 객체 형식 (권장): `{ "en": "영어 원문", "ko": "한국어 번역", "source": "출처 URL(선택)" }`
  - 문자열 형식: `"한국어 예시 문장"` (하위호환)
- `synonyms`: 동의어 배열
- `issueNumber`: 관련 GitHub Issue 번호
- `notes`: 번역 선택 근거나 편집 메모

## 기여 절차

1. **Fork** 이 저장소를 본인의 GitHub 계정으로 Fork합니다.

2. **브랜치 생성** 작업할 브랜치를 생성합니다.
   ```bash
   git checkout -b add-new-terms
   ```

3. **수정** 용어를 추가하거나 수정합니다.
   - 기존 파일에 용어 추가: `data/` 디렉토리의 적절한 파일 수정
   - 새 파일 생성: `data/index.json`에 파일명도 추가해야 합니다

4. **Pull Request** 변경사항을 커밋하고 PR을 생성합니다.
   ```bash
   git add .
   git commit -m "Add: 새로운 용어 추가"
   git push origin add-new-terms
   ```

## PR 전 체크리스트

Pull Request를 제출하기 전에 다음 사항을 확인해주세요:

- [ ] JSON 파일이 유효한 형식입니다 (문법 오류 없음)
- [ ] 모든 필수 필드(`term`, `meanings[].korean`, `meanings[].definition`)를 포함합니다
- [ ] 새 알파벳 파일을 추가했다면 `data/index.json`에도 파일명을 추가했습니다
- [ ] `npm run build` 가 성공합니다
- [ ] 추가한 용어의 정의가 명확하고 정확합니다

## 번역 문서 사용 통계에 기여하기

용어 상세 페이지의 표기 출현 통계에 새 번역 문서 출처를 추가하려면 [사용 통계 문서](docs/usage-statistics/README.md)와 [출처 추가 절차](docs/usage-statistics/adding-source.md)를 참고해주세요. 사람과 에이전트가 동일한 집계·검증 기준을 따르도록 설계와 실행 절차를 함께 관리합니다.

## 로컬 개발 방법

프로젝트를 로컬에서 실행하여 변경사항을 확인할 수 있습니다:

```bash
# 의존성 설치
npm install

# 개발 서버 실행 (http://localhost:5173)
npm run dev

# 린트
npm run lint

# 의존성 보안 점검
npm run audit:security

# 데이터 검증
npm run validate:data

# 프로덕션 빌드
npm run build

# 빌드 결과 미리보기
npm run preview
```

## 질문이나 제안사항

이슈를 통해 언제든지 질문하거나 제안사항을 남겨주세요. 여러분의 기여가 terms.kr를 더 나은 프로젝트로 만듭니다!
