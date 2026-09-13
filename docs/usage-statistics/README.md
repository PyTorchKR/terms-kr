# 번역 문서에서의 쓰임

용어 상세 페이지에 한국어 표기가 번역 문서에서 나타난 횟수와 확인 가능한 근거를 제공한다. 사전의 대표 번역·의미·동의어를 통계로 바꾸거나 추천 순위로 재정렬하지 않는다.

**새 출처를 추가하려면 [출처 추가 가이드](adding-source.md)를 먼저 읽는다.** 사람과 에이전트가 같은 절차를 사용한다. 저장소 전체의 에이전트 지침은 변경하지 않는다.

## 무엇을 세는가

통계 단위는 `출처 × 문서 × 영문 용어 항목 × 한국어 표기`다. 영문 용어는 사전 항목의 식별자이며, 실제 검색은 한국어 문자열로 한다. 영문 원문과 한국어 문장을 정렬하거나 문맥의 의미를 판별한 번역 빈도가 아니다.

예를 들어 `gradient`의 후보에 `경사`가 있으면 `경사하강법` 안의 `경사`도 센다. 같은 표기를 여러 사전 항목이 공유하면 각 항목에 독립적으로 집계한다. 따라서 모든 용어의 횟수를 합쳐 문서 전체의 고유 용어 수로 해석하면 안 된다. 문서 수 또한 표기 행끼리 더하지 않는다.

## 작은 정적 파이프라인

1. 출처 설정과 사전·추가 표기를 읽는다.
2. 선택한 출처의 로컬 Git 저장소에서 설정에 고정한 커밋을 읽는다.
3. 문서 목록·포함 조건·blob SHA를 확인한다. 변경된 본문만 다시 세고, 삭제 문서는 해당 출처의 새 상태에서 빠진다.
4. 각 출처의 호환되는 상태를 합쳐 공개 JSON과 스캔 목록을 만든다.
5. 사이트 빌드에서 데이터·해시·합계·근거를 검증한다. 상세 페이지에서만 공개 통계 JSON을 읽는다.

DB, 백엔드, 큐, 예약 실행, 크롤러는 없다. 집계 도구는 원격 fetch·commit·push·배포를 하지 않는다. 문서를 코드로 실행하지 않는다. Git에 추적되지 않은 파일과 체크아웃의 미커밋 변경도 입력으로 사용하지 않는다.

### 파일 역할

| 경로 | 역할 | 직접 편집 |
| --- | --- | --- |
| `data/*.json` | 기존 사전; 모든 의미의 한국어 번역·동의어가 기본 검색 후보 | 기존 사전 기여 절차 사용 |
| `usage/sources.json` | 출처 ID·커뮤니티·저장소·커밋·경로·어댑터·제외 조건 | 가능 |
| `usage/variants.json` | 추가 검색 표기, 미출현이어도 확인할 후보 목록 | 검토 후 가능 |
| `scripts/usage-statistics/usage_core.py` | 공통 Markdown 정제, 표기 매칭, 문서 캐시 갱신 | 규칙 변경 시 버전 관리 |
| `scripts/usage-statistics/rst_source.py` | reST·sphinx-gallery 본문 블록 추출; 매칭 규칙은 갖지 않음 | 규칙 변경 시 버전 관리 |
| `scripts/usage-statistics/update_usage_counts.py` | 출처 목록 확인, 선택 집계, 합산·출력 | 새 형식이 필요할 때만 확장 |
| `usage/state/<source-id>.json` | 출처별 문서 횟수·첫 근거·해시·커밋 | 생성 파일; 숫자 수기 수정 금지 |
| `public/usage/term-usage.json` | 상세 페이지용 합산 결과 | 생성 파일 |
| `public/usage/scanned.md` | 포함·제외 문서, 사유, 커밋, 집계 시각 | 생성 파일 |
| `scripts/usage-statistics/validate-usage-data.mjs` | Python/원문 저장소 없이 빌드 결과의 정합성 검사 | 스키마 변경 시 함께 수정 |

상태 파일을 출처별로 나눈 이유는 다른 커뮤니티의 원문 저장소 없이 자신의 출처만 갱신하고 검토하기 위해서다. 공개 합산 파일은 하나로 유지한다. 용량이 실제 문제가 되기 전에는 DB나 별도 배포 서비스로 확장하지 않는다.

### 커뮤니티와 출처의 화면 표시

통계 영역은 용어 상세 페이지의 **한 표**로 유지한다. PyTorch와 Hugging Face KREW를 별도 표·탭·페이지로 나누지 않는다.

- `community`: 참여 커뮤니티 표시 이름. HF 출처는 `Hugging Face KREW`, PyTorch 출처는 `PyTorch`로 통일한다. **해당 용어의 출현 근거가 있는 출처**의 커뮤니티만 중복 제거해 영역 상단에 ` · `로 이어 표시한다. 기준은 출처 상태 `collected`와 해당 용어의 `bySource[id].documentCount > 0`이다. HF 근거만 있으면 HF만, PyTorch 근거만 있으면 PyTorch만, 둘 다 있으면 두 이름을 표시한다. 어디에도 근거가 없으면 이름 영역을 숨긴다.
- `label`: 문서 출처 컬럼 이름. 현재 컬럼은 `Transformers`, `smolagents`, `HF Blog`, `PyTorch Tutorials`, `PyTorch Hub`, `PyTorch Blog`이며 새 출처의 label이 자동 추가된다. 표시 순서는 공개 JSON의 출처 순서이며 생성기는 설정 배열 순서를 유지한다.
- `id`: 캐시·숫자·근거를 연결하는 영구 키. 표시 이름이 아니므로 이름을 바꾸려고 ID를 변경하지 않는다.

커뮤니티 이름과 출처 컬럼은 모두 데이터에서 생성한다. 현재 2단 그룹 헤더나 커뮤니티별 소계는 없으며, 단순 출처 추가에 이를 구현할 필요는 없다. 전체 합계는 수집된 모든 출처의 합이다. 출처 간 같은 문서의 중복은 자동 제거하지 않으므로 중복 코퍼스를 등록하지 않는다.

미등록 커뮤니티의 이름이나 가상 통계는 표시하지 않는다. 설정만 등록하고 아직 수집하지 않은 출처는 컬럼에 `—`가 표시되지만 상단 커뮤니티 이름에는 포함하지 않는다. 이름 필터는 출처 컬럼·집계 범위 설명·전체 합계에 영향을 주지 않는다. 포함 문서가 전부 제외된 수집 출처는 출처별 셀에 0이 나올 수 있으므로 아래 범위 검증 없이 미출현으로 해석하지 않는다.

### 표기별 검색 관심도 (Google Trends)

상세 페이지 아래쪽의 **표기별 검색 관심도**는 같은 후보 목록(`terms[term].variants`)을 Google Trends 임베드로 비교한다. 문서 출현이 많은 표기부터 정렬해 최대 5개를 기본 선택하며, 나머지 후보도 직접 선택해 볼 수 있다. Google Trends가 한 차트에서 5개까지만 비교하기 때문에 남은 후보는 선택을 바꿔 확인한다.

- 이 영역은 집계 결과를 만들지 않는다. 횟수·근거·상태 어디에도 영향을 주지 않으며, 검색 관심도는 번역의 정확성이나 표준 표기를 증명하지 않는다.
- 차트는 `https://trends.google.com`의 iframe이다. 방문자의 브라우저가 Google에 직접 요청하며(`loading="lazy"`로 화면에 보일 때 요청), 우리 쪽으로 돌아오는 데이터는 없다. 브라우저 정책상 iframe 내부의 성공·실패를 페이지가 판별할 수 없으므로 실패 시 안내와 외부 링크를 함께 제공한다.
- 임베드 주소는 `src/utils/trendsEmbed.ts`가 만들고 `tests/trends-embed.test.mjs`가 형식을 고정한다. 지역은 대한민국, 기간은 최근 5년, 웹 검색으로 고정한다.

## 집계 규칙: `ko-surface-v2.1`

- 파서: Markdown은 `markdown-it-py==3.0.0`(CommonMark와 표 지원), reST와 sphinx-gallery `.py`는 `rst_source.py`의 블록 추출기다. `.mdx`, 노트북, HTML은 어느 쪽에도 억지로 넣지 않는다.
- 포함: 제목, 문단, 목록, 인용문, 표 셀의 텍스트와 링크 표시 문구.
- 제외: frontmatter, fenced/indented/inline 코드, HTML 주석, 이미지·이미지 대체 텍스트, URL, raw HTML 블록, 자동 문서 앵커/API 지시문. 임의 HTML/MDX를 실행하지 않는다.
- 정규화: Unicode NFC, 소문자화, 연속 공백 축약. 띄어쓰기와 하이픈을 임의로 없애지 않는다.
- 매칭: 부분 문자열 검색. 같은 용어 안에서는 왼쪽부터 찾고, 같은 시작 위치에서는 긴 후보를 먼저 선택해 겹침을 막는다. 다른 용어 항목끼리는 독립적이다.
- 경계: 서로 다른 문단·표 셀·제외된 인라인 코드의 양쪽을 합쳐 가짜 표기를 만들지 않는다.
- 후보: 모든 `meanings[].korean`, `synonyms[]`, `usage/variants.json`의 `extraVariants`. 정규화 후 중복을 제거한다. 추가 후보는 사전의 권장 번역에 자동 등록되지 않는다.
- 한글 음절이 없는 영문·약어 후보는 `unsupportedVariants`로 구분하며, 0회라고 표시하지 않는다.
- reST 본문: 제목·문단·목록·표 셀·링크 표시 문구와 `note`·`warning`·`grid` 같은 본문 지시문의 내용을 포함한다. 코드 블록·리터럴 블록·doctest·주석·이미지·`math`, 인라인 리터럴(``` `` ```), 역할(`:class:`, `:ref:` 등)의 내용, 하이퍼링크 대상, 목록에 없는 지시문의 본문은 제외한다.
- sphinx-gallery `.py`: 모듈 독스트링과 `####`(20자 이상) 또는 `# %%` 구분선 뒤의 주석 블록만 본문이다. 나머지 코드·코드 주석·함수 독스트링은 제외한다. 구분 규칙은 이 코퍼스가 사용하는 sphinx-gallery 0.19.0의 분할과 같다.
- 근거: 문서·표기별 전체 횟수와 **첫 출현** 주변 문맥만 저장한다. GitHub 링크의 행 범위는 해당 문단·표 영역이지 정확한 문자 위치가 아니다. 문맥은 검색에 사용한 정규화 텍스트다.

정제·검색 방식이 달라지면 `usage_core.py`의 `RULE`을 올리고 테스트 및 전체 출처를 재집계한다. 서로 다른 집계 규칙의 숫자를 같은 표에서 합하지 않는다. 새 형식의 추출기를 추가하는 것만으로는 기존 형식의 본문·매칭이 달라지지 않으므로 `RULE`을 올리지 않고 해당 어댑터 버전으로 관리한다. 이미 수집한 출처의 본문 추출이 달라지는 변경이라면 `RULE`을 올린다.

### 포함 범위와 어댑터

출처별로 포함 범위를 명시한다. 현재 어댑터는 다음 넷이다.

- `paired-markdown`: 번역 root 아래 `.md`를 찾고, 같은 상대 경로의 영문 일반 파일이 있는지 확인한다. 원문과 번역이 서로 다른 Git 저장소여도 된다. symlink는 따라가지 않는다.
- `krew-blog`: KREW의 `_posts` 규칙을 사용한다. 공식 HF 블로그 원문 연결, 번역 고지, 영문 파일을 확인하고 `translation_status: draft`를 제외한다. 누락된 상태 필드는 기존 정책대로 게시본으로 취급한다.
- `paired-sphinx`: `paired-markdown`과 같은 경로 대응을 `.rst`와 sphinx-gallery `.py`에 적용한다. `root`를 배열로 적으면 형제 문서 디렉터리 여러 개를 한 출처로 묶고, 각 번역 root는 같은 순서의 영문 root와 짝지어진다. 모듈 독스트링이 없는 `.py`는 sphinx-gallery 문서가 아니므로 `not-a-gallery-document`로 제외한다.
- `pytorch-blog`: pytorch.kr의 `_posts` 전용이다. frontmatter의 `org_link`가 `https://pytorch.org/blog/`를 가리키고 `category`에 `translation`이 있는 글을 포함하며, 날짜 접두사가 서로 달라 URL 슬러그로 영문 글을 찾는다. 다른 블로그에 이름만 바꿔 재사용하지 않는다.

`root`는 디렉터리 경로이고, 문서가 저장소 루트에 있으면 `.`으로 적는다. 루트 범위는 저장소의 모든 파일이 후보가 되므로 `exclude`로 문서가 아닌 파일을 함께 지정한다.

네 어댑터 모두 `exclude`에 매칭되는 문서를 제외 사유와 함께 기록한다. glob은 **저장소 기준 전체 경로에 대한 Python `fnmatchcase`**이며 `*`가 `/`도 매칭한다. Gitignore 패턴 문법이 아니다. 해당 형식의 파일이 root 아래에서 모두 없어지거나 경로가 잘못되면 집계가 실패한다. 전체 코퍼스 제거는 설정·상태 제거를 명시적으로 리뷰하는 별도 작업이다.

영문 대응의 존재는 번역 코퍼스를 정하는 조건이지 문장별 번역 정확성의 증명이 아니다. 포함된 문서 중 아직 번역되지 않은 부분이 있어도 한국어 표기가 없으면 0회로 집계된다. 새 저장소의 구조·형식을 확인하기 전에는 같은 경로나 어댑터를 사용할 수 있다고 가정하지 않는다.

영문 원문이 Git 저장소를 떠난 경우는 `pytorch-blog`에서만 예외로 다룬다. 이 블로그는 frontmatter가 원문 주소를 명시하고 본문이 문단마다 영문 원문을 인용문으로 함께 싣기 때문에 번역 근거가 문서 안에 있다. 영문 파일이 남아 있으면 `paired-translation`으로 `enPath`까지 기록하고, 원문이 웹에만 있으면 `linked-translation`으로 구분한다. 다른 출처에 이 예외를 확대 적용하지 않는다.

## 데이터 계약: schemaVersion 2

### 출처별 상태

`usage/state/<id>.json`에는 다음을 저장한다.

- `source`: 출처 설정, 한국어 및 영문 원본의 정확한 커밋.
- `documents`: `<source-id>:<repository-relative-path>`를 키로 한 문서별 기록.
- 문서 기록: `blobSha`, `eligible`, `reason`, `enPath`, `countedAt`, `counts[term][spelling]`, `evidence[term][spelling]`. 어댑터별 추가 필드는 포함 판단의 근거다(`krew-blog`의 `translationStatus`, `pytorch-blog`의 `originalLink`).
- `reason`: 포함은 `paired-translation`·`linked-translation`, 제외는 `english-missing`·`draft`·`translation-notice-missing`·`not-a-gallery-document`·`excluded-by-config`다. 포함 사유는 어떤 근거로 번역 문서라고 판단했는지를 나타내며 `public/usage/scanned.md`에 그대로 남는다.
- `candidateHash`, `countingRuleVersion`, `policyHash`, `configHash`: 캐시 사용 및 출처 간 합산의 호환성 기준.
- `inputHash`: 커밋·목록·후보·포함 정책의 동일성. `snapshotId`: 상태 전체의 무결성 해시.

파일 수정 시각은 변경 감지에 사용하지 않는다. 커밋을 이동해도 본문 blob과 포함 조건이 같으면 문서별 결과를 재사용한다. `generatedAt`은 해당 출처 스냅샷의 생성 시각이고, `countedAt`은 각 본문을 마지막으로 실제 센 시각이다. 어느 것도 원문 작성·번역 날짜나 최신성 보증을 의미하지 않는다.

### 공개 결과

`term-usage.json`은 다음을 포함한다.

- `sources[id]`: 동적으로 UI에 표시할 이름·커뮤니티·커밋·집계 시점·상태.
- `corpus[id]`: 스캔·포함 문서 수.
- `terms[term]`: 표기별 횟수·중복 제거 문서 수·출처별 합계·문서별 첫 근거.
- `snapshotId`: 설정·검색 후보·출처별 스냅샷 ID를 묶은 식별자.

상태는 다음처럼 구분한다.

- `sources[id].status == not-collected`: 아직 상태 파일이 없는 출처. 해당 출처 수치는 `null`, UI는 `—`.
- 용어 `status == no-match`: 포함된 문서가 있고 지원하는 표기를 검색했으나 출현이 없음.
- 용어 `status == not-collected`: 지원 표기는 있으나 어느 출처에도 집계에 포함된 문서가 없음. 모든 문서가 제외된 경우도 해당한다.
- `unsupported`: 검색 가능한 한글 표기가 없음.
- 읽기·검증 실패: 결과를 0회나 미수집으로 덮지 않고 실행 실패로 처리한다. UI의 네트워크 오류도 미출현과 구분한다.

전체 횟수는 **집계된 출처만의 합계**다. 미수집 출처가 있거나 출처별 시점이 다르면 완전한 동시점 통계가 아니다. 출현한 용어는 항상 표시하고, 미출현 항목은 `showWhenUnmatched` 목록에 있는 것만 표시한다. 이 목록은 초기 HF 후보의 리뷰 경험을 보존하기 위한 표시 정책이며 집계 횟수를 바꾸지 않는다.

## 재현·갱신

기본 사이트 빌드에는 Node 의존성과 커밋된 상태·공개 JSON만 필요하다. Python과 문서 체크아웃은 재집계할 때만 필요하다.

```bash
python3 -m pip install -r scripts/usage-statistics/requirements.txt
npm run update:usage -- --sources-dir /path/to/document-checkouts
npm run test:usage
python3 scripts/usage-statistics/update_usage_counts.py --check-full --sources-dir /path/to/document-checkouts
npm run build
```

특정 출처만 갱신하려면:

```bash
npm run update:usage -- --source transformers --sources-dir /path/to/document-checkouts
python3 scripts/usage-statistics/update_usage_counts.py --source transformers --check-full --sources-dir /path/to/document-checkouts
```

`--source`는 여러 번 지정할 수 있다. 설정한 커밋이 로컬 저장소에 있어야 한다. 스크립트가 최신 main을 가져오거나 임의로 추적하지 않으므로, 최신화는 작성자가 커밋을 선택하고 `sources.json`의 `ref`를 변경하는 별도 단계다.

원문 없이 기존 상태만 합산하려면:

```bash
npm run update:usage -- --aggregate-only
npm run validate:usage
```

### 갱신 시 보장과 제한

- 새 문서·수정 문서는 집계, 삭제는 제거, 이동은 삭제+추가로 처리한다. 마지막 합계는 남은 문서별 결과를 다시 더한다.
- 선택하지 않은 출처는 로컬 문서 저장소를 열지 않고 커밋된 상태를 재사용한다.
- 후보 또는 공통 규칙이 바뀌면 **이미 수집된 모든 출처**를 같은 새 기준으로 재집계해야 한다. 일부만 갱신해 나머지가 오래된 경우 저장 전에 실패한다. 이 경우 `--aggregate-only`로 우회할 수 없다.
- 새 출처는 상태가 없어도 기존 숫자를 보존하고 미수집으로 등록할 수 있다. 출처 설정을 삭제하면 그 출처는 합계에서 제외된다. 삭제는 의도적인 코퍼스 변경이므로 관련 상태 파일도 PR에서 정리한다.
- 동일 입력은 파일·해시·집계 시각을 바꾸지 않는다. `--check-full`은 선택한 출처를 캐시 없이 다시 세어 비교하고 파일을 쓰지 않는다. 선택하지 않은 출처는 정합성만 확인하며 전체 재스캔했다고 주장하지 않는다.
- `--check-full`은 설정한 범위의 재현성 검사이며 범위의 타당성을 보장하지 않는다. 모든 영문 대응 누락 등으로 포함 문서가 0개여도 성공할 수 있다. 게시 전에 [출처 추가 가이드의 범위 검증](adding-source.md#5-검증-체크리스트)으로 포함 수·제외 사유를 반드시 확인하고 예상하지 못한 전체 제외나 급감은 중단한다.
- 계산 및 검증 성공 후 임시 파일을 교체한다. **파일 하나씩은 원자적이지만 전체 파일 묶음의 교체는 트랜잭션이 아니다.** 중단되면 집계 명령을 재실행하고 빌드 검사로 일관성을 확인한다. 출력 파일을 쓰는 프로세스는 체크아웃당 하나만 실행한다.
- 다수가 작업할 때는 별도 브랜치·체크아웃을 사용한다. 출처별 상태를 먼저 합치고 공개 JSON은 `--aggregate-only`로 재생성한다. 거대한 생성 파일의 줄을 수동 병합하지 않는다.

## 등록된 스냅샷

사전 263개 중 출현을 확인한 용어는 237개다(HF만 집계하던 시점 194개). 출처를 추가할 때마다 전체 재집계와 캐시 결과 비교, 동일 입력 재실행, 해당 출처 단독 갱신을 검증한다.

### Hugging Face KREW

2026-09-06에 모아 둔 고정 커밋을 사용한다. 출처 공통화 후 기존 로컬 Step 2와 모든 용어별 횟수·문서 수·첫 출현 근거가 같음을 확인했다. 스캔 254개, 포함 205개(스캔/포함): Transformers 186/173, smolagents 17/17, HF Blog 51/15.

### PyTorch

pytorch.kr이 게시하는 번역 문서를 튜토리얼·허브·블로그 세 출처로 나누어 등록했다. 셋 다 `community: "PyTorch"`이며 한 표의 서로 다른 컬럼으로 표시된다.

| 출처 | 한국어 저장소 | 영문 원문 | 문서(스캔/포함) |
| --- | --- | --- | --- |
| 튜토리얼 `pytorch-tutorials` | [tutorials-kr@84b7db6e](https://github.com/PyTorchKR/tutorials-kr/tree/84b7db6e020c098cf38a0dfaf036007c24057bb1) | [pytorch/tutorials@c4d9d93](https://github.com/pytorch/tutorials/tree/c4d9d935655cf754c90d5ce7f37024afc015f054) | 269 / 250 |
| 허브 `pytorch-hub` | [hub-kr@39749bdf](https://github.com/PyTorchKR/hub-kr/tree/39749bdf8fe853e1a74ab1b3a03332168d31eb3f) | [pytorch/hub@c7895df7](https://github.com/pytorch/hub/tree/c7895df70c7767403e36f82786d6b611b7984557) | 58 / 46 |
| 블로그 `pytorch-blog` | [pytorch.kr@dbc281dc](https://github.com/PyTorchKR/pytorch.kr/tree/dbc281dc498500109db8598180d5c3dcdaf43674) | [pytorch.github.io@9104164e](https://github.com/pytorch/pytorch.github.io/tree/9104164e5c459899b49f2ef269cb2c0143e0f703) | 48 / 45 |

- **튜토리얼**(tutorials.pytorch.kr): 범위는 `beginner_source`·`intermediate_source`·`advanced_source`·`recipes_source`·`unstable_source`의 `.rst`와 sphinx-gallery `.py`다. 생성물인 `docs/`·`unstable/`과 저장소 루트의 색인 `.rst`는 중복 코퍼스이므로 넣지 않는다. 포함 250개 중 123개에 한국어가 있고 127개는 아직 영문 그대로여서 0회로 집계된다(`unstable_source`는 25개 전부 미번역). 제외는 `english-missing` 14개와 모듈 독스트링이 없는 코드 파일 5개(`not-a-gallery-document`)다. 영문 커밋은 저장소가 번역 기준으로 기록해 둔 값이다(`README.md`, `.migration_state.json`). 두 저장소 모두 BSD 3-Clause.
  - `english-missing` 14개 중 12개는 영문이 삭제되었거나 8~11줄짜리 이전 안내만 남은 과거 번역이다. 나머지 2개(`beginner_source/introyt/introyt_index.rst`, `intermediate_source/torchvision_tutorial.rst`)는 영문이 같은 이름의 `.py`로 바뀐 경우다. 특히 뒤의 파일은 한국어 3,247자가 남아 있지만 사이트가 빌드하는 것은 같은 이름의 `.py`(영문, 포함·0회)이므로 게시되지 않는 잔여 파일이다. 확장자만 바꿔 짝을 찾으면 같은 문서를 두 번 세게 되므로 현재 규칙을 유지한다.
- **허브**(pytorch.kr/hub): pytorch.kr이 `_hub` 서브모듈로 싣는 모델 카드다. 문서가 저장소 루트에 있어 `root`는 `.`이고, `exclude`는 사이트 `_config.yml`이 허브 컬렉션에서 빼는 문서와 Jekyll이 무시하는 dot 디렉터리를 그대로 옮긴 것이다(10개). 영문에서 사라진 silero-vad 카드 2개는 `english-missing`이다. 포함 46개 중 37개에 한국어가 있고 9개는 아직 영문 그대로여서 0회로 집계된다. **원문·번역 저장소 모두 LICENSE 파일이 없다.** 저장하는 것은 한국어 발췌와 커밋 링크이며, 등록은 저장소를 운영하는 커뮤니티의 요청에 따른 것이다.
- **블로그**(pytorch.kr/blog): `_posts`의 번역 글이다. 포함 45개 중 14개는 영문 Markdown이 남아 있어 `paired-translation`, 31개는 원문이 웹에만 있어 `linked-translation`이다. 업스트림이 2025-08-08 커밋 [`1cd595f7`](https://github.com/pytorch/pytorch.github.io/commit/1cd595f70eaa2577c8a0f619ec0fb28f5c063ab4)에서 `_posts`를 삭제하고 새 사이트로 옮겼기 때문에 그 직전 커밋을 영문 기준으로 고정했다. 한국어 자체 글 3개는 `english-missing`으로 제외된다. pytorch.kr은 BSD 3-Clause.

한국어 표기가 본문에 있어도 frontmatter(제목·요약)와 raw HTML 블록은 모든 Markdown 출처에서 동일하게 제외한다.

이 수치는 범위·규칙이 달랐던 초기 후보 채집 통계와 증감을 직접 비교하지 않는다. 출처마다 기준 커밋과 집계 시점이 다르므로 동시점 통계가 아니다. 정의·번역 추천과 표기 빈도 통계를 분리해서 리뷰한다.
