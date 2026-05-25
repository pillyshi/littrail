# Littrail MVP Implementation Brief

この文書は、新規リポジトリ `littrail` を Claude Code で実装するための
指示書である。`littrail` は、AI が生成した文献調査レポートを起点に、
検証済み metadata、読書ノート、実装前の issue candidate までを Git 管理
可能な形で残すための Python CLI tool と workflow template を提供する。

## Claude Code への依頼

新規 GitHub repository `littrail` 上で、以下の MVP を実装してください。
作業は discovery、実装、テスト、README の動作例確認まで完了させてください。
不明点があっても、MVP の scope 内で合理的に決められるものは実装を進め、
判断を README または設計メモに記録してください。

## Product Goal

`littrail` は、ソフトウェアプロジェクトに次の research workflow を導入する
CLI tool である。

1. LLM が作成した literature survey を `research/reports/` に保存する。
2. 関係する論文の metadata を OpenAlex で検証して
   `research/catalog.yaml` に記録する。
3. 読む価値のある論文について `research/notes/` にノートを書く。
4. 実装または実験へ進めるアイデアを `research/ideas/` に整理する。
5. 合意した candidate を GitHub issue に昇格する。

MVP は、この workflow の導入と metadata 整合性の検査を自動化する。
論文の読解、アイデア判断、GitHub issue 作成の自動化は MVP の対象外とする。

## Core Principle

- Markdown report、note、idea、verified metadata は Git 管理する。
- PDF binary は `research/pdfs/` に保存し、Git 管理しない。
- AI 生成 report は情報源候補であり、metadata と一次本文を確認するまで
  根拠として扱わない。
- CLI はプロジェクトの実装 dependency ではなく、research workflow の
  補助 tool として利用できることを優先する。

## Package And CLI Name

- GitHub repository: `littrail`
- PyPI distribution name: `littrail`
- Python import package: `littrail`
- CLI executable: `littrail`

想定利用方法:

```bash
uvx littrail init
uvx littrail add-paper --doi 10.18653/v1/D19-1404
uvx littrail verify
uvx littrail check
```

CI などで継続的に検証するプロジェクトのみ、任意で dev dependency として
導入できる設計にする。

## MVP Commands

### `littrail init`

対象プロジェクトの current directory に workflow を導入する。

作成する構造:

```text
research/
  README.md
  catalog.yaml
  reports/
    .gitkeep
  notes/
    .gitkeep
  ideas/
    .gitkeep
  pdfs/
```

実行内容:

- `research/README.md` を template から作成する。
- 空の `research/catalog.yaml` を作成する。
- `reports/`, `notes/`, `ideas/`, `pdfs/` を作成する。
- repository root の `.gitignore` に `research/pdfs/` を追加する。
- `.gitignore` entry や既存 directory が存在しても重複や破壊的上書きを
  発生させない。

必要 option:

```bash
littrail init
littrail init --force
```

- default は既存の管理対象 file を上書きせず、衝突を明確に報告する。
- `--force` は Littrail が管理する template file の再生成を許可するが、
  ユーザーが作成した report、note、idea を削除してはならない。

### `littrail add-paper`

安定 identifier から OpenAlex metadata を取得し、catalog entry を追加する。

MVP で対応する入力:

```bash
littrail add-paper --doi 10.18653/v1/D19-1404
littrail add-paper --openalex W2970200208
```

必要な挙動:

- DOI または OpenAlex work ID のいずれか一つを受け取る。
- `pyalex` 経由で work metadata を取得する。
- title、authors、publication year、type、venue、DOI、OpenAlex ID を
  正規化して `research/catalog.yaml` に追加する。
- catalog 内で DOI または OpenAlex ID が一致する既存 entry がある場合は
  duplicate を作らず、既存 entry があることを報告して終了する。
- `key` は決定的に生成する。MVP では
  `<first-author-family-name>-<year>` を基本とし、衝突時は
  `-2`, `-3` の suffix を付与してよい。
- 新規 entry の workflow fields は次を default とする。

```yaml
relevance: to_classify
priority: to_review
rationale: ""
note_status: pending
pdf_status: missing
```

- `add-paper` は PDF をダウンロードしない。

### `littrail verify`

catalog に保存された metadata を OpenAlex の現在の record と照合する。

想定利用:

```bash
littrail verify
littrail verify --catalog research/catalog.yaml
```

必要な挙動:

- `papers` の各 entry の DOI または OpenAlex ID を用いて OpenAlex record を
  取得する。
- 少なくとも title、authors、year、DOI、OpenAlex ID を照合する。
- 完全一致でない場合は、差分を人間が判断できる形で表示する。
- 勝手に catalog を書き換えない。MVP の `verify` は read-only とする。
- 全 entry が確認できれば exit code `0`、不一致または取得不能があれば
  non-zero で終了する。
- verification が成功した場合に、利用者が手動で
  `verified_on` を更新する workflow としてよい。自動更新は MVP では不要。

### `littrail check`

ネットワークを必要とせず、repository 内の workflow 整合性を検査する。

想定利用:

```bash
littrail check
littrail check --catalog research/catalog.yaml
```

必要な検査:

- `research/catalog.yaml` が parse 可能で、最低限の schema を満たす。
- `note_status: drafted` の entry に対して
  `research/notes/<key>.md` が存在する。
- `pdf_status: cached` の entry に対して `local_pdf` が存在し、
  対応 file が存在する。
- `local_pdf` は `research/pdfs/` 配下だけを参照する。
- `research/pdfs/` が `.gitignore` に含まれる。
- Git repository 内で `research/pdfs/` 配下の PDF が tracked されて
  いないことを、利用可能な場合は `git ls-files` で検査する。
- 成功時 exit code `0`、問題があれば問題一覧を出力して non-zero で終了する。

## Catalog Schema

MVP の template は次の schema を採用する。YAML を人が編集しやすいことを
優先し、OpenAlex response をそのまま保存しない。

```yaml
catalog_version: 1
project: ""
verified_on: null
verification:
  provider: OpenAlex
  client: pyalex
source_reports: []

papers: []
```

各 paper entry:

```yaml
- key: yin-2019
  title: "Benchmarking Zero-shot Text Classification: Datasets, Evaluation and Entailment Approach"
  authors:
    - "Wenpeng Yin"
    - "Jamaal Hay"
    - "Dan Roth"
  year: 2019
  publication_type: article
  venue: "EMNLP-IJCNLP 2019"
  identifiers:
    doi: "10.18653/v1/D19-1404"
    openalex: "W2970200208"
  relevance: to_classify
  priority: to_review
  rationale: ""
  note_status: pending
  pdf_status: missing
```

Optional fieldsとして、少なくとも次を将来追加可能な parser にしておく。
MVP では生成・編集 UI は不要である。

```yaml
related_versions: []
cached_version: preprint
local_pdf: "pdfs/yin-2019.pdf"
```

## Template Files

package に以下の templates を同梱する。

```text
src/littrail/templates/
  research_README.md
  catalog.yaml
  paper-note.md
  issue-candidate.md
```

`research/README.md` template が記載する policy:

- `reports/`, `notes/`, `ideas/`, `catalog.yaml`, `pdfs/` の役割
- tracked artifacts と ignored PDF cache の区別
- report -> verify -> note -> candidate -> issue の workflow
- DOI、arXiv ID、ACL Anthology ID、OpenAlex ID などの安定識別子を残す方針

`paper-note.md` template:

```markdown
# <Citation Key>

## Citation

## Why It Matters For This Project

## Method

## Relevant Findings

## Limitations

## Actionable Findings

## Issue Candidate Impact

## Sources Checked
```

`issue-candidate.md` template:

```markdown
# Issue Candidate: <Title>

## Status

Draft.

## Motivation

## Evidence

## Proposed Scope

## Acceptance Criteria

## Out Of Scope

## Open Questions
```

## Python Project Requirements

実装は standard `src/` layout の Python package とする。

推奨構造:

```text
littrail/
  README.md
  LICENSE
  pyproject.toml
  src/
    littrail/
      __init__.py
      cli.py
      catalog.py
      openalex.py
      checks.py
      templates/
        research_README.md
        catalog.yaml
        paper-note.md
        issue-candidate.md
  tests/
    test_init.py
    test_add_paper.py
    test_verify.py
    test_check.py
```

Technical requirements:

- Python `>=3.11`.
- Runtime dependency に `pyalex` と YAML parser を含める。
- CLI framework は `typer` を第一候補とする。ただし、dependency を抑える
  明確な理由があれば `argparse` でもよい。
- Test runner は `pytest`。
- Lint / format は `ruff`。
- Type checking は `mypy` または `pyright` のどちらかを選び、
  README に記録する。
- package data として templates が wheel に含まれるよう設定する。
- `littrail --help` と各 subcommand の `--help` が動作する。

## OpenAlex And Authentication

`pyalex` を OpenAlex adapter として利用する。OpenAlex metadata response を
直接 CLI の domain model に漏らさず、catalog entry へ正規化する層を持つ。

API key の取り扱い:

- 環境変数 `OPENALEX_API_KEY` を読む。
- 値がある場合は `pyalex.config.api_key` に設定する。
- key を catalog、log、test fixture、Git tracked file に保存しない。
- `add-paper` と `verify` が key なしで API 制限または認証エラーになった
  場合、`OPENALEX_API_KEY` の設定方法を含む明確なエラーメッセージを出す。

ネットワークに依存するテストは禁止する。OpenAlex adapter は mock 可能な
境界に分離し、tests では固定 fixture を返す。

## Error Handling And Idempotency

- `init` は繰り返し実行しても `.gitignore` entry を重複させない。
- `add-paper` は DOI / OpenAlex ID duplicate を追加しない。
- malformed YAML、missing catalog、unknown identifier、OpenAlex fetch failure
  は stack trace ではなく行動可能な CLI error として表示する。
- `check` は可能な限り全問題を一度に列挙する。
- Windows / macOS / Linux で path を正しく扱えるよう `pathlib` を用いる。

## Out Of Scope For MVP

以下は初期 release に含めない。

- LLM API integration または report 自動生成
- PDF 自動ダウンロード
- PDF 本文抽出、citation scraping、full-text validation
- GitHub issue 作成・更新
- Markdown note の自動執筆
- DOI 以外の arXiv / ACL identifier 入力対応
- catalog の自動 migration
- CI workflow template の自動生成
- plugin / MCP server / Claude Code skill packaging

これらは MVP を別プロジェクトで運用してから issue 化する。

## Required Tests

最低限、次の tests を実装する。

### `init`

- 空 directory に期待する `research/` 構造が作成される。
- `.gitignore` に `research/pdfs/` が追加される。
- 二度実行しても `.gitignore` entry が重複しない。
- 既存 `research/README.md` を default では上書きしない。

### `add-paper`

- mocked OpenAlex work から正常な catalog entry が生成される。
- DOI 入力と OpenAlex ID 入力の双方が動く。
- duplicate DOI または OpenAlex ID が追加されない。
- author/year key の衝突時に deterministic suffix が付く。

### `verify`

- 一致する metadata で成功する。
- title、author、year、identifier の不一致を報告し non-zero となる。
- adapter failure のエラーが利用者向けに表示される。

### `check`

- 有効な minimal catalog で成功する。
- drafted note の file 欠損を検出する。
- cached PDF の file 欠損を検出する。
- `pdfs/` 外の `local_pdf` を拒否する。
- `.gitignore` entry 欠損を検出する。
- tracked PDF が存在する場合に検出する。

## README Requirements

public README には次を含める。

1. Littrail が解決する問題:
   AI-generated survey を、そのまま implementation の根拠にせず、
   verified literature trail として扱うこと。
2. workflow diagram または短い flow:

   ```text
   generated report -> verified catalog -> paper notes -> issue candidates -> GitHub issues
   ```

3. Installation:

   ```bash
   uvx littrail --help
   # or, for CI/team-managed installs:
   poetry add --group dev littrail
   ```

4. Quickstart:

   ```bash
   littrail init
   export OPENALEX_API_KEY=...
   littrail add-paper --doi 10.18653/v1/D19-1404
   littrail verify
   littrail check
   ```

5. `research/` directory policy と PDF ignore 方針。
6. API key は commit しない注意書き。
7. MVP の non-goals。

## Definition Of Done

MVP は次を満たした時点で完了とする。

- 新規 directory で `littrail init` が workflow template を導入できる。
- mocked unit tests で `add-paper`, `verify`, `check` の主経路と failure
  cases が確認できる。
- `ruff`、type checker、`pytest` が成功する。
- build した wheel を clean virtual environment に install し、
  `littrail --help` と `littrail init` が実行できる。
- README の quickstart が implementation と一致している。
- 実ネットワークでの smoke test は API key を environment variable で渡し、
  公開されている一件の DOI metadata を追加・検証する範囲に留める。
- PDF download、GitHub issue operation、LLM integration が MVP に
  混入していない。

## Suggested Implementation Order

1. 新規 repository を作成し、Python packaging、CLI entry point、
   lint/test/type-check 設定を用意する。
2. template files と `init` を実装し、idempotency tests を通す。
3. catalog domain model と YAML read/write を実装する。
4. OpenAlex adapter を `pyalex` で実装し、fixture で mock できる境界にする。
5. `add-paper` と duplicate handling を実装する。
6. `verify` を read-only command として実装する。
7. `check` を offline validation command として実装する。
8. README を実装済み interface に合わせて完成させる。
9. wheel install smoke test と OpenAlex DOI smoke test を行う。
10. MVP scope 外で見つかった要望を GitHub issues に記録する。

## Source Workflow Reference

この MVP は `semaxis` プロジェクトで試した以下の構成を一般化する。

```text
research/
  README.md
  reports/deep-research-report.md
  catalog.yaml
  notes/*.md
  ideas/*.md
  pdfs/                 # ignored local cache
```

この実例では、AI 生成 report を起点に OpenAlex / `pyalex` で metadata を
検証し、一次本文を読んだノートから scoped GitHub issues を作成した。
Littrail はこの作業の判断そのものではなく、再利用可能な構造と検証作業を
tool 化するものである。
