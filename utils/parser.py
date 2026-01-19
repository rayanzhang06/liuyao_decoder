"""卦象输入解析器"""
import re
from typing import Dict, List, Optional
from loguru import logger

from storage.models import HexagramInput, LineInfo


class HexagramParser:
    """卦象解析器"""

    @staticmethod
    def parse_text(text: str) -> HexagramInput:
        """
        解析卦象文本为结构化数据

        Args:
            text: 卦象文本（符合设计文档格式）

        Returns:
            HexagramInput: 解析后的卦象数据
        """
        logger.info("开始解析卦象文本")

        # 提取各个部分
        system_name = HexagramParser._extract_system_name(text)
        datetime_str = HexagramParser._extract_datetime(text)
        question = HexagramParser._extract_question(text)
        ganzhi = HexagramParser._extract_ganzhi(text)
        kongwang = HexagramParser._extract_kongwang(text)
        ben_gua_info = HexagramParser._extract_ben_gua(text)
        bian_gua_info = HexagramParser._extract_bian_gua(text)
        lines = HexagramParser._extract_lines(text)

        hexagram = HexagramInput(
            original_text=text.strip(),
            system_name=system_name,
            datetime=datetime_str,
            question=question,
            ganzhi=ganzhi,
            kongwang=kongwang,
            ben_gua=ben_gua_info['full'],
            ben_gua_name=ben_gua_info['name'],
            ben_gua_gong=ben_gua_info['gong'],
            ben_gua_index=ben_gua_info['index'],
            ben_gua_type=ben_gua_info['type'],
            bian_gua=bian_gua_info['full'],
            bian_gua_name=bian_gua_info['name'],
            bian_gua_gong=bian_gua_info['gong'],
            bian_gua_index=bian_gua_info['index'],
            lines=lines
        )

        logger.info(f"卦象解析成功: {hexagram.ben_gua_name} → {hexagram.bian_gua_name}")
        return hexagram

    @staticmethod
    def _extract_system_name(text: str) -> str:
        """提取系统名称"""
        match = re.search(r'(.*?)·六爻排盘', text)
        if match:
            return match.group(1).strip()
        return "未知系统"

    @staticmethod
    def _extract_datetime(text: str) -> str:
        """提取占卜时间"""
        match = re.search(r'时间：(.+)', text)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _extract_question(text: str) -> str:
        """提取占问问题"""
        match = re.search(r'占问：(.+)', text)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _extract_ganzhi(text: str) -> Dict[str, str]:
        """提取干支信息"""
        ganzhi = {}

        # 提取年柱
        match = re.search(r'([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])年', text)
        if match:
            ganzhi['year'] = match.group(1)

        # 提取月柱
        match = re.search(r'([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])月', text)
        if match:
            ganzhi['month'] = match.group(1)

        # 提取日柱
        match = re.search(r'([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])日', text)
        if match:
            ganzhi['day'] = match.group(1)

        # 提取时柱
        match = re.search(r'([甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥])时', text)
        if match:
            ganzhi['hour'] = match.group(1)

        return ganzhi

    @staticmethod
    def _extract_kongwang(text: str) -> Dict[str, str]:
        """提取空亡信息"""
        kongwang = {}
        matches = re.findall(r'([子丑寅卯辰巳午未申酉戌亥]+)空', text)
        for i, match in enumerate(matches):
            if i == 0:
                kongwang['year'] = match
            elif i == 1:
                kongwang['month'] = match
            elif i == 2:
                kongwang['day'] = match
            elif i == 3:
                kongwang['hour'] = match

        return kongwang

    @staticmethod
    def _extract_ben_gua(text: str) -> Dict[str, str]:
        """提取本卦信息"""
        # 示例：本卦：火天大有/乾宫·8 (归魂)
        match = re.search(r'本卦：(.+?)/(.+?)·(\d+)\s*\((.+?)\)', text)
        if match:
            return {
                'full': f"{match.group(1)}/{match.group(2)}",
                'name': match.group(1).strip(),
                'gong': match.group(2).strip(),
                'index': int(match.group(3)),
                'type': match.group(4).strip()
            }

        # 备用格式：本卦：火天大有
        match = re.search(r'本卦：(.+)', text)
        if match:
            name = match.group(1).strip()
            return {
                'full': name,
                'name': name,
                'gong': '未知',
                'index': 0,
                'type': '未知'
            }

        return {
            'full': '未知',
            'name': '未知',
            'gong': '未知',
            'index': 0,
            'type': '未知'
        }

    @staticmethod
    def _extract_bian_gua(text: str) -> Dict[str, str]:
        """提取变卦信息"""
        # 示例：变卦：风水涣/离宫·6
        match = re.search(r'变卦：(.+?)/(.+?)·(\d+)', text)
        if match:
            return {
                'full': f"{match.group(1)}/{match.group(2)}",
                'name': match.group(1).strip(),
                'gong': match.group(2).strip(),
                'index': int(match.group(3))
            }

        # 备用格式：变卦：风水涣
        match = re.search(r'变卦：(.+)', text)
        if match:
            name = match.group(1).strip()
            return {
                'full': name,
                'name': name,
                'gong': '未知',
                'index': 0
            }

        return {
            'full': '未知',
            'name': '未知',
            'gong': '未知',
            'index': 0
        }

    @staticmethod
    def _extract_lines(text: str) -> List[LineInfo]:
        """提取六爻信息"""
        lines = []

        # 六神映射
        liushen_map = {
            '虎': '白虎',
            '蛇': '螣蛇',
            '勾': '勾陈',
            '雀': '朱雀',
            '龙': '青龙',
            '玄': '玄武'
        }

        # 六亲映射
        liuqin_map = {
            '父': '父母',
            '子': '子孙',
            '财': '妻财',
            '官': '官鬼',
            '兄': '兄弟',
            '孙': '子孙'
        }

        # 解析每一行
        # 格式示例：虎 父戌 官巳 —  应 财卯 —
        line_patterns = [
            r'([虎蛇勾雀龙玄])\s+([父子财官兄孙])(\w+)\s+(\w+)\s+([—-]+)\s*(应)?\s*(\w+)?\s*([—-]+)',
            r'([虎蛇勾雀龙玄])\s+([父子财官兄孙])(\w+)\s+(\w+)\s+([—-]+)\s*(世|应)?',
        ]

        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue

            for pattern in line_patterns:
                match = re.search(pattern, line)
                if match:
                    shen = liushen_map.get(match.group(1), match.group(1))
                    liuqin_abbr = match.group(2)
                    liuqin = liuqin_map.get(liuqin_abbr, liuqin_abbr)
                    tian_gan = match.group(3) if len(match.groups()) > 3 else ''
                    di_zhi = match.group(4) if len(match.groups()) > 4 else ''
                    yin_yang = match.group(5) if len(match.groups()) > 5 else ''
                    shi_ying = match.group(6) if len(match.groups()) > 6 else None

                    # 检测动爻
                    change_info = None
                    if 'Ｏ' in line or 'Χ' in line or 'O' in line:
                        # 提取变爻信息
                        change_match = re.search(r'[ＯΧO]\s+(\w+)', line)
                        if change_match:
                            change_info = change_match.group(1)

                    line_info = LineInfo(
                        position=len(lines) + 1,
                        shen=shen,
                        liuqin=liuqin,
                        wuxing=f"{tian_gan}{di_zhi}" if tian_gan else di_zhi,
                        dizhi=di_zhi,
                        yin_yang=yin_yang,
                        shi_ying=shi_ying,
                        change_info=change_info
                    )

                    lines.append(line_info)
                    break

        # 应该有6个爻
        if len(lines) != 6:
            logger.warning(f"爻数量不是6个: {len(lines)}")

        # 倒序排列（从初爻到上爻）
        lines.reverse()

        # 重新编号
        for i, line in enumerate(lines):
            line.position = i + 1

        return lines


def parse_hexagram_from_text(text: str) -> HexagramInput:
    """
    便捷函数：解析卦象文本

    Args:
        text: 卦象文本

    Returns:
        HexagramInput: 解析后的卦象数据
    """
    parser = HexagramParser()
    return parser.parse_text(text)
