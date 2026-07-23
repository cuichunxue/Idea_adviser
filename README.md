# Idea Adviser — 発想法オーケストレーター

入力内容(お題・課題)に対して、以下の7つの発想法の中から適切なものを
論理的に選定し、その発想法のフレームワークに沿ってアイデアを網羅的に
洗い出すオーケストレーターです。

## 対応する発想法

| 発想法 | 主な効果 | 向いている状況 |
| --- | --- | --- |
| シックスハット法 | 事実・感情・リスク・利点・創造性を切り分けてバランスよく評価できる | 提案を多角的に評価したい・チームで合意形成したいとき |
| TRIZ | トレードオフ(技術的矛盾)を我慢せず両立させる発想が得られる | 技術的・工学的なジレンマがあるとき |
| 逆転思考 | 固定観念から脱却し、新たなチャンスを発見できる | 「当たり前」を疑いブレイクスルーが欲しいとき |
| ランダム発想法 | 予期しない・常識の枠を超えたユニークな発想が生まれる | アイデアが行き詰まり・マンネリ化しているとき |
| オズボーンのチェックリスト | 転用・適用/応用・変更・拡大・縮小・代用・再配置・逆転・結合の9視点で網羅的に検討できる | 既存の製品・業務を漏れなく見直したいとき |
| SCAMPER | オズボーンのチェックリストを7つの動詞に整理した汎用フレームワーク | 新商品・新機能を短時間で幅広く発想したいとき |
| ソクラテス応答法 | 前提・根拠・視点・含意を掘り下げ、批判的思考を促す | 自分の考えや主張を深く検証したいとき |

各発想法の定義・ステップ・選定用キーワードは `idea_adviser/methods.py` に、
TRIZ の40の発明原理は `idea_adviser/triz_principles.py` にまとまっています。

## 仕組み(オーケストレーターの流れ)

1. **選定 (`idea_adviser/selector.py`)**
   入力テキストを各発想法の「向いている状況」を表すキーワード集合と
   照合し、マッチ度をスコアリングする。どの発想法とも強くマッチしない
   場合は、汎用性の高い「オズボーンのチェックリスト」に既定でフォール
   バックする。選定理由(マッチしたキーワード)は常に結果に含まれる。

2. **展開 (`idea_adviser/methods.py`)**
   選ばれた発想法が持つステップ(シックスハット法なら6色の帽子、
   オズボーンのチェックリストなら9つの視点など)を、入力内容に
   合わせて具体的な問いへ展開する。

3. **アイデア生成 (`idea_adviser/generator.py`)**
   各ステップの問いに対して、実際のアイデアを生成する。
   - `TemplateGenerator`(既定・API不要): 発想法のロジック自体は
     最後まで実行し、埋めるべき欄を明示する。
   - `AnthropicGenerator`: Claude API を呼び出し、各ステップの問いに
     対する具体的なアイデアを自動生成する(`ANTHROPIC_API_KEY` が必要)。

4. **レポート (`idea_adviser/report.py`)**
   選定理由・発想法の効果・各ステップの問いとアイデアを Markdown レポート
   にまとめる。

## 使い方

### CLI

```bash
# 自動選定(オズボーンのチェックリストが選ばれる例)
python -m idea_adviser "既存の営業プロセスを見直して、漏れなく改善点を洗い出したい"

# 発想法を指定して強制的に使う
python -m idea_adviser "電動自転車の新機能を考えたい" --method scamper

# 上位2つの発想法を併用する
python -m idea_adviser "新商品のアイデアを考えたい" --top-k 2

# Claude API で実際にアイデアを生成する(ANTHROPIC_API_KEY が必要)
export ANTHROPIC_API_KEY=sk-ant-...
python -m idea_adviser "新商品のアイデアを考えたい" --use-llm
```

### ライブラリとして

```python
from idea_adviser import Orchestrator
from idea_adviser.report import to_markdown

orchestrator = Orchestrator()  # 既定は TemplateGenerator (API不要)
result = orchestrator.run("既存の営業プロセスを見直して、漏れなく改善点を洗い出したい")

print(result.primary.method.name_ja)  # -> オズボーンのチェックリスト
print(to_markdown(result))
```

Claude API でアイデアを自動生成したい場合:

```python
from idea_adviser import Orchestrator
from idea_adviser.generator import AnthropicGenerator

orchestrator = Orchestrator(generator=AnthropicGenerator())
result = orchestrator.run("電動自転車の新機能を考えたい", method_id="scamper")
```

## 開発

```bash
pip install -e ".[dev]"
pytest
```
