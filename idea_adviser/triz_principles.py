"""TRIZ の40の発明原理(参考リスト)。

矛盾解消のヒントとして提示するための短い参考データ。
オーケストレーターは、この一覧の中から矛盾の内容に応じて
候補をいくつか提示し、具体的なアイデア出しの呼び水として使う。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Principle:
    number: int
    name_ja: str
    name_en: str
    hint: str


TRIZ_PRINCIPLES: tuple[Principle, ...] = (
    Principle(1, "分割", "Segmentation", "全体を独立した部分に分ける"),
    Principle(2, "分離・抽出", "Extraction", "不要・邪魔な部分だけを取り除く/必要な部分だけを取り出す"),
    Principle(3, "局所性質", "Local Quality", "均一だった構造や性質を部分ごとに変える"),
    Principle(4, "非対称", "Asymmetry", "対称な形をあえて非対称にする"),
    Principle(5, "併合", "Merging", "同種・関連する部分や操作を1つにまとめる"),
    Principle(6, "汎用性", "Universality", "1つのものに複数の機能を持たせる"),
    Principle(7, "入れ子", "Nesting", "あるものを別のものの中に入れる/積み重ねる"),
    Principle(8, "重量補償", "Counterweight", "重さや力を、別の力で打ち消す・釣り合わせる"),
    Principle(9, "先取り反作用", "Prior Counteraction", "望ましくない影響が出る前に、あらかじめ逆の作用を加えておく"),
    Principle(10, "先取り作用", "Prior Action", "必要になる前に、あらかじめ必要な変更・準備をしておく"),
    Principle(11, "事前保護", "Cushion in Advance", "信頼性が低い部分に、あらかじめ対策・予備を用意しておく"),
    Principle(12, "等ポテンシャル", "Equipotentiality", "上げ下げの手間をなくし、条件を揃えておく"),
    Principle(13, "逆発想", "Inversion (The Other Way Round)", "動作・順序・向きを逆にする"),
    Principle(14, "曲面化", "Spheroidality – Curvature", "直線的・平面的なものを曲線・曲面にする"),
    Principle(15, "動的性", "Dynamicity", "固定的な構造を状況に応じて可動・可変にする"),
    Principle(16, "部分的・過剰な作用", "Partial or Excessive Action", "少し足りない/やり過ぎることで問題を単純化する"),
    Principle(17, "次元(方向)変換", "Another Dimension", "1次元的なものを2次元・3次元に展開する"),
    Principle(18, "機械的振動", "Mechanical Vibration", "振動を利用する/振動数を変える"),
    Principle(19, "周期的作用", "Periodic Action", "連続的な作用を間欠的・周期的な作用に変える"),
    Principle(20, "有用作用の継続", "Continuity of Useful Action", "アイドルタイムをなくし、常に有効な状態を保つ"),
    Principle(21, "高速実行", "Skipping", "有害・危険な過程を高速に通過させる"),
    Principle(22, "災いを転じて福となす", "Blessing in Disguise", "有害な要素・作用を逆に利用して利益に変える"),
    Principle(23, "フィードバック", "Feedback", "結果を測定し、プロセスにフィードバックする仕組みを入れる"),
    Principle(24, "仲介", "Mediator", "間に仲介物・仲介プロセスを挟む"),
    Principle(25, "セルフサービス", "Self-Service", "対象自身に補助的な機能・自己修復を持たせる"),
    Principle(26, "コピー", "Copying", "高価・壊れやすい実物の代わりに、簡易なコピーやモデルを使う"),
    Principle(27, "使い捨て", "Cheap Short-Living Objects", "高価で長寿命なものを、安価で使い捨てのものに置き換える"),
    Principle(28, "機械システムの代替", "Replacement of Mechanical System", "機械的な仕組みを光学・音響・電磁気などに置き換える"),
    Principle(29, "空気圧・水圧利用", "Pneumatics and Hydraulics", "固体部品を気体・液体で置き換える"),
    Principle(30, "柔軟な膜・薄膜", "Flexible Shells and Thin Films", "硬い構造を柔軟な膜・薄膜に置き換える"),
    Principle(31, "多孔質材料", "Porous Materials", "対象を多孔質にする、あるいは穴を追加要素として使う"),
    Principle(32, "色・光学的性質の変更", "Changing the Color", "見やすさ・扱いやすさのために色や透明度を変える"),
    Principle(33, "均質性", "Homogeneity", "関連するものを同じ材料・性質にする"),
    Principle(34, "排除と再生", "Discarding and Recovering", "役目を終えた部分を捨てる/使用中に自己再生させる"),
    Principle(35, "パラメータ変更", "Parameter Changes", "状態・濃度・温度などのパラメータを変える"),
    Principle(36, "相変化", "Phase Transition", "物質の相(固体・液体・気体など)の変化を利用する"),
    Principle(37, "熱膨張の利用", "Thermal Expansion", "熱による膨張・収縮を利用する"),
    Principle(38, "強い酸化剤の利用", "Strong Oxidants", "反応・作用を強めるために濃度や強度を高める"),
    Principle(39, "不活性雰囲気", "Inert Atmosphere", "通常の環境を不活性・中立な環境に置き換える"),
    Principle(40, "複合材料", "Composite Materials", "単一素材を複合材料に置き換える"),
)


def principle_by_number(number: int) -> Principle:
    for p in TRIZ_PRINCIPLES:
        if p.number == number:
            return p
    raise KeyError(number)
