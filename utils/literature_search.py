"""文献搜索功能 - 支持关键词搜索各流派经典文献"""
import re
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
from loguru import logger

try:
    import jieba
    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False
    logger.warning("jieba未安装，文献搜索功能将使用简单分词")

from storage.models import SchoolType, LiteratureRef


class LiteratureSearch:
    """文献搜索系统 - 支持基于关键词的文献检索"""

    def __init__(self, config: dict):
        """
        初始化文献搜索系统

        Args:
            config: 文献搜索配置
        """
        self.enabled = config.get('enabled', False)
        self.kb_path = Path(config['knowledge_base_path'])
        self.top_k = config.get('top_k', 3)

        if not self.enabled:
            logger.info("文献搜索功能未启用")
            return

        # 验证知识库路径
        if not self.kb_path.exists():
            logger.warning(f"知识库路径不存在: {self.kb_path}")
            self.enabled = False
            return

        # 构建搜索索引
        self.index: Dict[SchoolType, Dict[str, Any]] = {}
        self._build_index()

        logger.info("LiteratureSearch 初始化完成")

    def _build_index(self):
        """为所有流派构建搜索索引"""
        logger.info("开始构建文献搜索索引...")

        self.index = {
            SchoolType.TRADITIONAL: self._build_school_index('traditional'),
            SchoolType.XIANGSHU: self._build_school_index('xiangshu'),
            SchoolType.MANGPAI: self._build_school_index('mangpai')
        }

        # 统计索引结果
        for school, idx in self.index.items():
            doc_count = len(idx.get('documents', []))
            seg_count = len(idx.get('segments', []))
            logger.info(f"{school.value}派: {doc_count}个文档, {seg_count}个段落")

    def _build_school_index(self, school_dir: str) -> Dict[str, Any]:
        """
        为单个流派构建索引

        Args:
            school_dir: 流派目录名

        Returns:
            Dict: 索引字典
        """
        base_path = self.kb_path / school_dir

        if not base_path.exists():
            logger.warning(f"流派目录不存在: {base_path}")
            return {'documents': [], 'segments': [], 'keyword_map': defaultdict(list)}

        index = {
            'documents': [],  # 文档元数据
            'segments': [],   # 文本段落
            'keyword_map': defaultdict(list)  # keyword -> segment_ids
        }

        # 遍历所有.txt文件
        for file_path in base_path.glob('**/*.txt'):
            # 跳过README文件
            if file_path.name.lower() == 'readme.md':
                continue

            try:
                doc = self._parse_document(file_path)
                if doc:
                    index['documents'].append(doc)

                    # 分割文档为段落
                    segments = self._split_into_segments(doc)
                    index['segments'].extend(segments)

                    # 提取关键词并建立索引
                    for segment in segments:
                        keywords = self._extract_keywords(segment['text'])
                        for kw in keywords:
                            if len(kw) >= 2:  # 忽略单字
                                index['keyword_map'][kw].append(segment['id'])

            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")

        return index

    def _parse_document(self, file_path: Path) -> Dict[str, Any]:
        """
        解析文档文件

        Args:
            file_path: 文件路径

        Returns:
            Dict: 文档元数据
        """
        try:
            content = file_path.read_text(encoding='utf-8')

            # 提取书名（第一个#标题）
            book_title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            book_title = book_title_match.group(1) if book_title_match else file_path.stem

            return {
                'id': str(file_path),
                'file_path': str(file_path),
                'book_title': book_title,
                'raw_content': content
            }
        except Exception as e:
            logger.error(f"解析文档失败 {file_path}: {e}")
            return None

    def _split_into_segments(self, doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        将文档分割为可搜索的段落

        Args:
            doc: 文档字典

        Returns:
            List[Dict]: 段落列表
        """
        segments = []
        lines = doc['raw_content'].split('\n')

        current_volume = None
        current_chapter = None
        current_segment = []
        segment_id = 0

        for line in lines:
            # 跟踪卷（##标题）
            vol_match = re.match(r'^##\s+(.+)', line)
            if vol_match:
                # 保存之前的段落
                if current_segment:
                    segments.append({
                        'id': f"{doc['id']}_{segment_id}",
                        'doc_id': doc['id'],
                        'book_title': doc['book_title'],
                        'volume': current_volume or '未知',
                        'chapter': current_chapter or '未知',
                        'text': '\n'.join(current_segment),
                        'keywords': []
                    })
                    current_segment = []
                    segment_id += 1

                current_volume = vol_match.group(1)
                current_chapter = None
                continue

            # 跟踪章（###标题）
            chap_match = re.match(r'^###\s+(.+)', line)
            if chap_match:
                # 保存之前的段落
                if current_segment:
                    segments.append({
                        'id': f"{doc['id']}_{segment_id}",
                        'doc_id': doc['id'],
                        'book_title': doc['book_title'],
                        'volume': current_volume or '未知',
                        'chapter': current_chapter or '未知',
                        'text': '\n'.join(current_segment),
                        'keywords': []
                    })
                    current_segment = []
                    segment_id += 1

                current_chapter = chap_match.group(1)
                continue

            # 累积内容行
            if line.strip() and not line.startswith('#'):
                current_segment.append(line.strip())
            elif current_segment:
                # 遇到空行，保存段落
                segments.append({
                    'id': f"{doc['id']}_{segment_id}",
                    'doc_id': doc['id'],
                    'book_title': doc['book_title'],
                    'volume': current_volume or '未知',
                    'chapter': current_chapter or '未知',
                    'text': '\n'.join(current_segment),
                    'keywords': []
                })
                current_segment = []
                segment_id += 1

        # 保存最后的段落
        if current_segment:
            segments.append({
                'id': f"{doc['id']}_{segment_id}",
                'doc_id': doc['id'],
                'book_title': doc['book_title'],
                'volume': current_volume or '未知',
                'chapter': current_chapter or '未知',
                'text': '\n'.join(current_segment),
                'keywords': []
            })

        return segments

    def _extract_keywords(self, text: str) -> List[str]:
        """
        从文本中提取关键词

        Args:
            text: 文本内容

        Returns:
            List[str]: 关键词列表
        """
        if JIEBA_AVAILABLE:
            # 使用jieba分词
            keywords = jieba.lcut(text)
            # 过滤停用词和单字
            keywords = [kw for kw in keywords if len(kw) >= 2 and not kw.isspace()]
            return keywords
        else:
            # 简单分词：按空格和标点分割
            words = re.findall(r'[\w]+', text)
            return [w for w in words if len(w) >= 2]

    def search(self,
              school: SchoolType,
              keywords: List[str],
              top_k: int = None) -> List[LiteratureRef]:
        """
        关键词搜索

        Args:
            school: 流派
            keywords: 关键词列表
            top_k: 返回结果数量

        Returns:
            List[LiteratureRef]: 文献引用列表
        """
        if not self.enabled:
            logger.debug("文献搜索未启用")
            return []

        top_k = top_k or self.top_k
        index = self.index.get(school)

        if not index or not index.get('segments'):
            logger.warning(f"流派 {school.value} 没有索引数据")
            return []

        logger.debug(f"搜索 {school.value} 文献，关键词: {keywords}")

        # 匹配关键词并打分
        scored_segments = defaultdict(float)

        for keyword in keywords:
            # 精确匹配（优先）
            if keyword in index['keyword_map']:
                for seg_id in index['keyword_map'][keyword]:
                    scored_segments[seg_id] += 2.0

            # 部分匹配
            for segment in index['segments']:
                if keyword in segment['text']:
                    scored_segments[segment['id']] += 1.0

        # 排序并返回top_k
        sorted_segments = sorted(scored_segments.items(),
                                 key=lambda x: x[1], reverse=True)

        results = []
        for seg_id, score in sorted_segments[:top_k]:
            segment = next((s for s in index['segments'] if s['id'] == seg_id), None)
            if segment:
                # 提取相关片段
                snippet = self._extract_snippet(segment['text'], keywords)

                results.append(LiteratureRef(
                    book_title=segment['book_title'],
                    volume=segment['volume'],
                    chapter=segment['chapter'],
                    original_text=snippet,
                    keyword=keywords[0],  # 主要关键词
                    school=school
                ))

        logger.debug(f"找到 {len(results)} 条结果")
        return results

    def _extract_snippet(self, text: str, keywords: List[str], max_length: int = 200) -> str:
        """
        从文本中提取包含关键词的片段

        Args:
            text: 文本
            keywords: 关键词列表
            max_length: 最大长度

        Returns:
            str: 文本片段
        """
        # 查找第一个关键词的位置
        for keyword in keywords:
            pos = text.find(keyword)
            if pos != -1:
                # 提取关键词周围的内容
                start = max(0, pos - 50)
                end = min(len(text), pos + len(keyword) + 50)
                snippet = text[start:end]

                # 添加省略号
                if start > 0:
                    snippet = "..." + snippet
                if end < len(text):
                    snippet = snippet + "..."

                return snippet

        # 如果没有找到关键词，返回前N个字符
        return text[:max_length] + "..." if len(text) > max_length else text

    def rebuild_index(self):
        """重建搜索索引"""
        logger.info("重建文献搜索索引...")
        self._build_index()
        logger.info("索引重建完成")
